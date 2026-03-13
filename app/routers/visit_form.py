from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.database import get_session
from app.models.doctor import Doctor
from app.models.visit_form import VisitFormConfig, VisitFormField
from app.routers.auth import get_current_doctor

router = APIRouter(prefix="/api/visit-forms", tags=["visit-forms"])


@router.get("")
async def get_visit_forms(
    doctor: Doctor = Depends(get_current_doctor),
    session: AsyncSession = Depends(get_session)
):
    result = await session.execute(
        select(VisitFormConfig).where(
            VisitFormConfig.doctor_id == doctor.id
        ).options(
            selectinload(VisitFormConfig.fields)
        ).order_by(VisitFormConfig.created_at.desc())
    )
    configs = result.scalars().all()

    # Если нет конфигураций — создаём дефолтную
    if not configs:
        default_config = await _create_default_config(doctor.id, session)
        configs = [default_config]

    return [{
        "id": c.id,
        "name": c.name,
        "is_default": c.is_default,
        "fields": [{
            "id": f.id,
            "field_name": f.field_name,
            "field_label": f.field_label,
            "field_type": f.field_type,
            "is_visible": f.is_visible,
            "is_required": f.is_required,
            "width": f.width,
            "height": f.height,
            "sort_order": f.sort_order
        } for f in sorted(c.fields, key=lambda x: x.sort_order)]
    } for c in configs]


@router.post("")
async def create_visit_form(
    request: Request,
    doctor: Doctor = Depends(get_current_doctor),
    session: AsyncSession = Depends(get_session)
):
    data = await request.json()

    name = data.get("name", "").strip()
    if not name:
        raise HTTPException(status_code=400, detail="Название обязательно")

    config = VisitFormConfig(
        doctor_id=doctor.id,
        name=name,
        is_default=data.get("is_default", False)
    )
    session.add(config)
    await session.flush()

    fields = data.get("fields", [])
    if not fields:
        # Дефолтные поля
        fields = _get_default_fields()

    for i, field_data in enumerate(fields):
        field = VisitFormField(
            config_id=config.id,
            field_name=field_data.get("field_name", f"field_{i}"),
            field_label=field_data.get("field_label", ""),
            field_type=field_data.get("field_type", "textarea"),
            is_visible=field_data.get("is_visible", True),
            is_required=field_data.get("is_required", False),
            width=field_data.get("width", "full"),
            height=field_data.get("height", 100),
            sort_order=field_data.get("sort_order", i)
        )
        session.add(field)

    return {
        "message": "Форма приёма создана",
        "config": {"id": config.id, "name": config.name}
    }


@router.put("/{config_id}")
async def update_visit_form(
    config_id: int,
    request: Request,
    doctor: Doctor = Depends(get_current_doctor),
    session: AsyncSession = Depends(get_session)
):
    result = await session.execute(
        select(VisitFormConfig).where(
            VisitFormConfig.id == config_id,
            VisitFormConfig.doctor_id == doctor.id
        ).options(selectinload(VisitFormConfig.fields))
    )
    config = result.scalar_one_or_none()
    if not config:
        raise HTTPException(status_code=404, detail="Форма не найдена")

    data = await request.json()

    if data.get("name"):
        config.name = data["name"]
    if "is_default" in data:
        config.is_default = data["is_default"]

    if "fields" in data:
        for field in config.fields:
            await session.delete(field)
        await session.flush()

        for i, field_data in enumerate(data["fields"]):
            field = VisitFormField(
                config_id=config.id,
                field_name=field_data.get("field_name", f"field_{i}"),
                field_label=field_data.get("field_label", ""),
                field_type=field_data.get("field_type", "textarea"),
                is_visible=field_data.get("is_visible", True),
                is_required=field_data.get("is_required", False),
                width=field_data.get("width", "full"),
                height=field_data.get("height", 100),
                sort_order=field_data.get("sort_order", i)
            )
            session.add(field)

    return {"message": "Форма обновлена"}


@router.delete("/{config_id}")
async def delete_visit_form(
    config_id: int,
    doctor: Doctor = Depends(get_current_doctor),
    session: AsyncSession = Depends(get_session)
):
    result = await session.execute(
        select(VisitFormConfig).where(
            VisitFormConfig.id == config_id,
            VisitFormConfig.doctor_id == doctor.id
        )
    )
    config = result.scalar_one_or_none()
    if not config:
        raise HTTPException(status_code=404, detail="Форма не найдена")

    await session.delete(config)
    return {"message": "Форма удалена"}


def _get_default_fields():
    return [
        {"field_name": "weight", "field_label": "Вес (кг)", "field_type": "number", "is_visible": True, "is_required": False, "width": "half", "height": 40, "sort_order": 0},
        {"field_name": "temperature", "field_label": "Температура", "field_type": "number", "is_visible": True, "is_required": False, "width": "half", "height": 40, "sort_order": 1},
        {"field_name": "anamnesis", "field_label": "Анамнез (жалобы)", "field_type": "textarea", "is_visible": True, "is_required": False, "width": "full", "height": 150, "sort_order": 2},
        {"field_name": "recommendations", "field_label": "Рекомендации", "field_type": "textarea", "is_visible": True, "is_required": False, "width": "full", "height": 200, "sort_order": 3},
        {"field_name": "notes", "field_label": "Примечания", "field_type": "textarea", "is_visible": True, "is_required": False, "width": "full", "height": 100, "sort_order": 4},
    ]


async def _create_default_config(doctor_id: int, session: AsyncSession) -> VisitFormConfig:
    config = VisitFormConfig(
        doctor_id=doctor_id,
        name="Стандартная форма",
        is_default=True
    )
    session.add(config)
    await session.flush()

    for field_data in _get_default_fields():
        field = VisitFormField(config_id=config.id, **field_data)
        session.add(field)

    await session.flush()

    result = await session.execute(
        select(VisitFormConfig).where(
            VisitFormConfig.id == config.id
        ).options(selectinload(VisitFormConfig.fields))
    )
    return result.scalar_one()
