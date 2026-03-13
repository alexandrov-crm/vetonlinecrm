from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.database import get_session
from app.models.doctor import Doctor
from app.models.owner import Owner
from app.models.pet import Pet
from app.models.questionnaire import Questionnaire, QuestionnaireField
from app.models.intake import Intake, IntakeAnswer
from app.routers.auth import get_current_doctor

router = APIRouter(prefix="/api/intake", tags=["intake"])


# ============ ПУБЛИЧНЫЙ ЭНДПОИНТ (без авторизации) ============

@router.get("/public/{public_link}")
async def get_public_questionnaire(
    public_link: str,
    session: AsyncSession = Depends(get_session)
):
    """Получить опросник по публичной ссылке (без авторизации)"""
    result = await session.execute(
        select(Questionnaire).where(
            Questionnaire.public_link == public_link,
            Questionnaire.is_active == True
        ).options(selectinload(Questionnaire.fields))
    )
    q = result.scalar_one_or_none()
    if not q:
        raise HTTPException(status_code=404, detail="Опросник не найден или деактивирован")

    return {
        "id": q.id,
        "title": q.title,
        "description": q.description,
        "fields": [{
            "id": f.id,
            "field_name": f.field_name,
            "field_type": f.field_type,
            "field_label": f.field_label,
            "is_required": f.is_required,
            "options": f.options,
            "sort_order": f.sort_order
        } for f in sorted(q.fields, key=lambda x: x.sort_order)]
    }


@router.post("/public/{public_link}")
async def submit_public_questionnaire(
    public_link: str,
    request: Request,
    session: AsyncSession = Depends(get_session)
):
    """Отправить заполненный опросник (без авторизации)"""
    result = await session.execute(
        select(Questionnaire).where(
            Questionnaire.public_link == public_link,
            Questionnaire.is_active == True
        ).options(selectinload(Questionnaire.fields))
    )
    q = result.scalar_one_or_none()
    if not q:
        raise HTTPException(status_code=404, detail="Опросник не найден")

    data = await request.json()
    answers_data = data.get("answers", {})

    # Проверяем обязательные поля
    for field in q.fields:
        if field.is_required and not answers_data.get(field.field_name):
            raise HTTPException(
                status_code=400,
                detail=f"Поле '{field.field_label}' обязательно для заполнения"
            )

    # Создаём запись intake
    intake = Intake(
        questionnaire_id=q.id,
        owner_name=answers_data.get("owner_name", ""),
        owner_phone=answers_data.get("owner_phone", ""),
        owner_email=answers_data.get("owner_email", ""),
        pet_name=answers_data.get("pet_name", ""),
        pet_species=answers_data.get("pet_species", ""),
        pet_breed=answers_data.get("pet_breed", ""),
        pet_age=answers_data.get("pet_age", ""),
        status="new"
    )
    session.add(intake)
    await session.flush()

    # Сохраняем все ответы
    for field in q.fields:
        value = answers_data.get(field.field_name, "")
        answer = IntakeAnswer(
            intake_id=intake.id,
            field_id=field.id,
            field_name=field.field_name,
            value=str(value) if value else ""
        )
        session.add(answer)

    return {
        "message": "Анкета отправлена! Спасибо!",
        "intake_id": intake.id
    }


# ============ ЭНДПОИНТЫ ДЛЯ ВРАЧА (с авторизацией) ============

@router.get("")
async def get_intakes(
    status: str = None,
    questionnaire_id: int = None,
    doctor: Doctor = Depends(get_current_doctor),
    session: AsyncSession = Depends(get_session)
):
    """Список заполненных анкет"""
    query = select(Intake).join(Questionnaire).where(
        Questionnaire.doctor_id == doctor.id
    ).options(
        selectinload(Intake.answers),
        selectinload(Intake.questionnaire)
    )

    if status:
        query = query.where(Intake.status == status)
    if questionnaire_id:
        query = query.where(Intake.questionnaire_id == questionnaire_id)

    query = query.order_by(Intake.created_at.desc())
    result = await session.execute(query)
    intakes = result.scalars().all()

    return [{
        "id": i.id,
        "questionnaire_title": i.questionnaire.title,
        "owner_name": i.owner_name,
        "owner_phone": i.owner_phone,
        "owner_email": i.owner_email,
        "pet_name": i.pet_name,
        "pet_species": i.pet_species,
        "pet_breed": i.pet_breed,
        "pet_age": i.pet_age,
        "status": i.status,
        "pet_id": i.pet_id,
        "created_at": i.created_at.isoformat() if i.created_at else None,
        "answers": [{
            "field_name": a.field_name,
            "value": a.value
        } for a in i.answers]
    } for i in intakes]


@router.get("/{intake_id}")
async def get_intake(
    intake_id: int,
    doctor: Doctor = Depends(get_current_doctor),
    session: AsyncSession = Depends(get_session)
):
    result = await session.execute(
        select(Intake).join(Questionnaire).where(
            Intake.id == intake_id,
            Questionnaire.doctor_id == doctor.id
        ).options(
            selectinload(Intake.answers),
            selectinload(Intake.questionnaire)
        )
    )
    intake = result.scalar_one_or_none()
    if not intake:
        raise HTTPException(status_code=404, detail="Анкета не найдена")

    return {
        "id": intake.id,
        "questionnaire_title": intake.questionnaire.title,
        "owner_name": intake.owner_name,
        "owner_phone": intake.owner_phone,
        "owner_email": intake.owner_email,
        "pet_name": intake.pet_name,
        "pet_species": intake.pet_species,
        "pet_breed": intake.pet_breed,
        "pet_age": intake.pet_age,
        "status": intake.status,
        "pet_id": intake.pet_id,
        "created_at": intake.created_at.isoformat() if intake.created_at else None,
        "answers": [{
            "field_name": a.field_name,
            "value": a.value
        } for a in intake.answers]
    }


@router.post("/{intake_id}/convert")
async def convert_intake_to_patient(
    intake_id: int,
    doctor: Doctor = Depends(get_current_doctor),
    session: AsyncSession = Depends(get_session)
):
    """Создать карточку пациента из анкеты"""
    result = await session.execute(
        select(Intake).join(Questionnaire).where(
            Intake.id == intake_id,
            Questionnaire.doctor_id == doctor.id
        ).options(selectinload(Intake.answers))
    )
    intake = result.scalar_one_or_none()
    if not intake:
        raise HTTPException(status_code=404, detail="Анкета не найдена")

    # Создаём владельца
    owner = Owner(
        doctor_id=doctor.id,
        full_name=intake.owner_name or "Без имени",
        phone=intake.owner_phone or "",
        email=intake.owner_email or ""
    )
    session.add(owner)
    await session.flush()

    # Создаём питомца
    pet = Pet(
        owner_id=owner.id,
        name=intake.pet_name or "Без клички",
        species=intake.pet_species or "Кошка",
        breed=intake.pet_breed or "",
        age=intake.pet_age or ""
    )
    session.add(pet)
    await session.flush()

    # Привязываем анкету к питомцу
    intake.pet_id = pet.id
    intake.status = "converted"

    return {
        "message": "Карточка пациента создана из анкеты",
        "owner": {"id": owner.id, "full_name": owner.full_name},
        "pet": {"id": pet.id, "name": pet.name},
        "anamnesis_data": _extract_anamnesis(intake.answers)
    }


@router.put("/{intake_id}/status")
async def update_intake_status(
    intake_id: int,
    request: Request,
    doctor: Doctor = Depends(get_current_doctor),
    session: AsyncSession = Depends(get_session)
):
    result = await session.execute(
        select(Intake).join(Questionnaire).where(
            Intake.id == intake_id,
            Questionnaire.doctor_id == doctor.id
        )
    )
    intake = result.scalar_one_or_none()
    if not intake:
        raise HTTPException(status_code=404, detail="Анкета не найдена")

    data = await request.json()
    intake.status = data.get("status", intake.status)

    return {"message": "Статус обновлён"}


@router.delete("/{intake_id}")
async def delete_intake(
    intake_id: int,
    doctor: Doctor = Depends(get_current_doctor),
    session: AsyncSession = Depends(get_session)
):
    result = await session.execute(
        select(Intake).join(Questionnaire).where(
            Intake.id == intake_id,
            Questionnaire.doctor_id == doctor.id
        )
    )
    intake = result.scalar_one_or_none()
    if not intake:
        raise HTTPException(status_code=404, detail="Анкета не найдена")

    await session.delete(intake)
    return {"message": "Анкета удалена"}


def _extract_anamnesis(answers) -> str:
    """Извлекаем данные для автозаполнения анамнеза"""
    for answer in answers:
        if answer.field_name == "complaints" and answer.value:
            return answer.value
    return ""
