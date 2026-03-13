import os
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from contextlib import asynccontextmanager
from app.config import settings
from app.database import init_db
from app.routers import auth, doctors, patients, visits, templates, calendar, reminders
from app.routers import questionnaire, visit_form, intake, files, documents, dashboard
from app.routers import settings as settings_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_db()
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    print(f"🚀 {settings.PROJECT_NAME} v{settings.VERSION} запущен!")
    yield
    # Shutdown
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
        from app.services.auth_service import decode_access_token
        payload = decode_access_token(token)
        if payload:
            return jinja_templates.TemplateResponse("app.html", {"request": request})
    return jinja_templates.TemplateResponse("login.html", {"request": request})


@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return jinja_templates.TemplateResponse("login.html", {"request": request})


@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return jinja_templates.TemplateResponse("login.html", {"request": request, "mode": "register"})


@app.get("/app", response_class=HTMLResponse)
async def app_page(request: Request):
    return jinja_templates.TemplateResponse("app.html", {"request": request})


@app.get("/intake/{public_link}", response_class=HTMLResponse)
async def intake_page(request: Request, public_link: str):
    return jinja_templates.TemplateResponse("intake.html", {
        "request": request,
        "public_link": public_link
    })


# Health check
@app.get("/health")
async def health():
    return {"status": "ok", "project": settings.PROJECT_NAME, "version": settings.VERSION}
