from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.database import get_session
from app.models.doctor import Doctor
from app.models.owner import Owner
from app.models.pet import Pet
from app.models.visit import Visit
from app.models.settings import DoctorSettings
from app.services.pdf_service import generate_visit_pdf, generate_epicrisis_pdf
from app.services.doc_service import generate_visit_docx, generate_epicrisis_docx
from app.routers.auth import get_current_doctor

router = APIRouter(prefix="/api/documents", tags=["documents"])


async def _get_doctor_settings(doctor_id: int, session: AsyncSession) -> dict:
    result = await session.execute(
        select(DoctorSettings).where(DoctorSettings.doctor_id == doctor_id)
    )
    s = result.scalar_one_or_none()
    if not s:
        return {}
    return {
        "doc_header": s.doc_header,
        "doc_footer": s.doc_footer,
        "doc_doctor_name": s.doc_doctor_name,
        "doc_doctor_contacts": s.doc_doctor_contacts,
        "doc_signature": s.doc_signature,
        "clinic_name": s.clinic_name
    }


async def _get_visit_data(visit_id: int, doctor_id: int, session: AsyncSession) -> dict:
    result = await session.execute(
        select(Visit).where(
            Visit.id == visit_id,
            Visit.doctor_id == doctor_id
        ).options(
            selectinload(Visit.pet).selectinload(Pet.owner)
        )
    )
    visit = result.scalar_one_or_none()
    if not visit:
        return None

    return {
        "id": visit.id,
        "visit_type": visit.visit_type,
        "status": visit.status,
        "weight": visit.weight,
        "temperature": visit.temperature,
        "anamnesis": visit.anamnesis,
        "recommendations": visit.recommendations,
        "notes": visit.notes,
        "visit_date": visit.visit_date,
        "pet_name": visit.pet.name,
        "pet_species": visit.pet.species,
        "pet_breed": visit.pet.breed,
        "owner_name": visit.pet.owner.full_name
    }


@router.get("/visit/{visit_id}/pdf")
async def get_visit_pdf(
    visit_id: int,
    doctor: Doctor = Depends(get_current_doctor),
    session: AsyncSession = Depends(get_session)
):
    visit_data = await _get_visit_data(visit_id, doctor.id, session)
    if not visit_data:
        raise HTTPException(status_code=404, detail="Приём не найден")

    doc_settings = await _get_doctor_settings(doctor.id, session)
    pdf_bytes = await generate_visit_pdf(visit_data, doc_settings)

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=visit_{visit_id}.pdf"}
    )


@router.get("/visit/{visit_id}/docx")
async def get_visit_docx(
    visit_id: int,
    doctor: Doctor = Depends(get_current_doctor),
    session: AsyncSession = Depends(get_session)
):
    visit_data = await _get_visit_data(visit_id, doctor.id, session)
    if not visit_data:
        raise HTTPException(status_code=404, detail="Приём не найден")

    doc_settings = await _get_doctor_settings(doctor.id, session)
    docx_bytes = await generate_visit_docx(visit_data, doc_settings)

    return Response(
        content=docx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f"attachment; filename=visit_{visit_id}.docx"}
    )


@router.get("/epicrisis/{pet_id}/pdf")
async def get_epicrisis_pdf(
    pet_id: int,
    doctor: Doctor = Depends(get_current_doctor),
    session: AsyncSession = Depends(get_session)
):
    """Эпикриз — все приёмы питомца в PDF"""
    result = await session.execute(
        select(Pet).join(Owner).where(
            Pet.id == pet_id,
            Owner.doctor_id == doctor.id
        ).options(
            selectinload(Pet.owner),
            selectinload(Pet.visits)
        )
    )
    pet = result.scalar_one_or_none()
    if not pet:
        raise HTTPException(status_code=404, detail="Питомец не найден")

    if not pet.visits:
        raise HTTPException(status_code=400, detail="Нет приёмов для формирования эпикриза")

    visits_data = [{
        "visit_type": v.visit_type,
        "weight": v.weight,
        "temperature": v.temperature,
        "anamnesis": v.anamnesis,
        "recommendations": v.recommendations,
        "notes": v.notes,
        "visit_date": v.visit_date
    } for v in sorted(pet.visits, key=lambda x: x.created_at)]

    pet_data = {
        "name": pet.name,
        "species": pet.species,
        "breed": pet.breed,
        "age": pet.age,
        "owner_name": pet.owner.full_name
    }

    doc_settings = await _get_doctor_settings(doctor.id, session)
    pdf_bytes = await generate_epicrisis_pdf(visits_data, pet_data, doc_settings)

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=epicrisis_{pet_id}.pdf"}
    )


@router.get("/epicrisis/{pet_id}/docx")
async def get_epicrisis_docx(
    pet_id: int,
    doctor: Doctor = Depends(get_current_doctor),
    session: AsyncSession = Depends(get_session)
):
    """Эпикриз — все приёмы питомца в Word"""
    result = await session.execute(
        select(Pet).join(Owner).where(
            Pet.id == pet_id,
            Owner.doctor_id == doctor.id
        ).options(
            selectinload(Pet.owner),
            selectinload(Pet.visits)
        )
    )
    pet = result.scalar_one_or_none()
    if not pet:
        raise HTTPException(status_code=404, detail="Питомец не найден")

    if not pet.visits:
        raise HTTPException(status_code=400, detail="Нет приёмов для формирования эпикриза")

    visits_data = [{
        "visit_type": v.visit_type,
        "weight": v.weight,
        "temperature": v.temperature,
        "anamnesis": v.anamnesis,
        "recommendations": v.recommendations,
        "notes": v.notes,
        "visit_date": v.visit_date
    } for v in sorted(pet.visits, key=lambda x: x.created_at)]

    pet_data = {
        "name": pet.name,
        "species": pet.species,
        "breed": pet.breed,
        "age": pet.age,
        "owner_name": pet.owner.full_name
    }

    doc_settings = await _get_doctor_settings(doctor.id, session)
    docx_bytes = await generate_epicrisis_docx(visits_data, pet_data, doc_settings)

    return Response(
        content=docx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f"attachment; filename=epicrisis_{pet_id}.docx"}
    )
