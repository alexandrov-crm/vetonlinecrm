from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from sqlalchemy.orm import selectinload
from datetime import datetime, timedelta

from app.database import get_session
from app.models.doctor import Doctor
from app.models.owner import Owner
from app.models.pet import Pet
from app.routers.auth import get_current_doctor

router = APIRouter(prefix="/api/patients", tags=["patients"])


# ============ ВЛАДЕЛЬЦЫ ============

@router.get("/owners")
async def get_owners(
    search: str = "",
    doctor: Doctor = Depends(get_current_doctor),
    session: AsyncSession = Depends(get_session)
):
    query = select(Owner).where(Owner.doctor_id == doctor.id).options(
        selectinload(Owner.pets)
    )

    if search:
        query = query.where(
            or_(
                Owner.full_name.ilike(f"%{search}%"),
                Owner.phone.ilike(f"%{search}%"),
                Owner.email.ilike(f"%{search}%")
            )
        )

    query = query.order_by(Owner.created_at.desc())
    result = await session.execute(query)
    owners = result.scalars().all()

    return [{
        "id": o.id,
        "full_name": o.full_name,
        "phone": o.phone,
        "email": o.email,
        "messenger": o.messenger,
        "notes": o.notes,
        "created_at": o.created_at.isoformat() if o.created_at else None,
        "pets": [{
            "id": p.id,
            "name": p.name,
            "species": p.species,
            "breed": p.breed,
            "age": p.age,
            "subscription_until": p.subscription_until.isoformat() if getattr(p, "subscription_until", None) else None
        } for p in o.pets]
    } for o in owners]


@router.post("/owners")
async def create_owner(
    request: Request,
    doctor: Doctor = Depends(get_current_doctor),
    session: AsyncSession = Depends(get_session)
):
    data = await request.json()

    full_name = data.get("full_name", "").strip()
    if not full_name:
        raise HTTPException(status_code=400, detail="ФИО обязательно")

    owner = Owner(
        doctor_id=doctor.id,
        full_name=full_name,
        phone=data.get("phone", ""),
        email=data.get("email", ""),
        messenger=data.get("messenger", ""),
        notes=data.get("notes", "")
    )
    session.add(owner)
    await session.flush()

    return {
        "message": "Владелец добавлен",
        "owner": {
            "id": owner.id,
            "full_name": owner.full_name
        }
    }


@router.put("/owners/{owner_id}")
async def update_owner(
    owner_id: int,
    request: Request,
    doctor: Doctor = Depends(get_current_doctor),
    session: AsyncSession = Depends(get_session)
):
    result = await session.execute(
        select(Owner).where(Owner.id == owner_id, Owner.doctor_id == doctor.id)
    )
    owner = result.scalar_one_or_none()
    if not owner:
        raise HTTPException(status_code=404, detail="Владелец не найден")

    data = await request.json()

    if data.get("full_name"):
        owner.full_name = data["full_name"]
    if "phone" in data:
        owner.phone = data["phone"]
    if "email" in data:
        owner.email = data["email"]
    if "messenger" in data:
        owner.messenger = data["messenger"]
    if "notes" in data:
        owner.notes = data["notes"]

    return {"message": "Владелец обновлён"}


@router.delete("/owners/{owner_id}")
async def delete_owner(
    owner_id: int,
    doctor: Doctor = Depends(get_current_doctor),
    session: AsyncSession = Depends(get_session)
):
    result = await session.execute(
        select(Owner).where(Owner.id == owner_id, Owner.doctor_id == doctor.id)
    )
    owner = result.scalar_one_or_none()
    if not owner:
        raise HTTPException(status_code=404, detail="Владелец не найден")

    await session.delete(owner)
    return {"message": "Владелец удалён"}


# ============ ПИТОМЦЫ ============

@router.get("/pets")
async def get_pets(
    search: str = "",
    owner_id: int = None,
    doctor: Doctor = Depends(get_current_doctor),
    session: AsyncSession = Depends(get_session)
):
    query = select(Pet).join(Owner).where(Owner.doctor_id == doctor.id).options(
        selectinload(Pet.owner)
    )

    if owner_id:
        query = query.where(Pet.owner_id == owner_id)

    if search:
        query = query.where(
            or_(
                Pet.name.ilike(f"%{search}%"),
                Pet.breed.ilike(f"%{search}%"),
                Owner.full_name.ilike(f"%{search}%"),
                Owner.phone.ilike(f"%{search}%")
            )
        )

    query = query.order_by(Pet.created_at.desc())
    result = await session.execute(query)
    pets = result.scalars().all()

    return [{
        "id": p.id,
        "name": p.name,
        "species": p.species,
        "breed": p.breed,
        "age": p.age,
        "weight": p.weight,
        "sex": p.sex,
        "chip_number": p.chip_number,
        "notes": p.notes,
        "subscription_until": p.subscription_until.isoformat() if getattr(p, "subscription_until", None) else None,
        "created_at": p.created_at.isoformat() if p.created_at else None,
        "owner": {
            "id": p.owner.id,
            "full_name": p.owner.full_name,
            "phone": p.owner.phone
        }
    } for p in pets]


@router.get("/pets/{pet_id}")
async def get_pet(
    pet_id: int,
    doctor: Doctor = Depends(get_current_doctor),
    session: AsyncSession = Depends(get_session)
):
    """Карточка питомца с историей визитов"""
    result = await session.execute(
        select(Pet).join(Owner).where(
            Pet.id == pet_id,
            Owner.doctor_id == doctor.id
        ).options(
            selectinload(Pet.owner),
            selectinload(Pet.visits),
            selectinload(Pet.files),
            selectinload(Pet.intakes)
        )
    )
    pet = result.scalar_one_or_none()
    if not pet:
        raise HTTPException(status_code=404, detail="Питомец не найден")

    return {
        "id": pet.id,
        "name": pet.name,
        "species": pet.species,
        "breed": pet.breed,
        "age": pet.age,
        "weight": pet.weight,
        "sex": pet.sex,
        "chip_number": pet.chip_number,
        "notes": pet.notes,
        "subscription_until": pet.subscription_until.isoformat() if getattr(pet, "subscription_until", None) else None,
        "created_at": pet.created_at.isoformat() if pet.created_at else None,
        "owner": {
            "id": pet.owner.id,
            "full_name": pet.owner.full_name,
            "phone": pet.owner.phone,
            "email": pet.owner.email,
            "messenger": pet.owner.messenger
        },
        "visits": [{
            "id": v.id,
            "visit_type": v.visit_type,
            "status": v.status,
            "visit_date": v.visit_date.isoformat() if v.visit_date else None,
            "weight": v.weight,
            "anamnesis": v.anamnesis,
            "recommendations": v.recommendations,
            "notes": v.notes
        } for v in sorted(pet.visits, key=lambda x: x.created_at, reverse=True)],
        "files": [{
            "id": f.id,
            "original_name": f.original_name,
            "file_type": f.file_type,
            "uploaded_at": f.uploaded_at.isoformat() if f.uploaded_at else None
        } for f in sorted(pet.files, key=lambda x: x.uploaded_at, reverse=True)],
        "intakes": [{
            "id": i.id,
            "status": i.status,
            "created_at": i.created_at.isoformat() if i.created_at else None
        } for i in pet.intakes]
    }


@router.post("/pets")
async def create_pet(
    request: Request,
    doctor: Doctor = Depends(get_current_doctor),
    session: AsyncSession = Depends(get_session)
):
    data = await request.json()

    owner_id = data.get("owner_id")
    name = data.get("name", "").strip()
    species = data.get("species", "").strip()

    if not all([owner_id, name, species]):
        raise HTTPException(status_code=400, detail="Владелец, кличка и вид обязательны")

    # Проверяем что владелец принадлежит этому врачу
    result = await session.execute(
        select(Owner).where(Owner.id == owner_id, Owner.doctor_id == doctor.id)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Владелец не найден")

    pet = Pet(
        owner_id=owner_id,
        name=name,
        species=species,
        breed=data.get("breed", ""),
        age=data.get("age", ""),
        weight=data.get("weight"),
        sex=data.get("sex", ""),
        chip_number=data.get("chip_number", ""),
        notes=data.get("notes", ""),
        subscription_until=None
    )
    session.add(pet)
    await session.flush()

    return {
        "message": "Питомец добавлен",
        "pet": {
            "id": pet.id,
            "name": pet.name,
            "species": pet.species
        }
    }


@router.put("/pets/{pet_id}")
async def update_pet(
    pet_id: int,
    request: Request,
    doctor: Doctor = Depends(get_current_doctor),
    session: AsyncSession = Depends(get_session)
):
    result = await session.execute(
        select(Pet).join(Owner).where(
            Pet.id == pet_id,
            Owner.doctor_id == doctor.id
        )
    )
    pet = result.scalar_one_or_none()
    if not pet:
        raise HTTPException(status_code=404, detail="Питомец не найден")

    data = await request.json()

    if data.get("name"):
        pet.name = data["name"]
    if data.get("species"):
        pet.species = data["species"]
    if "breed" in data:
        pet.breed = data["breed"]
    if "age" in data:
        pet.age = data["age"]
    if "weight" in data:
        pet.weight = data["weight"]
    if "sex" in data:
        pet.sex = data["sex"]
    if "chip_number" in data:
        pet.chip_number = data["chip_number"]
    if "notes" in data:
        pet.notes = data["notes"]

    # (опционально) дать возможность руками поставить subscription_until из админки/формы
    if "subscription_until" in data:
        # ожидаем ISO-строку или пусто/null
        val = data["subscription_until"]
        if not val:
            pet.subscription_until = None
        else:
            try:
                pet.subscription_until = datetime.fromisoformat(val.replace("Z", "+00:00"))
            except Exception:
                raise HTTPException(status_code=400, detail="subscription_until должен быть ISO-датой")

    return {"message": "Питомец обновлён"}


@router.delete("/pets/{pet_id}")
async def delete_pet(
    pet_id: int,
    doctor: Doctor = Depends(get_current_doctor),
    session: AsyncSession = Depends(get_session)
):
    result = await session.execute(
        select(Pet).join(Owner).where(
            Pet.id == pet_id,
            Owner.doctor_id == doctor.id
        )
    )
    pet = result.scalar_one_or_none()
    if not pet:
        raise HTTPException(status_code=404, detail="Питомец не найден")

    await session.delete(pet)
    return {"message": "Питомец удалён"}


# ============ ПОДПИСКА (продление) ============

@router.post("/pets/{pet_id}/subscription")
async def extend_pet_subscription(
    pet_id: int,
    request: Request,
    doctor: Doctor = Depends(get_current_doctor),
    session: AsyncSession = Depends(get_session)
):
    """
    Продлить подписку.

    body:
      { "months": 1 }  или { "days": 30 }

    months считаем как 30 дней (простая модель).
    """
    data = await request.json()
    months = int(data.get("months") or 0)
    days = int(data.get("days") or 0)

    if months <= 0 and days <= 0:
        raise HTTPException(status_code=400, detail="Передайте months или days > 0")

    result = await session.execute(
        select(Pet).join(Owner).where(
            Pet.id == pet_id,
            Owner.doctor_id == doctor.id
        )
    )
    pet = result.scalar_one_or_none()
    if not pet:
        raise HTTPException(status_code=404, detail="Питомец не найден")

    now = datetime.utcnow()
    base = pet.subscription_until or now
    if base < now:
        base = now

    delta_days = days + months * 30
    pet.subscription_until = base + timedelta(days=delta_days)

    return {
        "message": "Подписка продлена",
        "subscription_until": pet.subscription_until.isoformat()
    }


# ============ ГЛОБАЛЬНЫЙ ПОИСК ============

@router.get("/search")
async def global_search(
    q: str = "",
    doctor: Doctor = Depends(get_current_doctor),
    session: AsyncSession = Depends(get_session)
):
    if not q or len(q) < 2:
        return {"owners": [], "pets": []}

    # Поиск владельцев
    owners_result = await session.execute(
        select(Owner).where(
            Owner.doctor_id == doctor.id,
            or_(
                Owner.full_name.ilike(f"%{q}%"),
                Owner.phone.ilike(f"%{q}%"),
                Owner.email.ilike(f"%{q}%")
            )
        ).limit(10)
    )
    owners = owners_result.scalars().all()

    # Поиск питомцев
    pets_result = await session.execute(
        select(Pet).join(Owner).where(
            Owner.doctor_id == doctor.id,
            or_(
                Pet.name.ilike(f"%{q}%"),
                Pet.breed.ilike(f"%{q}%"),
                Owner.full_name.ilike(f"%{q}%")
            )
        ).options(selectinload(Pet.owner)).limit(10)
    )
    pets = pets_result.scalars().all()

    return {
        "owners": [{
            "id": o.id,
            "full_name": o.full_name,
            "phone": o.phone
        } for o in owners],
        "pets": [{
            "id": p.id,
            "name": p.name,
            "species": p.species,
            "breed": p.breed,
            "owner_name": p.owner.full_name
        } for p in pets]
    }
