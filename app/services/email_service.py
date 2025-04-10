import os
import smtplib
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import List, Dict, Any, Optional
from jinja2 import Environment, FileSystemLoader

from app.core.config import settings

logger = logging.getLogger(__name__)


class EmailService:
    def __init__(self):
        self.smtp_server = settings.SMTP_SERVER
        self.smtp_port = settings.SMTP_PORT
        self.username = settings.SMTP_USERNAME
        self.password = settings.SMTP_PASSWORD
        self.from_email = settings.EMAILS_FROM_EMAIL
        self.enabled = all(
            [self.smtp_server, self.smtp_port, self.username, self.password]
        )

        # Fix template path to point to app/templates instead of just templates
        templates_dir = Path(__file__).parents[2] / "app" / "templates"
        self.env = Environment(loader=FileSystemLoader(templates_dir), autoescape=True)

        if not self.enabled:
            logger.warning(
                "Email service is not fully configured. Emails will not be sent."
            )

    async def send_email(
        self,
        to_email: str,
        subject: str,
        template_name: str,
        template_data: Dict[str, Any],
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None,
    ) -> bool:
        """
        Send an email using a template

        Args:
            to_email: Recipient email
            subject: Email subject
            template_name: Name of the template file without path or extension
            template_data: Data to be passed to the template
            cc: Carbon copy recipients
            bcc: Blind carbon copy recipients

        Returns:
            bool: True if email was sent successfully, False otherwise
        """
        if not self.enabled:
            logger.warning(
                f"Email not sent to {to_email}: Email service not configured"
            )
            return False

        try:
            message = MIMEMultipart()
            message["From"] = self.from_email
            message["To"] = to_email
            message["Subject"] = subject

            if cc:
                message["Cc"] = ", ".join(cc)
            if bcc:
                message["Bcc"] = ", ".join(bcc)

            template_path = f"emails/{template_name}.html"
            template = self.env.get_template(template_path)
            html_content = template.render(**template_data)

            message.attach(MIMEText(html_content, "html"))

            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                if settings.SMTP_USE_TLS:
                    server.starttls()
                server.login(self.username, self.password)

                recipients = [to_email]
                if cc:
                    recipients.extend(cc)
                if bcc:
                    recipients.extend(bcc)

                server.sendmail(self.from_email, recipients, message.as_string())

            logger.info(f"Email sent successfully to {to_email}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            return False

    async def send_verification_email(
        self, to_email: str, verification_code: str, user_name: str
    ) -> bool:

        subject = "Подтверждение электронной почты - PetRadar"
        template_data = {
            "user_name": user_name,
            "verification_code": verification_code,
            "app_name": settings.APP_NAME,
            "verification_code_expire_minutes": settings.VERIFICATION_CODE_EXPIRE_MINUTES,
        }
        return await self.send_email(
            to_email, subject, "verification_code", template_data
        )

    async def send_password_reset_email(
        self, to_email: str, reset_token: str, user_name: str
    ) -> bool:

        subject = "Сброс пароля - PetRadar"
        reset_url = f"{settings.API_URL}/reset-password?token={reset_token}"
        template_data = {
            "user_name": user_name,
            "reset_url": reset_url,
            "app_name": settings.APP_NAME,
            "reset_token_expire_minutes": settings.VERIFICATION_CODE_EXPIRE_MINUTES,
        }
        return await self.send_email(to_email, subject, "password_reset", template_data)

    async def send_match_found_notification(
        self,
        to_email: str,
        user_name: str,
        pet_name: str,
        similarity: float,
        match_id: str,
    ) -> bool:

        subject = f"Найдено возможное совпадение для {pet_name} - PetRadar"
        match_url = f"{settings.API_URL}/matches/{match_id}"
        template_data = {
            "user_name": user_name,
            "pet_name": pet_name,
            "similarity": int(similarity * 100),
            "match_url": match_url,
            "app_name": settings.APP_NAME,
        }
        return await self.send_email(to_email, subject, "match_found", template_data)

    async def send_match_confirmed_notification(
        self, to_email: str, user_name: str, pet_details: Dict[str, Any]
    ) -> bool:

        subject = "Подтверждено совпадение - PetRadar"
        template_data = {
            "user_name": user_name,
            "pet_details": pet_details,
            "app_name": settings.APP_NAME,
        }
        return await self.send_email(
            to_email, subject, "match_confirmed", template_data
        )

    async def send_email_change_verification(
        self, to_email: str, verification_code: str, user_name: str
    ) -> bool:

        subject = "Подтверждение смены адреса электронной почты - PetRadar"
        template_data = {
            "user_name": user_name,
            "verification_code": verification_code,
            "app_name": settings.APP_NAME,
            "verification_code_expire_minutes": settings.VERIFICATION_CODE_EXPIRE_MINUTES,
        }
        return await self.send_email(to_email, subject, "email_change", template_data)

    async def send_pet_lost_confirmation(
        self,
        to_email: str,
        user_name: str,
        pet_name: str,
        lost_date: str,
        lost_location: str,
    ) -> bool:

        subject = f"Питомец {pet_name} отмечен как потерянный - PetRadar"
        template_data = {
            "user_name": user_name,
            "pet_name": pet_name,
            "lost_date": lost_date,
            "lost_location": lost_location,
            "app_name": settings.APP_NAME,
        }
        return await self.send_email(
            to_email, subject, "pet_lost_confirmation", template_data
        )
