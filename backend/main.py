from __future__ import annotations

import json
import os
import shutil
from uuid import uuid4
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, List, Optional

from fastapi import FastAPI, File, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from openai import OpenAI, OpenAIError
from sqlmodel import Field, Session, SQLModel, create_engine, select
from dotenv import load_dotenv


DATABASE_URL = "sqlite:///meetings.db"
BASE_DIR = Path(__file__).parent
ENV_FILE = BASE_DIR / ".env"
UPLOAD_DIR = BASE_DIR / "uploads"
IMAGE_UPLOAD_DIR = UPLOAD_DIR / "images"
ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png"}
ALLOWED_IMAGE_CONTENT_TYPES = {"image/jpeg", "image/png"}

load_dotenv(ENV_FILE)

IMAGE_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

app = FastAPI(title="Meeting Summary Lite API")
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class MeetingBase(SQLModel):
    title: str
    transcript: str


class Meeting(MeetingBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    summary: str
    action_items: str
    keywords: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class MeetingCreate(MeetingBase):
    pass


class MeetingRead(MeetingBase):
    id: int
    summary: str
    action_items: str
    keywords: str
    created_at: datetime


class ImageUploadRead(SQLModel):
    url: str
    filename: str
    content_type: str


def create_db_and_tables() -> None:
    SQLModel.metadata.create_all(engine)


@app.on_event("startup")
def on_startup() -> None:
    create_db_and_tables()


def get_openai_client() -> OpenAI:
    api_key = os.getenv("OPENAI_API_KEY")
    base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")

    if not api_key:
        raise HTTPException(status_code=500, detail="请先在 backend/.env 中配置 OPENAI_API_KEY")

    return OpenAI(api_key=api_key, base_url=base_url)


def extract_json_object(content: str) -> dict[str, Any]:
    decoder = json.JSONDecoder()
    first_object_start = content.find("{")

    for index, char in enumerate(content):
        if char != "{":
            continue

        try:
            data, _ = decoder.raw_decode(content[index:])
        except json.JSONDecodeError:
            continue

        if isinstance(data, dict):
            return data

    if first_object_start != -1:
        possible_json = content[first_object_start:].strip()
        missing_closing_braces = possible_json.count("{") - possible_json.count("}")

        if missing_closing_braces > 0:
            repaired_json = possible_json + ("}" * missing_closing_braces)
            try:
                data = json.loads(repaired_json)
            except json.JSONDecodeError:
                pass
            else:
                if isinstance(data, dict):
                    return data

    raise HTTPException(status_code=502, detail="模型返回的内容不是有效 JSON")


def normalize_model_field(value: Any, separator: str) -> str:
    if isinstance(value, list):
        return separator.join(str(item).strip() for item in value if str(item).strip())

    return str(value).strip()


def parse_json_response(content: str) -> dict[str, str]:
    data = extract_json_object(content)

    required_fields = ["summary", "action_items", "keywords"]
    for field in required_fields:
        if field not in data or not normalize_model_field(data[field], "\n").strip():
            raise HTTPException(status_code=502, detail=f"模型返回缺少字段：{field}")

    return {
        "summary": normalize_model_field(data["summary"], "\n"),
        "action_items": normalize_model_field(data["action_items"], "\n"),
        "keywords": normalize_model_field(data["keywords"], ", "),
    }


def generate_meeting_notes(transcript: str) -> dict[str, str]:
    client = get_openai_client()
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    prompt = f"""
请根据下面的会议转录文本生成会议纪要。

只返回 JSON，不要返回 Markdown，不要添加额外说明。
JSON 字段必须包含：
- summary：一段中文会议摘要
- action_items：中文待办事项，使用换行分隔
- keywords：3 到 6 个中文关键词，使用英文逗号分隔

会议转录文本：
{transcript}
""".strip()

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "你是一个擅长整理中文会议纪要的助手。"},
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
        )
    except OpenAIError as error:
        raise HTTPException(status_code=502, detail=f"调用模型服务失败：{error}") from error

    content = response.choices[0].message.content
    if not content:
        raise HTTPException(status_code=502, detail="模型服务没有返回内容")

    return parse_json_response(content)


@app.get("/")
def read_root() -> dict[str, str]:
    return {"message": "Meeting Summary Lite API is running"}


@app.post("/images", response_model=ImageUploadRead)
def upload_image(request: Request, image: UploadFile = File(...)) -> ImageUploadRead:
    original_filename = image.filename or ""
    suffix = Path(original_filename).suffix.lower()

    if suffix not in ALLOWED_IMAGE_EXTENSIONS:
        raise HTTPException(status_code=400, detail="仅支持上传 jpg、jpeg 或 png 图片")

    if image.content_type not in ALLOWED_IMAGE_CONTENT_TYPES:
        raise HTTPException(status_code=400, detail="图片类型必须是 image/jpeg 或 image/png")

    saved_filename = f"{uuid4().hex}{suffix}"
    saved_path = IMAGE_UPLOAD_DIR / saved_filename

    try:
        with saved_path.open("wb") as file:
            shutil.copyfileobj(image.file, file)
    except OSError as error:
        saved_path.unlink(missing_ok=True)
        raise HTTPException(status_code=500, detail="保存图片失败") from error
    finally:
        image.file.close()

    url = request.url_for("uploads", path=f"images/{saved_filename}")
    return ImageUploadRead(
        url=str(url),
        filename=saved_filename,
        content_type=image.content_type,
    )


@app.post("/meetings", response_model=MeetingRead)
def create_meeting(meeting_create: MeetingCreate) -> Meeting:
    title = meeting_create.title.strip()
    transcript = meeting_create.transcript.strip()

    if not title:
        raise HTTPException(status_code=400, detail="会议标题不能为空")
    if not transcript:
        raise HTTPException(status_code=400, detail="会议转录文本不能为空")

    generated = generate_meeting_notes(transcript)
    meeting = Meeting(
        title=title,
        transcript=transcript,
        summary=generated["summary"],
        action_items=generated["action_items"],
        keywords=generated["keywords"],
    )

    with Session(engine) as session:
        session.add(meeting)
        session.commit()
        session.refresh(meeting)
        return meeting


@app.get("/meetings", response_model=List[MeetingRead])
def list_meetings() -> List[Meeting]:
    with Session(engine) as session:
        statement = select(Meeting).order_by(Meeting.created_at.desc())
        return list(session.exec(statement).all())


@app.get("/meetings/{meeting_id}", response_model=MeetingRead)
def get_meeting(meeting_id: int) -> Meeting:
    with Session(engine) as session:
        meeting = session.get(Meeting, meeting_id)
        if meeting is None:
            raise HTTPException(status_code=404, detail="会议不存在")
        return meeting
