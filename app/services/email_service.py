import os
import logging

logger = logging.getLogger(__name__)


async def send_reminder_email(to_email: str, subject: str, body: str) -> bool:
    """
    Заглушка для email-уведомлений.
    В будущем можно подключить SMTP или SendGrid.
    """
    logger.info(f"📧 Email reminder to {to_email}: {subject}")
    # TODO: Реализовать отправку через SMTP
    # smtp_host = os.getenv("SMTP_HOST")
    # smtp_port = os.getenv("SMTP_PORT")
    # smtp_user = os.getenv("SMTP_USER")
    # smtp_pass = os.getenv("SMTP_PASS")
    return True


async def send_intake_link(to_email: str, link: str, doctor_name: str = "") -> bool:
    """Отправка ссылки на опросник"""
    subject = "Анкета перед приёмом"
    body = f"""
    Здравствуйте!
    
    {f'Врач {doctor_name} просит' if doctor_name else 'Просим'} вас заполнить анкету перед приёмом.
    
    Ссылка на анкету: {link}
    
    Спасибо!
    """
    return await send_reminder_email(to_email, subject, body)
