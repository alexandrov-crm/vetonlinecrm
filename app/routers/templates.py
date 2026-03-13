from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.database import get_session
from app.models.doctor import Doctor
from app.models.template import Template, TemplateCategory
from app.routers.auth import get_current_doctor

router = APIRouter(prefix="/api/templates", tags=["templates"])


# ============ КАТЕГОРИИ ============

@router.get("/categories")
async def get_categories(
    doctor: Doctor = Depends(get_current_doctor),
    session: AsyncSession = Depends(get_session)
):
    result = await session.execute(
        select(TemplateCategory).where(
            TemplateCategory.doctor_id == doctor.id
        ).options(
            selectinload(TemplateCategory.templates)
        ).order_by(TemplateCategory.sort_order)
    )
    categories = result.scalars().all()

    return [{
        "id": c.id,
        "name": c.name,
        "parent_id": c.parent_id,
        "sort_order": c.sort_order,
        "templates_count": len(c.templates)
    } for c in categories]


@router.post("/categories")
async def create_category(
    request: Request,
    doctor: Doctor = Depends(get_current_doctor),
    session: AsyncSession = Depends(get_session)
):
    data = await request.json()
    name = data.get("name", "").strip()

    if not name:
        raise HTTPException(status_code=400, detail="Название обязательно")

    category = TemplateCategory(
        doctor_id=doctor.id,
        name=name,
        parent_id=data.get("parent_id"),
        sort_order=data.get("sort_order", 0)
    )
    session.add(category)
    await session.flush()

    return {
        "message": "Категория создана",
        "category": {"id": category.id, "name": category.name}
    }


@router.put("/categories/{category_id}")
async def update_category(
    category_id: int,
    request: Request,
    doctor: Doctor = Depends(get_current_doctor),
    session: AsyncSession = Depends(get_session)
):
    result = await session.execute(
        select(TemplateCategory).where(
            TemplateCategory.id == category_id,
            TemplateCategory.doctor_id == doctor.id
        )
    )
    category = result.scalar_one_or_none()
    if not category:
        raise HTTPException(status_code=404, detail="Категория не найдена")

    data = await request.json()
    if data.get("name"):
        category.name = data["name"]
    if "parent_id" in data:
        category.parent_id = data["parent_id"]
    if "sort_order" in data:
        category.sort_order = data["sort_order"]

    return {"message": "Категория обновлена"}


@router.delete("/categories/{category_id}")
async def delete_category(
    category_id: int,
    doctor: Doctor = Depends(get_current_doctor),
    session: AsyncSession = Depends(get_session)
):
    result = await session.execute(
        select(TemplateCategory).where(
            TemplateCategory.id == category_id,
            TemplateCategory.doctor_id == doctor.id
        )
    )
    category = result.scalar_one_or_none()
    if not category:
        raise HTTPException(status_code=404, detail="Категория не найдена")

    await session.delete(category)
    return {"message": "Категория удалена"}


# ============ ШАБЛОНЫ ============

@router.get("")
async def get_templates(
    category_id: int = None,
    search: str = "",
    doctor: Doctor = Depends(get_current_doctor),
    session: AsyncSession = Depends(get_session)
):
    query = select(Template).where(Template.doctor_id == doctor.id)

    if category_id:
        query = query.where(Template.category_id == category_id)

    if search:
        query = query.where(
            Template.title.ilike(f"%{search}%") |
            Template.content.ilike(f"%{search}%")
        )

    query = query.order_by(Template.sort_order, Template.title)
    result = await session.execute(query)
    templates = result.scalars().all()

    return [{
        "id": t.id,
        "category_id": t.category_id,
        "title": t.title,
        "content": t.content,
        "sort_order": t.sort_order,
        "created_at": t.created_at.isoformat() if t.created_at else None,
        "updated_at": t.updated_at.isoformat() if t.updated_at else None
    } for t in templates]


@router.post("")
async def create_template(
    request: Request,
    doctor: Doctor = Depends(get_current_doctor),
    session: AsyncSession = Depends(get_session)
):
    data = await request.json()

    title = data.get("title", "").strip()
    content = data.get("content", "").strip()

    if not title or not content:
        raise HTTPException(status_code=400, detail="Название и содержание обязательны")

    template = Template(
        doctor_id=doctor.id,
        category_id=data.get("category_id"),
        title=title,
        content=content,
        sort_order=data.get("sort_order", 0)
    )
    session.add(template)
    await session.flush()

    return {
        "message": "Шаблон создан",
        "template": {"id": template.id, "title": template.title}
    }


@router.put("/{template_id}")
async def update_template(
    template_id: int,
    request: Request,
    doctor: Doctor = Depends(get_current_doctor),
    session: AsyncSession = Depends(get_session)
):
    result = await session.execute(
        select(Template).where(
            Template.id == template_id,
            Template.doctor_id == doctor.id
        )
    )
    template = result.scalar_one_or_none()
    if not template:
        raise HTTPException(status_code=404, detail="Шаблон не найден")

    data = await request.json()

    if data.get("title"):
        template.title = data["title"]
    if "content" in data:
        template.content = data["content"]
    if "category_id" in data:
        template.category_id = data["category_id"]
    if "sort_order" in data:
        template.sort_order = data["sort_order"]

    return {"message": "Шаблон обновлён"}


@router.delete("/{template_id}")
async def delete_template(
    template_id: int,
    doctor: Doctor = Depends(get_current_doctor),
    session: AsyncSession = Depends(get_session)
):
    result = await session.execute(
        select(Template).where(
            Template.id == template_id,
            Template.doctor_id == doctor.id
        )
    )
    template = result.scalar_one_or_none()
    if not template:
        raise HTTPException(status_code=404, detail="Шаблон не найден")

    await session.delete(template)
    return {"message": "Шаблон удалён"}
