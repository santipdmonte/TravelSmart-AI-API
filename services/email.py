import smtplib
import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
import os
from dotenv import load_dotenv
from jinja2 import Environment, FileSystemLoader
import asyncio

load_dotenv()

# Email configuration
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
FROM_EMAIL = os.getenv("FROM_EMAIL", SMTP_USERNAME)
FROM_NAME = os.getenv("FROM_NAME", "TravelSmart AI")

# Frontend URLs
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")
EMAIL_VERIFICATION_URL = os.getenv("EMAIL_VERIFICATION_URL", f"{FRONTEND_URL}/verify-email")
PASSWORD_RESET_URL = os.getenv("PASSWORD_RESET_URL", f"{FRONTEND_URL}/reset-password")

# Jinja2 environment for templates
template_env = Environment(loader=FileSystemLoader("templates/emails"))


class EmailService:
    """Service for sending emails"""
    
    def __init__(self):
        self.smtp_host = SMTP_HOST
        self.smtp_port = SMTP_PORT
        self.smtp_username = SMTP_USERNAME
        self.smtp_password = SMTP_PASSWORD
        self.from_email = FROM_EMAIL
        self.from_name = FROM_NAME
    
    async def _send_email(self, to_email: str, subject: str, html_content: str, text_content: Optional[str] = None) -> bool:
        """Send email using aiosmtplib"""
        try:
            # Create message
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = f"{self.from_name} <{self.from_email}>"
            message["To"] = to_email
            
            # Add text content
            if text_content:
                text_part = MIMEText(text_content, "plain")
                message.attach(text_part)
            
            # Add HTML content
            html_part = MIMEText(html_content, "html")
            message.attach(html_part)
            
            # Send email
            await aiosmtplib.send(
                message,
                hostname=self.smtp_host,
                port=self.smtp_port,
                start_tls=True,
                username=self.smtp_username,
                password=self.smtp_password,
            )
            
            return True
        
        except Exception as e:
            print(f"Error sending email to {to_email}: {e}")
            return False
    
    def _render_template(self, template_name: str, **kwargs) -> str:
        """Render email template with variables"""
        try:
            template = template_env.get_template(template_name)
            return template.render(**kwargs)
        except Exception as e:
            print(f"Error rendering template {template_name}: {e}")
            return self._get_fallback_template(template_name, **kwargs)
    
    def _get_fallback_template(self, template_name: str, **kwargs) -> str:
        """Get fallback HTML template if file template fails"""
        if template_name == "verification.html":
            return f"""
            <html>
                <body>
                    <h2>Welcome to TravelSmart AI!</h2>
                    <p>Hi {kwargs.get('user_name', 'there')},</p>
                    <p>Please verify your email address by clicking the link below:</p>
                    <p><a href="{kwargs.get('verification_url')}" style="background-color: #4CAF50; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Verify Email</a></p>
                    <p>Or copy and paste this link: {kwargs.get('verification_url')}</p>
                    <p>This link will expire in 24 hours.</p>
                    <p>Best regards,<br>TravelSmart AI Team</p>
                </body>
            </html>
            """
        elif template_name == "password_reset.html":
            return f"""
            <html>
                <body>
                    <h2>Password Reset Request</h2>
                    <p>Hi {kwargs.get('user_name', 'there')},</p>
                    <p>You requested to reset your password. Click the link below to reset it:</p>
                    <p><a href="{kwargs.get('reset_url')}" style="background-color: #f44336; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Reset Password</a></p>
                    <p>Or copy and paste this link: {kwargs.get('reset_url')}</p>
                    <p>This link will expire in 1 hour.</p>
                    <p>If you didn't request this, please ignore this email.</p>
                    <p>Best regards,<br>TravelSmart AI Team</p>
                </body>
            </html>
            """
        elif template_name == "welcome.html":
            return f"""
            <html>
                <body>
                    <h2>Welcome to TravelSmart AI!</h2>
                    <p>Hi {kwargs.get('user_name', 'there')},</p>
                    <p>Your email has been verified successfully! Welcome to TravelSmart AI.</p>
                    <p>You can now start planning your amazing trips with our AI-powered travel assistant.</p>
                    <p><a href="{FRONTEND_URL}/dashboard" style="background-color: #2196F3; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Start Planning</a></p>
                    <p>Best regards,<br>TravelSmart AI Team</p>
                </body>
            </html>
            """
        else:
            return f"<html><body><h2>Email from TravelSmart AI</h2><p>Content not available.</p></body></html>"
    
    async def send_verification_email(self, email: str, user_name: str, token: str) -> bool:
        """Send email verification email"""
        verification_url = f"{EMAIL_VERIFICATION_URL}?token={token}"
        
        html_content = self._render_template(
            "verification.html",
            user_name=user_name,
            verification_url=verification_url,
            token=token
        )
        
        text_content = f"""
        Hi {user_name},
        
        Please verify your email address by visiting this link:
        {verification_url}
        
        This link will expire in 24 hours.
        
        Best regards,
        TravelSmart AI Team
        """
        
        return await self._send_email(
            to_email=email,
            subject="Verify your TravelSmart AI account",
            html_content=html_content,
            text_content=text_content
        )
    
    async def send_password_reset_email(self, email: str, user_name: str, token: str) -> bool:
        """Send password reset email"""
        reset_url = f"{PASSWORD_RESET_URL}?token={token}"
        
        html_content = self._render_template(
            "password_reset.html",
            user_name=user_name,
            reset_url=reset_url,
            token=token
        )
        
        text_content = f"""
        Hi {user_name},
        
        You requested to reset your password. Visit this link to reset it:
        {reset_url}
        
        This link will expire in 1 hour.
        
        If you didn't request this, please ignore this email.
        
        Best regards,
        TravelSmart AI Team
        """
        
        return await self._send_email(
            to_email=email,
            subject="Reset your TravelSmart AI password",
            html_content=html_content,
            text_content=text_content
        )
    
    async def send_welcome_email(self, email: str, user_name: str) -> bool:
        """Send welcome email after successful verification"""
        html_content = self._render_template(
            "welcome.html",
            user_name=user_name,
            dashboard_url=f"{FRONTEND_URL}/dashboard"
        )
        
        text_content = f"""
        Hi {user_name},
        
        Welcome to TravelSmart AI! Your email has been verified successfully.
        
        You can now start planning your amazing trips with our AI-powered travel assistant.
        
        Visit: {FRONTEND_URL}/dashboard
        
        Best regards,
        TravelSmart AI Team
        """
        
        return await self._send_email(
            to_email=email,
            subject="Welcome to TravelSmart AI!",
            html_content=html_content,
            text_content=text_content
        )
    
    async def send_account_locked_email(self, email: str, user_name: str) -> bool:
        """Send account locked notification email"""
        html_content = f"""
        <html>
            <body>
                <h2>Account Security Alert</h2>
                <p>Hi {user_name},</p>
                <p>Your TravelSmart AI account has been temporarily locked due to multiple failed login attempts.</p>
                <p>The account will be automatically unlocked in 30 minutes.</p>
                <p>If this wasn't you, please contact our support team.</p>
                <p>Best regards,<br>TravelSmart AI Security Team</p>
            </body>
        </html>
        """
        
        text_content = f"""
        Hi {user_name},
        
        Your TravelSmart AI account has been temporarily locked due to multiple failed login attempts.
        
        The account will be automatically unlocked in 30 minutes.
        
        If this wasn't you, please contact our support team.
        
        Best regards,
        TravelSmart AI Security Team
        """
        
        return await self._send_email(
            to_email=email,
            subject="TravelSmart AI - Account Temporarily Locked",
            html_content=html_content,
            text_content=text_content
        )


# Global email service instance
email_service = EmailService()


def get_email_service() -> EmailService:
    """Dependency injection for EmailService"""
    return email_service 