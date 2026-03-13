from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph
import os


def _register_fonts():
    """Пытаемся зарегистрировать кириллический шрифт"""
    font_paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/TTF/DejaVuSans.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
    ]
    for path in font_paths:
        if os.path.exists(path):
            try:
                pdfmetrics.registerFont(TTFont('CustomFont', path))
                return 'CustomFont'
            except Exception:
                continue
    return 'Helvetica'


FONT_NAME = _register_fonts()


def _draw_text(c, x, y, text, font_size=10, bold=False):
    """Рисуем текст с переносом строк"""
    font = FONT_NAME
    c.setFont(font, font_size)
    if not text:
        return y

    lines = str(text).split('\n')
    for line in lines:
        # Простой перенос длинных строк
        while len(line) > 90:
            c.drawString(x, y, line[:90])
            line = line[90:]
            y -= font_size + 4
            if y < 40 * mm:
                c.showPage()
                c.setFont(font, font_size)
                y = 270 * mm
        c.drawString(x, y, line)
        y -= font_size + 4

    return y


async def generate_visit_pdf(visit_data: dict, doc_settings: dict) -> bytes:
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    y = height - 30 * mm

    # Header
    if doc_settings.get('doc_header'):
        y = _draw_text(c, 20 * mm, y, doc_settings['doc_header'], 12)
        y -= 5

    if doc_settings.get('clinic_name'):
        y = _draw_text(c, 20 * mm, y, doc_settings['clinic_name'], 14)
        y -= 3

    # Line
    c.setStrokeColorRGB(0.3, 0.5, 0.8)
    c.setLineWidth(1)
    c.line(20 * mm, y, width - 20 * mm, y)
    y -= 10

    # Title
    y = _draw_text(c, 20 * mm, y, "КАРТА ПРИЁМА", 16)
    y -= 8

    # Visit info
    y = _draw_text(c, 20 * mm, y, f"Дата: {visit_data.get('visit_date', '')}", 11)
    y = _draw_text(c, 20 * mm, y, f"Тип: {visit_data.get('visit_type', '')}", 11)
    y -= 5

    # Patient info
    y = _draw_text(c, 20 * mm, y, "ПАЦИЕНТ", 13)
    y = _draw_text(c, 20 * mm, y, f"Кличка: {visit_data.get('pet_name', '')}", 11)
    y = _draw_text(c, 20 * mm, y, f"Вид: {visit_data.get('pet_species', '')} | Порода: {visit_data.get('pet_breed', '')}", 11)
    y = _draw_text(c, 20 * mm, y, f"Владелец: {visit_data.get('owner_name', '')}", 11)
    y -= 5

    # Measurements
    if visit_data.get('weight') or visit_data.get('temperature'):
        y = _draw_text(c, 20 * mm, y, "ИЗМЕРЕНИЯ", 13)
        if visit_data.get('weight'):
            y = _draw_text(c, 20 * mm, y, f"Вес: {visit_data['weight']} кг", 11)
        if visit_data.get('temperature'):
            y = _draw_text(c, 20 * mm, y, f"Температура: {visit_data['temperature']}°C", 11)
        y -= 5

    # Anamnesis
    if visit_data.get('anamnesis'):
        y = _draw_text(c, 20 * mm, y, "АНАМНЕЗ", 13)
        y = _draw_text(c, 20 * mm, y, visit_data['anamnesis'], 10)
        y -= 5

    # Recommendations
    if visit_data.get('recommendations'):
        y = _draw_text(c, 20 * mm, y, "РЕКОМЕНДАЦИИ", 13)
        y = _draw_text(c, 20 * mm, y, visit_data['recommendations'], 10)
        y -= 5

    # Notes
    if visit_data.get('notes'):
        y = _draw_text(c, 20 * mm, y, "ПРИМЕЧАНИЯ", 13)
        y = _draw_text(c, 20 * mm, y, visit_data['notes'], 10)
        y -= 5

    # Footer
    y -= 10
    c.setStrokeColorRGB(0.3, 0.5, 0.8)
    c.line(20 * mm, y, width - 20 * mm, y)
    y -= 8

    if doc_settings.get('doc_doctor_name'):
        y = _draw_text(c, 20 * mm, y, f"Врач: {doc_settings['doc_doctor_name']}", 11)
    if doc_settings.get('doc_doctor_contacts'):
        y = _draw_text(c, 20 * mm, y, doc_settings['doc_doctor_contacts'], 10)
    if doc_settings.get('doc_footer'):
        y = _draw_text(c, 20 * mm, y, doc_settings['doc_footer'], 9)

    c.save()
    return buffer.getvalue()


async def generate_epicrisis_pdf(visits_data: list, pet_data: dict, doc_settings: dict) -> bytes:
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    y = height - 30 * mm

    # Header
    if doc_settings.get('doc_header'):
        y = _draw_text(c, 20 * mm, y, doc_settings['doc_header'], 12)
        y -= 3

    if doc_settings.get('clinic_name'):
        y = _draw_text(c, 20 * mm, y, doc_settings['clinic_name'], 14)

    c.setStrokeColorRGB(0.3, 0.5, 0.8)
    c.line(20 * mm, y - 3, width - 20 * mm, y - 3)
    y -= 15

    # Title
    y = _draw_text(c, 20 * mm, y, "ЭПИКРИЗ", 16)
    y -= 8

    # Pet info
    y = _draw_text(c, 20 * mm, y, f"Пациент: {pet_data['name']} ({pet_data['species']} {pet_data.get('breed', '')})", 11)
    y = _draw_text(c, 20 * mm, y, f"Возраст: {pet_data.get('age', '')} | Владелец: {pet_data.get('owner_name', '')}", 11)
    y -= 8

    # Visits
    for i, v in enumerate(visits_data, 1):
        if y < 60 * mm:
            c.showPage()
            y = height - 30 * mm

        c.setStrokeColorRGB(0.8, 0.8, 0.8)
        c.line(20 * mm, y, width - 20 * mm, y)
        y -= 8

        y = _draw_text(c, 20 * mm, y, f"Приём #{i} — {v.get('visit_date', '')}", 12)

        if v.get('weight'):
            y = _draw_text(c, 25 * mm, y, f"Вес: {v['weight']} кг", 10)
        if v.get('temperature'):
            y = _draw_text(c, 25 * mm, y, f"Температура: {v['temperature']}°C", 10)
        if v.get('anamnesis'):
            y = _draw_text(c, 25 * mm, y, f"Анамнез: {v['anamnesis']}", 10)
        if v.get('recommendations'):
            y = _draw_text(c, 25 * mm, y, f"Рекомендации: {v['recommendations']}", 10)
        y -= 5

    # Footer
    y -= 10
    c.setStrokeColorRGB(0.3, 0.5, 0.8)
    c.line(20 * mm, y, width - 20 * mm, y)
    y -= 8

    if doc_settings.get('doc_doctor_name'):
        y = _draw_text(c, 20 * mm, y, f"Врач: {doc_settings['doc_doctor_name']}", 11)
    if doc_settings.get('doc_footer'):
        y = _draw_text(c, 20 * mm, y, doc_settings['doc_footer'], 9)

    c.save()
    return buffer.getvalue()
