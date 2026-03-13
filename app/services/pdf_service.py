import io
from datetime import datetime


async def generate_visit_pdf(visit_data: dict, doctor_settings: dict = None) -> bytes:
    """Генерация PDF для одного приёма"""
    try:
        from weasyprint import HTML

        html_content = _build_visit_html(visit_data, doctor_settings)
        pdf_bytes = HTML(string=html_content).write_pdf()
        return pdf_bytes
    except ImportError:
        return _generate_simple_pdf(visit_data, doctor_settings)


async def generate_epicrisis_pdf(visits_data: list, pet_data: dict, doctor_settings: dict = None) -> bytes:
    """Генерация эпикриза — все приёмы в 1 файл"""
    try:
        from weasyprint import HTML

        html_content = _build_epicrisis_html(visits_data, pet_data, doctor_settings)
        pdf_bytes = HTML(string=html_content).write_pdf()
        return pdf_bytes
    except ImportError:
        return _generate_simple_epicrisis(visits_data, pet_data, doctor_settings)


def _build_visit_html(visit: dict, settings: dict = None) -> str:
    header = ""
    footer = ""
    doctor_name = ""
    doctor_contacts = ""

    if settings:
        header = settings.get("doc_header", "") or ""
        footer = settings.get("doc_footer", "") or ""
        doctor_name = settings.get("doc_doctor_name", "") or ""
        doctor_contacts = settings.get("doc_doctor_contacts", "") or ""

    visit_date = visit.get("visit_date", "")
    if isinstance(visit_date, datetime):
        visit_date = visit_date.strftime("%d.%m.%Y %H:%M")

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body {{ font-family: Arial, sans-serif; padding: 40px; color: #333; }}
            .header {{ text-align: center; margin-bottom: 30px; border-bottom: 2px solid #4A90D9; padding-bottom: 15px; }}
            .header h1 {{ color: #4A90D9; margin: 0; font-size: 20px; }}
            .header p {{ margin: 5px 0; color: #666; }}
            .patient-info {{ background: #f5f5f5; padding: 15px; border-radius: 8px; margin-bottom: 20px; }}
            .patient-info h3 {{ margin-top: 0; color: #4A90D9; }}
            .section {{ margin-bottom: 20px; }}
            .section h3 {{ color: #4A90D9; border-bottom: 1px solid #ddd; padding-bottom: 5px; }}
            .section p {{ white-space: pre-wrap; line-height: 1.6; }}
            .visit-type {{ display: inline-block; padding: 3px 10px; border-radius: 4px;
                          background: #e8f4fd; color: #4A90D9; font-size: 14px; }}
            .footer {{ margin-top: 40px; border-top: 2px solid #4A90D9; padding-top: 15px; text-align: center; color: #666; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>{header if header else 'Ветеринарная консультация'}</h1>
            {f'<p>{doctor_name}</p>' if doctor_name else ''}
            {f'<p>{doctor_contacts}</p>' if doctor_contacts else ''}
        </div>

        <div class="patient-info">
            <h3>Данные пациента</h3>
            <p><strong>Владелец:</strong> {visit.get('owner_name', '')}</p>
            <p><strong>Питомец:</strong> {visit.get('pet_name', '')} ({visit.get('pet_species', '')}
               {', ' + visit.get('pet_breed', '') if visit.get('pet_breed') else ''})</p>
            <p><strong>Дата:</strong> {visit_date}</p>
            <span class="visit-type">{'Первичный' if visit.get('visit_type') == 'primary' else 'Повторный'}</span>
        </div>

        {f'<div class="section"><h3>Вес</h3><p>{visit.get("weight", "")} кг</p></div>' if visit.get('weight') else ''}

        {f'<div class="section"><h3>Анамнез</h3><p>{visit.get("anamnesis", "")}</p></div>' if visit.get('anamnesis') else ''}

        {f'<div class="section"><h3>Рекомендации</h3><p>{visit.get("recommendations", "")}</p></div>' if visit.get('recommendations') else ''}

        {f'<div class="section"><h3>Примечания</h3><p>{visit.get("notes", "")}</p></div>' if visit.get('notes') else ''}

        <div class="footer">
            {footer if footer else ''}
        </div>
    </body>
    </html>
    """


def _build_epicrisis_html(visits: list, pet: dict, settings: dict = None) -> str:
    header = ""
    footer = ""
    doctor_name = ""

    if settings:
        header = settings.get("doc_header", "") or ""
        footer = settings.get("doc_footer", "") or ""
        doctor_name = settings.get("doc_doctor_name", "") or ""

    visits_html = ""
    for i, visit in enumerate(visits, 1):
        visit_date = visit.get("visit_date", "")
        if isinstance(visit_date, datetime):
            visit_date = visit_date.strftime("%d.%m.%Y %H:%M")

        visits_html += f"""
        <div class="visit-block">
            <h3>Приём #{i} — {visit_date}
                <span class="visit-type">{'Первичный' if visit.get('visit_type') == 'primary' else 'Повторный'}</span>
            </h3>
            {f'<p><strong>Вес:</strong> {visit.get("weight")} кг</p>' if visit.get('weight') else ''}
            {f'<div class="field"><strong>Анамнез:</strong><p>{visit.get("anamnesis", "")}</p></div>' if visit.get('anamnesis') else ''}
            {f'<div class="field"><strong>Рекомендации:</strong><p>{visit.get("recommendations", "")}</p></div>' if visit.get('recommendations') else ''}
            {f'<div class="field"><strong>Примечания:</strong><p>{visit.get("notes", "")}</p></div>' if visit.get('notes') else ''}
        </div>
        """

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body {{ font-family: Arial, sans-serif; padding: 40px; color: #333; }}
            .header {{ text-align: center; margin-bottom: 30px; border-bottom: 2px solid #4A90D9; padding-bottom: 15px; }}
            .header h1 {{ color: #4A90D9; margin: 0; }}
            .patient-info {{ background: #f5f5f5; padding: 15px; border-radius: 8px; margin-bottom: 25px; }}
            .visit-block {{ border: 1px solid #ddd; border-radius: 8px; padding: 15px; margin-bottom: 15px; }}
            .visit-block h3 {{ color: #4A90D9; margin-top: 0; }}
            .visit-type {{ font-size: 12px; background: #e8f4fd; padding: 2px 8px; border-radius: 4px; }}
            .field p {{ white-space: pre-wrap; line-height: 1.6; }}
            .footer {{ margin-top: 40px; border-top: 2px solid #4A90D9; padding-top: 15px; text-align: center; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>Эпикриз</h1>
            <p>{header if header else ''}</p>
            {f'<p>Врач: {doctor_name}</p>' if doctor_name else ''}
        </div>

        <div class="patient-info">
            <h3>Пациент</h3>
            <p><strong>Владелец:</strong> {pet.get('owner_name', '')}</p>
            <p><strong>Питомец:</strong> {pet.get('name', '')} ({pet.get('species', '')}
               {', ' + pet.get('breed', '') if pet.get('breed') else ''})</p>
            <p><strong>Возраст:</strong> {pet.get('age', '')}</p>
        </div>

        <h2>История приёмов ({len(visits)})</h2>
        {visits_html}

        <div class="footer">{footer if footer else ''}</div>
    </body>
    </html>
    """


def _generate_simple_pdf(visit: dict, settings: dict = None) -> bytes:
    """Fallback если WeasyPrint не установлен"""
    content = f"Ветеринарная консультация\n\n"
    content += f"Владелец: {visit.get('owner_name', '')}\n"
    content += f"Питомец: {visit.get('pet_name', '')}\n"
    content += f"Дата: {visit.get('visit_date', '')}\n\n"
    if visit.get('anamnesis'):
        content += f"Анамнез:\n{visit['anamnesis']}\n\n"
    if visit.get('recommendations'):
        content += f"Рекомендации:\n{visit['recommendations']}\n"
    return content.encode('utf-8')


def _generate_simple_epicrisis(visits: list, pet: dict, settings: dict = None) -> bytes:
    content = f"Эпикриз\n\nПитомец: {pet.get('name', '')}\n\n"
    for i, v in enumerate(visits, 1):
        content += f"--- Приём #{i} ---\n"
        content += f"Дата: {v.get('visit_date', '')}\n"
        if v.get('anamnesis'):
            content += f"Анамнез: {v['anamnesis']}\n"
        if v.get('recommendations'):
            content += f"Рекомендации: {v['recommendations']}\n"
        content += "\n"
    return content.encode('utf-8')
