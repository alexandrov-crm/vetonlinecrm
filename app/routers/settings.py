from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_session
from app.models.doctor import Doctor
from app.models.settings import DoctorSettings
from app.routers.auth import get_current_doctor

router = APIRouter(prefix="/api/settings", tags=["settings"])


@router.get("")
async def get_settings(
    doctor: Doctor = Depends(get_current_doctor),
    session: AsyncSession = Depends(get_session)
):
    result = await session.execute(
        select(DoctorSettings).where(DoctorSettings.doctor_id == doctor.id)
    )
    s = result.scalar_one_or_none()

    if not s:
        s = DoctorSettings(
            doctor_id=doctor.id,
            work_start_hour=9,
            work_end_hour=21,
            slot_duration=60,
            theme="light"
        )
        session.add(s)
        await session.flush()

    return {
        "id": s.id,
        "clinic_name": s.clinic_name,
        "clinic_address": s.clinic_address,
        "clinic_phone": s.clinic_phone,
        "work_start_hour": s.work_start_hour,
        "work_end_hour": s.work_end_hour,
        "slot_duration": s.slot_duration,
        "doc_header": s.doc_header,
        "doc_footer": s.doc_footer,
        "doc_doctor_name": s.doc_doctor_name,
        "doc_doctor_contacts": s.doc_doctor_contacts,
        "doc_signature": s.doc_signature,
        "theme": s.theme
    }


@router.put("")
async def update_settings(
    request: Request,
    doctor: Doctor = Depends(get_current_doctor),
    session: AsyncSession = Depends(get_session)
):
    result = await session.execute(
        select(DoctorSettings).where(DoctorSettings.doctor_id == doctor.id)
    )
    s = result.scalar_one_or_none()

    if not s:
        s = DoctorSettings(doctor_id=doctor.id)
        session.add(s)
        await session.flush()

    data = await request.json()

    if "clinic_name" in data:
        s.clinic_name = data["clinic_name"]
    if "clinic_address" in data:
        s.clinic_address = data["clinic_address"]
    if "clinic_phone" in data:
        s.clinic_phone = data["clinic_phone"]
    if "work_start_hour" in data:
        s.work_start_hour = data["work_start_hour"]
    if "work_end_hour" in data:
        s.work_end_hour = data["work_end_hour"]
    if "slot_duration" in data:
        s.slot_duration = data["slot_duration"]
    if "doc_header" in data:
        s.doc_header = data["doc_header"]
    if "doc_footer" in data:
        s.doc_footer = data["doc_footer"]
    if "doc_doctor_name" in data:
        s.doc_doctor_name = data["doc_doctor_name"]
    if "doc_doctor_contacts" in data:
        s.doc_doctor_contacts = data["doc_doctor_contacts"]
    if "doc_signature" in data:
        s.doc_signature = data["doc_signature"]
    if "theme" in data:
        s.theme = data["theme"]

    return {"message": "Настройки сохранены"}
