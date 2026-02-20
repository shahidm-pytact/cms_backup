"""Email service for sending emails via SMTP."""
import logging
from typing import Optional
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

import aiosmtplib

from src.email_sender.config import email_settings
from src.email_sender.template_loader import EmailTemplateLoader

logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending emails via SMTP."""
    
    def __init__(self):
        """Initialize email service with SMTP settings."""
        self.host = email_settings.smtp_host
        self.port = email_settings.smtp_port
        self.username = email_settings.smtp_username
        self.password = email_settings.smtp_password
        self.from_email = email_settings.smtp_from_email
        self.from_name = email_settings.smtp_from_name
        self.use_tls = email_settings.smtp_use_tls
        self.frontend_url = email_settings.frontend_url
        self.template_loader = EmailTemplateLoader()
    
    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_body: str,
        text_body: Optional[str] = None,
    ) -> bool:
        """Send email via SMTP.
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            html_body: HTML email body
            text_body: Plain text email body (optional, defaults to HTML stripped)
            
        Returns:
            True if email sent successfully, False otherwise
        """
        try:
            # Create message
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = f"{self.from_name} <{self.from_email}>"
            message["To"] = to_email
            
            # Add text and HTML parts
            if text_body:
                text_part = MIMEText(text_body, "plain")
                message.attach(text_part)
            
            html_part = MIMEText(html_body, "html")
            message.attach(html_part)
            
            # Determine TLS mode based on port
            # Port 587 uses STARTTLS (upgrade connection after connecting)
            # Port 465 uses direct SSL/TLS connection
            use_starttls = False
            use_direct_tls = False
            
            if self.use_tls:
                if self.port == 587:
                    # Port 587: Use STARTTLS
                    use_starttls = True
                elif self.port == 465:
                    # Port 465: Use direct TLS
                    use_direct_tls = True
                else:
                    # Default to STARTTLS for other ports if TLS is enabled
                    use_starttls = True
            
            # Validate SMTP credentials
            if not self.username or not self.password:
                logger.error(
                    f"SMTP credentials not configured. {self.username}, {self.password} "
                    f"Username: {'set' if self.username else 'missing'}, "
                    f"Password: {'set' if self.password else 'missing'}"
                )
                return False
            
            if not self.from_email:
                logger.error("SMTP from_email not configured")
                return False
            
            # Send email
            await aiosmtplib.send(
                message,
                hostname=self.host,
                port=self.port,
                username=self.username,
                password=self.password,
                start_tls=use_starttls,
                use_tls=use_direct_tls,
            )
            
            logger.info(f"Email sent successfully to {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {str(e)}", exc_info=True)
            return False
    
    async def send_invitation_email(
        self,
        to_email: str,
        to_name: str,
        invitation_token: str,
    ) -> bool:
        """Send invitation email to user.
        
        Args:
            to_email: Recipient email address
            to_name: Recipient name
            invitation_token: Invitation token for the link
            
        Returns:
            True if email sent successfully, False otherwise
        """
        invitation_url = f"{self.frontend_url}/accept-invitation?token={invitation_token}"
        
        subject = "You've been invited to join CMS"
        
        # Load and render template
        html_body = self.template_loader.render_template(
            "invitation.html",
            {
                "name": to_name,
                "invitation_url": invitation_url,
            }
        )
        
        text_body = self.template_loader.get_text_version(html_body)
        
        return await self.send_email(to_email, subject, html_body, text_body)
    
    async def send_password_reset_email(
        self,
        to_email: str,
        to_name: str,
        reset_token: str,
    ) -> bool:
        """Send password reset email to user.
        
        Args:
            to_email: Recipient email address
            to_name: Recipient name
            reset_token: Password reset token for the link
            
        Returns:
            True if email sent successfully, False otherwise
        """
        reset_url = f"{self.frontend_url}/reset-password?token={reset_token}"
        
        subject = "Password Reset Request"
        
        # Load and render template
        html_body = self.template_loader.render_template(
            "password_reset.html",
            {
                "name": to_name,
                "reset_url": reset_url,
            }
        )
        
        text_body = self.template_loader.get_text_version(html_body)
        
        return await self.send_email(to_email, subject, html_body, text_body)
    
    async def send_welcome_email(
        self,
        to_email: str,
        to_name: str,
    ) -> bool:
        """Send welcome email after account activation.
        
        Args:
            to_email: Recipient email address
            to_name: Recipient name
            
        Returns:
            True if email sent successfully, False otherwise
        """
        login_url = f"{self.frontend_url}/login"
        
        subject = "Welcome to CMS - Your Account is Active"
        
        # Load and render template
        html_body = self.template_loader.render_template(
            "welcome.html",
            {
                "name": to_name,
                "login_url": login_url,
            }
        )
        
        text_body = self.template_loader.get_text_version(html_body)
        
        return await self.send_email(to_email, subject, html_body, text_body)
    
    async def send_password_changed_email(
        self,
        to_email: str,
        to_name: str,
    ) -> bool:
        """Send password change confirmation email.
        
        Args:
            to_email: Recipient email address
            to_name: Recipient name
            
        Returns:
            True if email sent successfully, False otherwise
        """
        login_url = f"{self.frontend_url}/login"
        
        subject = "Your Password Has Been Changed"
        
        # Load and render template
        html_body = self.template_loader.render_template(
            "password_changed.html",
            {
                "name": to_name,
                "login_url": login_url,
            }
        )
        
        text_body = self.template_loader.get_text_version(html_body)
        
        return await self.send_email(to_email, subject, html_body, text_body)
    
    async def send_email_changed_notification(
        self,
        to_email: str,
        to_name: str,
        old_email: str,
        new_email: str,
    ) -> bool:
        """Send email change notification.
        
        Args:
            to_email: Recipient email address (new email)
            to_name: Recipient name
            old_email: Previous email address
            new_email: New email address
            
        Returns:
            True if email sent successfully, False otherwise
        """
        subject = "Your Email Address Has Been Changed"
        
        # Load and render template
        html_body = self.template_loader.render_template(
            "email_changed.html",
            {
                "name": to_name,
                "old_email": old_email,
                "new_email": new_email,
            }
        )
        
        text_body = self.template_loader.get_text_version(html_body)
        
        return await self.send_email(to_email, subject, html_body, text_body)
