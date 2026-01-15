"""
Email Service for Sending Password Reset Emails

Handles SMTP configuration and email template rendering.
"""

import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from jinja2 import Template
from typing import Optional
import logging

from ..config import settings

logger = logging.getLogger(__name__)


# HTML Email Template for Password Reset with OTP
PASSWORD_RESET_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <style>
        body {
            font-family: Arial, sans-serif;
            line-height: 1.6;
            color: #333;
        }
        .container {
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
        }
        .header {
            background-color: #4F46E5;
            color: white;
            padding: 20px;
            text-align: center;
            border-radius: 5px 5px 0 0;
        }
        .content {
            background-color: #f9fafb;
            padding: 30px;
            border-radius: 0 0 5px 5px;
        }
        .otp-code {
            background-color: #4F46E5;
            color: white;
            font-size: 32px;
            font-weight: bold;
            padding: 20px;
            text-align: center;
            letter-spacing: 8px;
            border-radius: 5px;
            margin: 20px 0;
        }
        .footer {
            text-align: center;
            color: #666;
            font-size: 12px;
            margin-top: 20px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{{ from_name }}</h1>
        </div>
        <div class="content">
            <h2>Password Reset OTP</h2>
            <p>Hello {{ user_name }},</p>
            <p>We received a request to reset your password for your {{ from_name }} account.</p>
            <p>Use this One-Time Password (OTP) to reset your password:</p>
            <div class="otp-code">{{ otp_code }}</div>
            <p><strong>This OTP will expire in {{ expire_minutes }} minutes.</strong></p>
            <p>Enter this code on the password reset page to set your new password.</p>
            <p>If you didn't request this password reset, please ignore this email or contact support if you have concerns.</p>
            <p>Best regards,<br>The {{ from_name }} Team</p>
        </div>
        <div class="footer">
            <p>This is an automated email. Please do not reply to this message.</p>
        </div>
    </div>
</body>
</html>
"""


class EmailService:
    """Service for sending emails via SMTP"""
    
    def __init__(self):
        self.smtp_host = settings.SMTP_HOST
        self.smtp_port = settings.SMTP_PORT
        self.smtp_user = settings.SMTP_USER
        self.smtp_password = settings.SMTP_PASSWORD
        self.from_email = settings.SMTP_FROM_EMAIL
        self.from_name = settings.SMTP_FROM_NAME
    
    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None
    ) -> bool:
        """
        Send an email via SMTP
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            html_content: HTML body content
            text_content: Plain text body content (optional)
        
        Returns:
            True if email sent successfully, False otherwise
        """
        try:
            # Create message
            message = MIMEMultipart("alternative")
            message["From"] = f"{self.from_name} <{self.from_email}>"
            message["To"] = to_email
            message["Subject"] = subject
            
            # Add plain text version if provided
            if text_content:
                text_part = MIMEText(text_content, "plain")
                message.attach(text_part)
            
            # Add HTML version
            html_part = MIMEText(html_content, "html")
            message.attach(html_part)
            
            # Send email
            await aiosmtplib.send(
                message,
                hostname=self.smtp_host,
                port=self.smtp_port,
                username=self.smtp_user,
                password=self.smtp_password,
                start_tls=True,
            )
            
            logger.info(f"Email sent successfully to {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {str(e)}")
            return False
    
    async def send_password_reset_otp(
        self,
        to_email: str,
        user_name: str,
        otp_code: str
    ) -> bool:
        """
        Send a password reset OTP email
        
        Args:
            to_email: Recipient email address
            user_name: User's full name
            otp_code: 6-digit OTP code
        
        Returns:
            True if email sent successfully, False otherwise
        """
        template = Template(PASSWORD_RESET_TEMPLATE)
        html_content = template.render(
            user_name=user_name,
            otp_code=otp_code,
            from_name=self.from_name,
            expire_minutes=settings.RESET_TOKEN_EXPIRE_MINUTES
        )
        
        subject = f"Your {self.from_name} Password Reset OTP"
        
        return await self.send_email(
            to_email=to_email,
            subject=subject,
            html_content=html_content
        )


# Global email service instance
email_service = EmailService()
