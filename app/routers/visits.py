from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from datetime import datetime
from app.database import get_session
from app.models.doctor import Doctor
from app.models.owner import Owner
from app.models.pet import Pet
from app.models.visit import Visit
from app.routers.auth import get_current_doctor

router = APIRouter(prefix="/api/visits", tags=["visits"])


@router.get("")
async def get_visits(
    pet_id: int = None,
    status: str = None,
    visit_type: str = None,
    doctor: Doctor = Depends(get_current_doctor),
    session: AsyncSession = Depends(get_session)
):
    query = select(Visit).where(Visit.doctor_id == doctor.id).options(
        selectinload(Visit.pet).selectinload(Pet.owner)
    )

    if pet_id:
        query = query.where(Visit.pet_id == pet_id)
    if status:
        query = query.where(Visit.status == status)
    if visit_type:
        query = query.where(Visit.visit_type == visit_type)

    query = query.order_by(Visit.created_at.desc())
    result = await session.execute(query)
    visits = result.scalars().all()

    return [{
        "id": v.id,
        "visit_type": v.visit_type,
        "status": v.status,
        "weight": v.weight,
        "temperature": v.temperature,
        "anamnesis": v.anamnesis,
        "recommendations": v.recommendations,
        "notes": v.notes,
        "custom_fields": v.custom_fields,
        "visit_date": v.visit_date.isoformat() if v.visit_date else None,
        "created_at": v.created_at.isoformat() if v.created_at else None,
        "pet": {
            "id": v.pet.id,
            "name": v.pet.name,
            "species": v.pet.species,
            "breed": v.pet.breed
        },
        "owner": {
            "id": v.pet.owner.id,
            "full_name": v.pet.owner.full_name,
            "phone": v.pet.owner.phone
        }
    } for v in visits]


@router.get("/{visit_id}")
async def get_visit(
    visit_id: int,
    doctor: Doctor = Depends(get_current_doctor),
    session: AsyncSession = Depends(get_session)
):
    result = await session.execute(
        select(Visit).where(
            Visit.id == visit_id,
            Visit.doctor_id == doctor.id
        ).options(
            selectinload(Visit.pet).selectinload(Pet.owner),
            selectinload(Visit.files)
        )
    )
    visit = result.scalar_one_or_none()
    if not visit:
        raise HTTPException(status_code=404, detail="Приём не найден")

    return {
        "id": visit.id,
        "visit_type": visit.visit_type,
        "status": visit.status,
        "weight": visit.weight,
        "temperature": visit.temperature,
        "anamnesis": visit.anamnesis,
        "recommendations": visit.recommendations,
        "notes": visit.notes,
        "custom_fields": visit.custom_fields,
        "visit_date": visit.visit_date.isoformat() if visit.visit_date else None,
        "created_at": visit.created_at.isoformat() if visit.created_at else None,
        "pet": {
            "id": visit.pet.id,
            "name": visit.pet.name,
            "species": visit.pet.species,
            "breed": visit.pet.breed,
            "age": visit.pet.age
        },
        "owner": {
            "id": visit.pet.owner.id,
            "full_name": visit.pet.owner.full_name,
            "phone": visit.pet.owner.phone,
            "email": visit.pet.owner.email
        },
        "files": [{
            "id": f.id,
            "original_name": f.original_name,
            "file_type": f.file_type,
            "uploaded_at": f.uploaded_at.isoformat() if f.uploaded_at else None
        } for f in visit.files]
    }


@router.post("")
async def create_visit(
    request: Request,
    doctor: Doctor = Depends(get_current_doctor),
    session: AsyncSession = Depends(get_session)
):
    data = await request.json()

    pet_id = data.get("pet_id")
    if not pet_id:
        raise HTTPException(status_code=400, detail="Питомец обязателен")

    # Проверяем что питомец принадлежит врачу
    result = await session.execute(
        select(Pet).join(Owner).where(
            Pet.id == pet_id,
            Owner.doctor_id == doctor.id
        )
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Питомец не найден")

    visit_date = None
    if data.get("visit_date"):
        try:
            visit_date = datetime.fromisoformat(data["visit_date"])
        except ValueError:
            visit_date = datetime.utcnow()

    visit = Visit(
        doctor_id=doctor.id,
        pet_id=pet_id,
        calendar_slot_id=data.get("calendar_slot_id"),
        visit_type=data.get("visit_type", "primary"),
        status=data.get("status", "scheduled"),
        weight=data.get("weight"),
        temperature=data.get("temperature"),
        anamnesis=data.get("anamnesis", ""),
        recommendations=data.get("recommendations", ""),
        notes=data.get("notes", ""),
        custom_fields=data.get("custom_fields", ""),
        visit_date=visit_date or datetime.utcnow()
    )
    session.add(visit)
    await session.flush()

    return {
        "message": "Приём создан",
        "visit": {
            "id": visit.id,
            "status": visit.status,
            "visit_type": visit.visit_type
        }
    }


@router.put("/{visit_id}")
async def update_visit(
    visit_id: int,
    request: Request,
    doctor: Doctor = Depends(get_current_doctor),
    session: AsyncSession = Depends(get_session)
):
    result = await session.execute(
        select(Visit).where(Visit.id == visit_id, Visit.doctor_id == doctor.id)
    )
    visit = result.scalar_one_or_none()
    if not visit:
        raise HTTPException(status_code=404, detail="Приём не найден")

    data = await request.json()

    if "visit_type" in data:
        visit.visit_type = data["visit_type"]
    if "status" in data:
        visit.status = data["status"]
    if "weight" in data:
        visit.weight = data["weight"]
    if "temperature" in data:
        visit.temperature = data["temperature"]
    if "anamnesis" in data:
        visit.anamnesis = data["anamnesis"]
    if "recommendations" in data:
        visit.recommendations = data["recommendations"]
    if "notes" in data:
        visit.notes = data["notes"]
    if "custom_fields" in data:
        visit.custom_fields = data["custom_fields"]
    if data.get("visit_date"):
        try:
            visit.visit_date = datetime.fromisoformat(data["visit_date"])
        except ValueError:
            pass

    return {"message": "Приём обновлён"}


@router.delete("/{visit_id}")
async def delete_visit(
    visit_id: int,
    doctor: Doctor = Depends(get_current_doctor),
    session: AsyncSession = Depends(get_session)
):
    result = await session.execute(
        select(Visit).where(Visit.id == visit_id, Visit.doctor_id == doctor.id)
    )
    visit = result.scalar_one_or_none()
    if not visit:
        raise HTTPException(status_code=404, detail="Приём не найден")

    await session.delete(visit)
    return {"message": "Приём удалён"}
