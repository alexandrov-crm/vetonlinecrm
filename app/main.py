import os
from fastapi import FastAPI, Request, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from contextlib import asynccontextmanager
from sqlalchemy import select
from app.config import settings
from app.database import init_db, async_session
from app.models.doctor import Doctor
from app.services.auth_service import hash_password, decode_access_token
from app.routers import auth, doctors, patients, visits, templates, calendar, reminders
from app.routers import questionnaire, visit_form, intake, files, documents, dashboard
from app.routers import settings as settings_router


async def create_default_admin():
    """Создаёт админа при первом запуске"""
    async with async_session() as session:
        result = await session.execute(select(Doctor).where(Doctor.is_admin == True))
        admin = result.scalar_one_or_none()
        if not admin:
            admin = Doctor(
                username="admin",
                email="admin@vetcrm.com",
                hashed_password=hash_password("admin123"),
                full_name="Администратор",
                specialization="",
                phone="",
                is_active=True,
                is_admin=True
            )
            session.add(admin)
            await session.commit()
            print("✅ Админ создан: логин=admin, пароль=admin123")
        else:
            print("✅ Админ уже существует")


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    await create_default_admin()
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    print(f"🚀 {settings.PROJECT_NAME} v{settings.VERSION} запущен!")
    yield
    print("👋 Сервер остановлен")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description=settings.DESCRIPTION,
    lifespan=lifespan
)

# Static files
static_dir = os.path.join(os.path.dirname(__file__), "static")
os.makedirs(static_dir, exist_ok=True)
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Templates
templates_dir = os.path.join(os.path.dirname(__file__), "templates")
os.makedirs(templates_dir, exist_ok=True)
jinja_templates = Jinja2Templates(directory=templates_dir)

# Routers
app.include_router(auth.router)
app.include_router(doctors.router)
app.include_router(patients.router)
app.include_router(visits.router)
app.include_router(templates.router)
app.include_router(calendar.router)
app.include_router(reminders.router)
app.include_router(questionnaire.router)
app.include_router(visit_form.router)
app.include_router(intake.router)
app.include_router(files.router)
app.include_router(documents.router)
app.include_router(dashboard.router)
app.include_router(settings_router.router)


# ============ HTML PAGES ============

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    token = request.cookies.get("access_token")
    if token:
        payload = decode_access_token(token)
        if payload:
            if payload.get("is_admin"):
                return RedirectResponse(url="/admin/doctors", status_code=303)
            return jinja_templates.TemplateResponse("app.html", {"request": request})
    return RedirectResponse(url="/login", status_code=303)


@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return jinja_templates.TemplateResponse("login.html", {"request": request})


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(request: Request):
    token = request.cookies.get("access_token")
    if not token:
        return RedirectResponse(url="/login", status_code=303)
    payload = decode_access_token(token)
    if not payload:
        return RedirectResponse(url="/login", status_code=303)
    if payload.get("is_admin"):
        return RedirectResponse(url="/admin/doctors", status_code=303)
    return jinja_templates.TemplateResponse("app.html", {"request": request})


@app.get("/admin/doctors", response_class=HTMLResponse)
async def admin_doctors_page(request: Request):
    token = request.cookies.get("access_token")
    if not token:
        return RedirectResponse(url="/login", status_code=303)
    payload = decode_access_token(token)
    if not payload or not payload.get("is_admin"):
        return RedirectResponse(url="/login", status_code=303)
    return jinja_templates.TemplateResponse("admin_doctors.html", {"request": request})


@app.get("/app", response_class=HTMLResponse)
async def app_page(request: Request):
    token = request.cookies.get("access_token")
    if not token:
        return RedirectResponse(url="/login", status_code=303)
    return jinja_templates.TemplateResponse("app.html", {"request": request})


@app.get("/intake/{public_link}", response_class=HTMLResponse)
async def intake_page(request: Request, public_link: str):
    return jinja_templates.TemplateResponse("intake.html", {
        "request": request,
        "public_link": public_link
    })


@app.get("/health")
async def health():
    return {"status": "ok", "project": settings.PROJECT_NAME, "version": settings.VERSION}
