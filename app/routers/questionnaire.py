from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.database import get_session
from app.models.doctor import Doctor
from app.models.questionnaire import Questionnaire, QuestionnaireField
from app.routers.auth import get_current_doctor

router = APIRouter(prefix="/api/questionnaires", tags=["questionnaires"])


@router.get("")
async def get_questionnaires(
    doctor: Doctor = Depends(get_current_doctor),
    session: AsyncSession = Depends(get_session)
):
    result = await session.execute(
        select(Questionnaire).where(
            Questionnaire.doctor_id == doctor.id
        ).options(
            selectinload(Questionnaire.fields)
        ).order_by(Questionnaire.created_at.desc())
    )
    questionnaires = result.scalars().all()

    return [{
        "id": q.id,
        "title": q.title,
        "description": q.description,
        "public_link": q.public_link,
        "is_active": q.is_active,
        "created_at": q.created_at.isoformat() if q.created_at else None,
        "fields_count": len(q.fields),
        "fields": [{
            "id": f.id,
            "field_name": f.field_name,
            "field_type": f.field_type,
            "field_label": f.field_label,
            "is_required": f.is_required,
            "options": f.options,
            "sort_order": f.sort_order,
            "maps_to": f.maps_to
        } for f in sorted(q.fields, key=lambda x: x.sort_order)]
    } for q in questionnaires]


@router.get("/{questionnaire_id}")
async def get_questionnaire(
    questionnaire_id: int,
    doctor: Doctor = Depends(get_current_doctor),
    session: AsyncSession = Depends(get_session)
):
    result = await session.execute(
        select(Questionnaire).where(
            Questionnaire.id == questionnaire_id,
            Questionnaire.doctor_id == doctor.id
        ).options(selectinload(Questionnaire.fields))
    )
    q = result.scalar_one_or_none()
    if not q:
        raise HTTPException(status_code=404, detail="Опросник не найден")

    return {
        "id": q.id,
        "title": q.title,
        "description": q.description,
        "public_link": q.public_link,
        "is_active": q.is_active,
        "fields": [{
            "id": f.id,
            "field_name": f.field_name,
            "field_type": f.field_type,
            "field_label": f.field_label,
            "is_required": f.is_required,
            "options": f.options,
            "sort_order": f.sort_order,
            "maps_to": f.maps_to
        } for f in sorted(q.fields, key=lambda x: x.sort_order)]
    }


@router.post("")
async def create_questionnaire(
    request: Request,
    doctor: Doctor = Depends(get_current_doctor),
    session: AsyncSession = Depends(get_session)
):
    data = await request.json()

    title = data.get("title", "").strip()
    if not title:
        raise HTTPException(status_code=400, detail="Название обязательно")

    questionnaire = Questionnaire(
        doctor_id=doctor.id,
        title=title,
        description=data.get("description", "")
    )
    session.add(questionnaire)
    await session.flush()

    # Создаём обязательные поля по умолчанию
    default_fields = [
        {"field_name": "owner_name", "field_label": "ФИО владельца", "field_type": "text", "is_required": True, "sort_order": 1, "maps_to": "owner_name"},
        {"field_name": "owner_phone", "field_label": "Телефон", "field_type": "text", "is_required": True, "sort_order": 2, "maps_to": "owner_phone"},
        {"field_name": "owner_email", "field_label": "Email", "field_type": "text", "is_required": False, "sort_order": 3, "maps_to": "owner_email"},
        {"field_name": "pet_name", "field_label": "Кличка питомца", "field_type": "text", "is_required": True, "sort_order": 4, "maps_to": "pet_name"},
        {"field_name": "pet_species", "field_label": "Вид (кошка/собака)", "field_type": "select", "is_required": True, "sort_order": 5, "maps_to": "pet_species", "options": '["Кошка", "Собака"]'},
        {"field_name": "pet_breed", "field_label": "Порода", "field_type": "text", "is_required": False, "sort_order": 6, "maps_to": "pet_breed"},
        {"field_name": "pet_age", "field_label": "Возраст", "field_type": "text", "is_required": True, "sort_order": 7, "maps_to": "pet_age"},
        {"field_name": "complaints", "field_label": "Жалобы / описание проблемы", "field_type": "textarea", "is_required": False, "sort_order": 8, "maps_to": "anamnesis"},
    ]

    # Добавляем кастомные поля из запроса
    custom_fields = data.get("fields", [])

    for field_data in default_fields:
        field = QuestionnaireField(
            questionnaire_id=questionnaire.id,
            **field_data
        )
        session.add(field)

    for i, field_data in enumerate(custom_fields):
        field = QuestionnaireField(
            questionnaire_id=questionnaire.id,
            field_name=field_data.get("field_name", f"custom_{i}"),
            field_type=field_data.get("field_type", "text"),
            field_label=field_data.get("field_label", f"Поле {i+1}"),
            is_required=field_data.get("is_required", False),
            options=field_data.get("options", ""),
            sort_order=field_data.get("sort_order", 100 + i),
            maps_to=field_data.get("maps_to", "")
        )
        session.add(field)

    return {
        "message": "Опросник создан",
        "questionnaire": {
            "id": questionnaire.id,
            "title": questionnaire.title,
            "public_link": questionnaire.public_link
        }
    }


@router.put("/{questionnaire_id}")
async def update_questionnaire(
    questionnaire_id: int,
    request: Request,
    doctor: Doctor = Depends(get_current_doctor),
    session: AsyncSession = Depends(get_session)
):
    result = await session.execute(
        select(Questionnaire).where(
            Questionnaire.id == questionnaire_id,
            Questionnaire.doctor_id == doctor.id
        ).options(selectinload(Questionnaire.fields))
    )
    q = result.scalar_one_or_none()
    if not q:
        raise HTTPException(status_code=404, detail="Опросник не найден")

    data = await request.json()

    if data.get("title"):
        q.title = data["title"]
    if "description" in data:
        q.description = data["description"]
    if "is_active" in data:
        q.is_active = data["is_active"]

    # Обновляем поля если переданы
    if "fields" in data:
        # Удаляем старые поля
        for field in q.fields:
            await session.delete(field)
        await session.flush()

        # Создаём новые
        for i, field_data in enumerate(data["fields"]):
            field = QuestionnaireField(
                questionnaire_id=q.id,
                field_name=field_data.get("field_name", f"field_{i}"),
                field_type=field_data.get("field_type", "text"),
                field_label=field_data.get("field_label", ""),
                is_required=field_data.get("is_required", False),
                options=field_data.get("options", ""),
                sort_order=field_data.get("sort_order", i),
                maps_to=field_data.get("maps_to", "")
            )
            session.add(field)

    return {"message": "Опросник обновлён"}


@router.delete("/{questionnaire_id}")
async def delete_questionnaire(
    questionnaire_id: int,
    doctor: Doctor = Depends(get_current_doctor),
    session: AsyncSession = Depends(get_session)
):
    result = await session.execute(
        select(Questionnaire).where(
            Questionnaire.id == questionnaire_id,
            Questionnaire.doctor_id == doctor.id
        )
    )
    q = result.scalar_one_or_none()
    if not q:
        raise HTTPException(status_code=404, detail="Опросник не найден")

    await session.delete(q)
    return {"message": "Опросник удалён"}
