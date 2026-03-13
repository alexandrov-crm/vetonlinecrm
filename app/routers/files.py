import os
import uuid
import aiofiles
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File as FastAPIFile
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_session
from app.models.doctor import Doctor
from app.models.owner import Owner
from app.models.pet import Pet
from app.models.file import File
from app.config import settings
from app.routers.auth import get_current_doctor

router = APIRouter(prefix="/api/files", tags=["files"])

ALLOWED_TYPES = {
    "image/jpeg": "image", "image/png": "image", "image/gif": "image",
    "image/webp": "image", "image/heic": "image",
    "video/mp4": "video", "video/quicktime": "video", "video/avi": "video",
    "application/pdf": "document", "application/msword": "document",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "document",
}


@router.post("/upload")
async def upload_file(
    file: UploadFile = FastAPIFile(...),
    pet_id: int = None,
    visit_id: int = None,
    doctor: Doctor = Depends(get_current_doctor),
    session: AsyncSession = Depends(get_session)
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="Файл не выбран")

    # Определяем тип
    content_type = file.content_type or ""
    file_type = ALLOWED_TYPES.get(content_type, "document")

    # Проверяем что питомец принадлежит врачу
    if pet_id:
        result = await session.execute(
            select(Pet).join(Owner).where(
                Pet.id == pet_id,
                Owner.doctor_id == doctor.id
            )
        )
        if not result.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="Питомец не найден")

    # Создаём папку uploads
    upload_dir = os.path.join(settings.UPLOAD_DIR, str(doctor.id))
    os.makedirs(upload_dir, exist_ok=True)

    # Генерируем уникальное имя
    ext = os.path.splitext(file.filename)[1]
    unique_name = f"{uuid.uuid4().hex}{ext}"
    file_path = os.path.join(upload_dir, unique_name)

    # Сохраняем файл
    content = await file.read()
    async with aiofiles.open(file_path, "wb") as f:
        await f.write(content)

    # Создаём запись в БД
    db_file = File(
        doctor_id=doctor.id,
        pet_id=pet_id,
        visit_id=visit_id,
        filename=unique_name,
        original_name=file.filename,
        file_type=file_type,
        file_size=len(content),
        file_path=file_path
    )
    session.add(db_file)
    await session.flush()

    return {
        "message": "Файл загружен",
        "file": {
            "id": db_file.id,
            "original_name": db_file.original_name,
            "file_type": db_file.file_type,
            "file_size": db_file.file_size
        }
    }


@router.get("")
async def get_files(
    pet_id: int = None,
    visit_id: int = None,
    file_type: str = None,
    doctor: Doctor = Depends(get_current_doctor),
    session: AsyncSession = Depends(get_session)
):
    query = select(File).where(File.doctor_id == doctor.id)

    if pet_id:
        query = query.where(File.pet_id == pet_id)
    if visit_id:
        query = query.where(File.visit_id == visit_id)
    if file_type:
        query = query.where(File.file_type == file_type)

    query = query.order_by(File.uploaded_at.desc())
    result = await session.execute(query)
    files = result.scalars().all()

    return [{
        "id": f.id,
        "original_name": f.original_name,
        "file_type": f.file_type,
        "file_size": f.file_size,
        "pet_id": f.pet_id,
        "visit_id": f.visit_id,
        "uploaded_at": f.uploaded_at.isoformat() if f.uploaded_at else None
    } for f in files]


@router.get("/download/{file_id}")
async def download_file(
    file_id: int,
    doctor: Doctor = Depends(get_current_doctor),
    session: AsyncSession = Depends(get_session)
):
    result = await session.execute(
        select(File).where(File.id == file_id, File.doctor_id == doctor.id)
    )
    db_file = result.scalar_one_or_none()
    if not db_file:
        raise HTTPException(status_code=404, detail="Файл не найден")

    if not os.path.exists(db_file.file_path):
        raise HTTPException(status_code=404, detail="Файл не найден на диске")

    return FileResponse(
        db_file.file_path,
        filename=db_file.original_name,
        media_type="application/octet-stream"
    )


@router.delete("/{file_id}")
async def delete_file(
    file_id: int,
    doctor: Doctor = Depends(get_current_doctor),
    session: AsyncSession = Depends(get_session)
):
    result = await session.execute(
        select(File).where(File.id == file_id, File.doctor_id == doctor.id)
    )
    db_file = result.scalar_one_or_none()
    if not db_file:
        raise HTTPException(status_code=404, detail="Файл не найден")

    # Удаляем с диска
    if os.path.exists(db_file.file_path):
        os.remove(db_file.file_path)

    await session.delete(db_file)
    return {"message": "Файл удалён"}
