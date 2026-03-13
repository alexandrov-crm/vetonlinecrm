from io import BytesIO
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH


def _add_header(doc, doc_settings):
    if doc_settings.get('doc_header'):
        p = doc.add_paragraph(doc_settings['doc_header'])
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        for run in p.runs:
            run.font.size = Pt(10)
            run.font.color.rgb = RGBColor(100, 100, 100)

    if doc_settings.get('clinic_name'):
        p = doc.add_paragraph(doc_settings['clinic_name'])
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        for run in p.runs:
            run.font.size = Pt(14)
            run.font.bold = True
            run.font.color.rgb = RGBColor(50, 80, 150)

    # Line
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(6)
    run = p.add_run('_' * 80)
    run.font.color.rgb = RGBColor(180, 180, 180)
    run.font.size = Pt(6)


def _add_footer(doc, doc_settings):
    p = doc.add_paragraph()
    run = p.add_run('_' * 80)
    run.font.color.rgb = RGBColor(180, 180, 180)
    run.font.size = Pt(6)

    if doc_settings.get('doc_doctor_name'):
        p = doc.add_paragraph(f"Врач: {doc_settings['doc_doctor_name']}")
        for run in p.runs:
            run.font.size = Pt(11)

    if doc_settings.get('doc_doctor_contacts'):
        p = doc.add_paragraph(doc_settings['doc_doctor_contacts'])
        for run in p.runs:
            run.font.size = Pt(10)
            run.font.color.rgb = RGBColor(100, 100, 100)

    if doc_settings.get('doc_footer'):
        p = doc.add_paragraph(doc_settings['doc_footer'])
        for run in p.runs:
            run.font.size = Pt(9)
            run.font.color.rgb = RGBColor(130, 130, 130)


def _add_section(doc, title, content):
    if not content:
        return
    p = doc.add_paragraph()
    run = p.add_run(title)
    run.font.bold = True
    run.font.size = Pt(12)
    run.font.color.rgb = RGBColor(50, 80, 150)

    p = doc.add_paragraph(str(content))
    for run in p.runs:
        run.font.size = Pt(11)


async def generate_visit_docx(visit_data: dict, doc_settings: dict) -> bytes:
    doc = Document()

    # Set default font
    style = doc.styles['Normal']
    font = style.font
    font.name = 'Arial'
    font.size = Pt(11)

    _add_header(doc, doc_settings)

    # Title
    p = doc.add_paragraph('КАРТА ПРИЁМА')
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    for run in p.runs:
        run.font.size = Pt(16)
        run.font.bold = True

    # Date & type
    doc.add_paragraph(f"Дата: {visit_data.get('visit_date', '')} | Тип: {visit_data.get('visit_type', '')}")

    # Patient
    _add_section(doc, 'Пациент', '')
    doc.add_paragraph(f"Кличка: {visit_data.get('pet_name', '')}")
    doc.add_paragraph(f"Вид: {visit_data.get('pet_species', '')} | Порода: {visit_data.get('pet_breed', '')}")
    doc.add_paragraph(f"Владелец: {visit_data.get('owner_name', '')}")

    # Measurements
    if visit_data.get('weight') or visit_data.get('temperature'):
        _add_section(doc, 'Измерения', '')
        if visit_data.get('weight'):
            doc.add_paragraph(f"Вес: {visit_data['weight']} кг")
        if visit_data.get('temperature'):
            doc.add_paragraph(f"Температура: {visit_data['temperature']}°C")

    # Main sections
    _add_section(doc, 'Анамнез', visit_data.get('anamnesis'))
    _add_section(doc, 'Рекомендации', visit_data.get('recommendations'))
    _add_section(doc, 'Примечания', visit_data.get('notes'))

    _add_footer(doc, doc_settings)

    buffer = BytesIO()
    doc.save(buffer)
    return buffer.getvalue()


async def generate_epicrisis_docx(visits_data: list, pet_data: dict, doc_settings: dict) -> bytes:
    doc = Document()

    style = doc.styles['Normal']
    font = style.font
    font.name = 'Arial'
    font.size = Pt(11)

    _add_header(doc, doc_settings)

    # Title
    p = doc.add_paragraph('ЭПИКРИЗ')
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    for run in p.runs:
        run.font.size = Pt(16)
        run.font.bold = True

    # Pet info
    doc.add_paragraph(f"Пациент: {pet_data['name']} ({pet_data['species']} {pet_data.get('breed', '')})")
    doc.add_paragraph(f"Возраст: {pet_data.get('age', '')} | Владелец: {pet_data.get('owner_name', '')}")

    # Visits
    for i, v in enumerate(visits_data, 1):
        p = doc.add_paragraph()
        run = p.add_run('_' * 60)
        run.font.color.rgb = RGBColor(200, 200, 200)
        run.font.size = Pt(6)

        _add_section(doc, f"Приём #{i} — {v.get('visit_date', '')}", '')

        if v.get('weight'):
            doc.add_paragraph(f"  Вес: {v['weight']} кг")
        if v.get('temperature'):
            doc.add_paragraph(f"  Температура: {v['temperature']}°C")
        if v.get('anamnesis'):
            doc.add_paragraph(f"  Анамнез: {v['anamnesis']}")
        if v.get('recommendations'):
            doc.add_paragraph(f"  Рекомендации: {v['recommendations']}")

    _add_footer(doc, doc_settings)

    buffer = BytesIO()
    doc.save(buffer)
    return buffer.getvalue()
