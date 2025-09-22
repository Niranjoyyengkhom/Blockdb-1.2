"""
SMTP Notification System
========================

Comprehensive SMTP system supporting Google, Outlook, SendGrid and other providers.
Handles invitations, alerts, and system notifications with templates.
"""

import asyncio
import smtplib
import ssl
import json
import uuid
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional, Union, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
from enum import Enum
import aiosmtplib
from jinja2 import Template


class EmailProvider(Enum):
    """Supported email providers"""
    GMAIL = "gmail"
    OUTLOOK = "outlook"
    SENDGRID = "sendgrid"
    CUSTOM = "custom"


class NotificationType(Enum):
    """Types of notifications"""
    INVITATION = "invitation"
    WELCOME = "welcome"
    PASSWORD_RESET = "password_reset"
    SECURITY_ALERT = "security_alert"
    SYSTEM_ALERT = "system_alert"
    DATA_BREACH = "data_breach"
    MAINTENANCE = "maintenance"
    CUSTOM = "custom"


@dataclass
class SMTPConfig:
    """SMTP server configuration"""
    provider: EmailProvider
    host: str
    port: int
    username: str
    password: str
    use_tls: bool = True
    use_ssl: bool = False
    from_name: str = "Blockchain Database"
    from_email: str = ""
    
    def __post_init__(self):
        if not self.from_email:
            self.from_email = self.username


@dataclass
class EmailTemplate:
    """Email template configuration"""
    template_id: str
    name: str
    subject_template: str
    html_template: str
    text_template: str
    notification_type: NotificationType
    variables: List[str]
    created_at: datetime
    is_active: bool = True


@dataclass
@dataclass
class EmailRecipient:
    """Email recipient information"""
    email: str
    name: str = ""
    variables: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.variables is None:
            self.variables = {}


@dataclass
class EmailMessage:
    """Email message to be sent"""
    message_id: str
    recipients: List[EmailRecipient]
    template_id: Optional[str]
    subject: str
    html_content: str
    text_content: str
    attachments: List[Dict[str, Any]]
    priority: str = "normal"  # low, normal, high
    scheduled_at: Optional[datetime] = None
    variables: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.variables is None:
            self.variables = {}
        if not self.message_id:
            self.message_id = str(uuid.uuid4())


@dataclass
class EmailDeliveryStatus:
    """Email delivery status"""
    message_id: str
    recipient: str
    status: str  # sent, failed, pending
    sent_at: Optional[datetime]
    error_message: Optional[str] = None


class EmailTemplateManager:
    """Manages email templates"""
    
    def __init__(self, templates_path: str):
        self.templates_path = Path(templates_path)
        self.templates_path.mkdir(parents=True, exist_ok=True)
        self.templates: Dict[str, EmailTemplate] = {}
        self._load_templates()
        self._create_default_templates()
    
    def _load_templates(self):
        """Load existing templates"""
        templates_file = self.templates_path / "templates.json"
        if templates_file.exists():
            try:
                with open(templates_file, 'r') as f:
                    templates_data = json.load(f)
                
                for template_data in templates_data:
                    template = EmailTemplate(
                        template_id=template_data["template_id"],
                        name=template_data["name"],
                        subject_template=template_data["subject_template"],
                        html_template=template_data["html_template"],
                        text_template=template_data["text_template"],
                        notification_type=NotificationType(template_data["notification_type"]),
                        variables=template_data["variables"],
                        created_at=datetime.fromisoformat(template_data["created_at"]),
                        is_active=template_data.get("is_active", True)
                    )
                    self.templates[template.template_id] = template
            except Exception as e:
                print(f"Warning: Failed to load email templates: {e}")
    
    def _save_templates(self):
        """Save templates to storage"""
        templates_data = []
        for template in self.templates.values():
            template_dict = {
                "template_id": template.template_id,
                "name": template.name,
                "subject_template": template.subject_template,
                "html_template": template.html_template,
                "text_template": template.text_template,
                "notification_type": template.notification_type.value,
                "variables": template.variables,
                "created_at": template.created_at.isoformat(),
                "is_active": template.is_active
            }
            templates_data.append(template_dict)
        
        templates_file = self.templates_path / "templates.json"
        with open(templates_file, 'w') as f:
            json.dump(templates_data, f, indent=2)
    
    def _create_default_templates(self):
        """Create default email templates"""
        default_templates = [
            {
                "template_id": "invitation",
                "name": "User Invitation",
                "subject_template": "Invitation to join {{ tenant_name }}",
                "html_template": """
                <html>
                <body>
                    <h2>You've been invited to join {{ tenant_name }}</h2>
                    <p>Hello {{ user_name }},</p>
                    <p>You have been invited to join the {{ tenant_name }} tenant in our Blockchain Database system.</p>
                    <p><strong>Your login details:</strong></p>
                    <ul>
                        <li>Tenant ID: {{ tenant_id }}</li>
                        <li>Username: {{ username }}</li>
                        <li>Mnemonic Phrase: <strong>{{ mnemonic }}</strong></li>
                    </ul>
                    <p><strong>Important:</strong> Please save your mnemonic phrase securely. You will need it to access the system.</p>
                    <p>Access the system at: <a href="{{ system_url }}">{{ system_url }}</a></p>
                    <p>Best regards,<br>The Blockchain Database Team</p>
                </body>
                </html>
                """,
                "text_template": """
                You've been invited to join {{ tenant_name }}
                
                Hello {{ user_name }},
                
                You have been invited to join the {{ tenant_name }} tenant in our Blockchain Database system.
                
                Your login details:
                - Tenant ID: {{ tenant_id }}
                - Username: {{ username }}
                - Mnemonic Phrase: {{ mnemonic }}
                
                IMPORTANT: Please save your mnemonic phrase securely. You will need it to access the system.
                
                Access the system at: {{ system_url }}
                
                Best regards,
                The Blockchain Database Team
                """,
                "notification_type": NotificationType.INVITATION,
                "variables": ["tenant_name", "user_name", "tenant_id", "username", "mnemonic", "system_url"]
            },
            {
                "template_id": "security_alert",
                "name": "Security Alert",
                "subject_template": "Security Alert - {{ alert_type }}",
                "html_template": """
                <html>
                <body>
                    <h2 style="color: red;">Security Alert</h2>
                    <p>Hello {{ user_name }},</p>
                    <p>We detected suspicious activity on your account:</p>
                    <p><strong>Alert Type:</strong> {{ alert_type }}</p>
                    <p><strong>Time:</strong> {{ alert_time }}</p>
                    <p><strong>IP Address:</strong> {{ ip_address }}</p>
                    <p><strong>Details:</strong> {{ details }}</p>
                    <p>If this was not you, please contact your administrator immediately.</p>
                    <p>Best regards,<br>The Security Team</p>
                </body>
                </html>
                """,
                "text_template": """
                SECURITY ALERT
                
                Hello {{ user_name }},
                
                We detected suspicious activity on your account:
                
                Alert Type: {{ alert_type }}
                Time: {{ alert_time }}
                IP Address: {{ ip_address }}
                Details: {{ details }}
                
                If this was not you, please contact your administrator immediately.
                
                Best regards,
                The Security Team
                """,
                "notification_type": NotificationType.SECURITY_ALERT,
                "variables": ["user_name", "alert_type", "alert_time", "ip_address", "details"]
            },
            {
                "template_id": "welcome",
                "name": "Welcome Message",
                "subject_template": "Welcome to {{ tenant_name }}",
                "html_template": """
                <html>
                <body>
                    <h2>Welcome to {{ tenant_name }}!</h2>
                    <p>Hello {{ user_name }},</p>
                    <p>Welcome to the Blockchain Database system. Your account has been successfully created.</p>
                    <p><strong>Getting Started:</strong></p>
                    <ul>
                        <li>Access the system at: <a href="{{ system_url }}">{{ system_url }}</a></li>
                        <li>Read our documentation</li>
                        <li>Contact support if you need help</li>
                    </ul>
                    <p>Best regards,<br>The Blockchain Database Team</p>
                </body>
                </html>
                """,
                "text_template": """
                Welcome to {{ tenant_name }}!
                
                Hello {{ user_name }},
                
                Welcome to the Blockchain Database system. Your account has been successfully created.
                
                Getting Started:
                - Access the system at: {{ system_url }}
                - Read our documentation
                - Contact support if you need help
                
                Best regards,
                The Blockchain Database Team
                """,
                "notification_type": NotificationType.WELCOME,
                "variables": ["tenant_name", "user_name", "system_url"]
            }
        ]
        
        for template_data in default_templates:
            if template_data["template_id"] not in self.templates:
                template = EmailTemplate(
                    template_id=template_data["template_id"],
                    name=template_data["name"],
                    subject_template=template_data["subject_template"],
                    html_template=template_data["html_template"],
                    text_template=template_data["text_template"],
                    notification_type=template_data["notification_type"],
                    variables=template_data["variables"],
                    created_at=datetime.now(timezone.utc)
                )
                self.templates[template.template_id] = template
        
        self._save_templates()
    
    def render_template(self, template_id: str, variables: Dict[str, Any]) -> Tuple[str, str, str]:
        """Render email template with variables"""
        template = self.templates.get(template_id)
        if not template:
            raise ValueError(f"Template {template_id} not found")
        
        # Render subject
        subject_template = Template(template.subject_template)
        subject = subject_template.render(**variables)
        
        # Render HTML content
        html_template = Template(template.html_template)
        html_content = html_template.render(**variables)
        
        # Render text content
        text_template = Template(template.text_template)
        text_content = text_template.render(**variables)
        
        return subject, html_content, text_content
    
    def add_template(self, template: EmailTemplate):
        """Add a new template"""
        self.templates[template.template_id] = template
        self._save_templates()
    
    def get_template(self, template_id: str) -> Optional[EmailTemplate]:
        """Get template by ID"""
        return self.templates.get(template_id)
    
    def list_templates(self) -> List[EmailTemplate]:
        """List all templates"""
        return list(self.templates.values())


class SMTPProvider:
    """SMTP provider implementations"""
    
    @staticmethod
    def get_config(provider: EmailProvider, username: str, password: str, **kwargs) -> SMTPConfig:
        """Get SMTP configuration for provider"""
        configs = {
            EmailProvider.GMAIL: SMTPConfig(
                provider=EmailProvider.GMAIL,
                host="smtp.gmail.com",
                port=587,
                username=username,
                password=password,
                use_tls=True,
                from_name=kwargs.get("from_name", "Blockchain Database"),
                from_email=username
            ),
            EmailProvider.OUTLOOK: SMTPConfig(
                provider=EmailProvider.OUTLOOK,
                host="smtp-mail.outlook.com",
                port=587,
                username=username,
                password=password,
                use_tls=True,
                from_name=kwargs.get("from_name", "Blockchain Database"),
                from_email=username
            ),
            EmailProvider.SENDGRID: SMTPConfig(
                provider=EmailProvider.SENDGRID,
                host="smtp.sendgrid.net",
                port=587,
                username="apikey",
                password=password,  # This should be the SendGrid API key
                use_tls=True,
                from_name=kwargs.get("from_name", "Blockchain Database"),
                from_email=kwargs.get("from_email", username)
            )
        }
        
        if provider in configs:
            return configs[provider]
        else:
            # Custom provider
            return SMTPConfig(
                provider=EmailProvider.CUSTOM,
                host=kwargs.get("host", "localhost"),
                port=kwargs.get("port", 587),
                username=username,
                password=password,
                use_tls=kwargs.get("use_tls", True),
                use_ssl=kwargs.get("use_ssl", False),
                from_name=kwargs.get("from_name", "Blockchain Database"),
                from_email=kwargs.get("from_email", username)
            )


class NotificationSystem:
    """Main notification system"""
    
    def __init__(self, storage_path: str = "./notifications"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize components
        self.template_manager = EmailTemplateManager(str(self.storage_path / "templates"))
        
        # SMTP configurations for different tenants
        self.smtp_configs: Dict[str, SMTPConfig] = {}
        
        # Delivery tracking
        self.delivery_log: List[EmailDeliveryStatus] = []
        
        # Load configurations
        self._load_smtp_configs()
    
    def _load_smtp_configs(self):
        """Load SMTP configurations"""
        config_file = self.storage_path / "smtp_configs.json"
        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    configs_data = json.load(f)
                
                for tenant_id, config_data in configs_data.items():
                    self.smtp_configs[tenant_id] = SMTPConfig(
                        provider=EmailProvider(config_data["provider"]),
                        host=config_data["host"],
                        port=config_data["port"],
                        username=config_data["username"],
                        password=config_data["password"],
                        use_tls=config_data.get("use_tls", True),
                        use_ssl=config_data.get("use_ssl", False),
                        from_name=config_data.get("from_name", "Blockchain Database"),
                        from_email=config_data.get("from_email", config_data["username"])
                    )
            except Exception as e:
                print(f"Warning: Failed to load SMTP configs: {e}")
    
    def _save_smtp_configs(self):
        """Save SMTP configurations"""
        configs_data = {}
        for tenant_id, config in self.smtp_configs.items():
            configs_data[tenant_id] = {
                "provider": config.provider.value,
                "host": config.host,
                "port": config.port,
                "username": config.username,
                "password": config.password,
                "use_tls": config.use_tls,
                "use_ssl": config.use_ssl,
                "from_name": config.from_name,
                "from_email": config.from_email
            }
        
        config_file = self.storage_path / "smtp_configs.json"
        with open(config_file, 'w') as f:
            json.dump(configs_data, f, indent=2)
    
    def configure_smtp(self, tenant_id: str, provider: EmailProvider, username: str, 
                      password: str, **kwargs):
        """Configure SMTP for a tenant"""
        config = SMTPProvider.get_config(provider, username, password, **kwargs)
        self.smtp_configs[tenant_id] = config
        self._save_smtp_configs()
    
    async def send_notification(self, tenant_id: str, notification_type: NotificationType,
                              recipients: List[EmailRecipient], variables: Optional[Dict[str, Any]] = None,
                              template_id: Optional[str] = None) -> List[EmailDeliveryStatus]:
        """Send notification to recipients"""
        if variables is None:
            variables = {}
        
        # Get SMTP config for tenant
        smtp_config = self.smtp_configs.get(tenant_id)
        if not smtp_config:
            raise ValueError(f"SMTP not configured for tenant {tenant_id}")
        
        # Determine template
        if not template_id:
            template_id = notification_type.value
        
        # Render template
        try:
            subject, html_content, text_content = self.template_manager.render_template(
                template_id, variables
            )
        except Exception as e:
            raise ValueError(f"Failed to render template {template_id}: {str(e)}")
        
        # Create email message
        message = EmailMessage(
            message_id=str(uuid.uuid4()),
            recipients=recipients,
            template_id=template_id,
            subject=subject,
            html_content=html_content,
            text_content=text_content,
            attachments=[],
            variables=variables
        )
        
        # Send emails
        return await self._send_email_message(smtp_config, message)
    
    async def send_invitation(self, tenant_id: str, user_email: str, user_name: str,
                            tenant_name: str, username: str, mnemonic: str,
                            system_url: str) -> Optional[EmailDeliveryStatus]:
        """Send user invitation"""
        recipients = [EmailRecipient(email=user_email, name=user_name)]
        variables = {
            "user_name": user_name,
            "tenant_name": tenant_name,
            "tenant_id": tenant_id,
            "username": username,
            "mnemonic": mnemonic,
            "system_url": system_url
        }
        
        results = await self.send_notification(
            tenant_id, NotificationType.INVITATION, recipients, variables
        )
        
        return results[0] if results else None
    
    async def send_security_alert(self, tenant_id: str, user_email: str, user_name: str,
                                alert_type: str, ip_address: str, details: str) -> Optional[EmailDeliveryStatus]:
        """Send security alert"""
        recipients = [EmailRecipient(email=user_email, name=user_name)]
        variables = {
            "user_name": user_name,
            "alert_type": alert_type,
            "alert_time": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
            "ip_address": ip_address,
            "details": details
        }
        
        results = await self.send_notification(
            tenant_id, NotificationType.SECURITY_ALERT, recipients, variables
        )
        
        return results[0] if results else None
    
    async def _send_email_message(self, smtp_config: SMTPConfig, 
                                message: EmailMessage) -> List[EmailDeliveryStatus]:
        """Send email message using SMTP"""
        delivery_statuses = []
        
        try:
            # Create SMTP connection
            if smtp_config.use_ssl:
                server = aiosmtplib.SMTP(hostname=smtp_config.host, port=smtp_config.port, use_tls=False)
                await server.connect()
                await server.starttls()
            else:
                server = aiosmtplib.SMTP(hostname=smtp_config.host, port=smtp_config.port, use_tls=smtp_config.use_tls)
                await server.connect()
            
            await server.login(smtp_config.username, smtp_config.password)
            
            # Send to each recipient
            for recipient in message.recipients:
                try:
                    # Create message
                    msg = MIMEMultipart('alternative')
                    msg['Subject'] = message.subject
                    msg['From'] = f"{smtp_config.from_name} <{smtp_config.from_email}>"
                    msg['To'] = recipient.email
                    
                    # Add text and HTML parts
                    text_part = MIMEText(message.text_content, 'plain')
                    html_part = MIMEText(message.html_content, 'html')
                    
                    msg.attach(text_part)
                    msg.attach(html_part)
                    
                    # Send message
                    await server.send_message(msg)
                    
                    # Record success
                    status = EmailDeliveryStatus(
                        message_id=message.message_id,
                        recipient=recipient.email,
                        status="sent",
                        sent_at=datetime.now(timezone.utc)
                    )
                    
                except Exception as e:
                    # Record failure
                    status = EmailDeliveryStatus(
                        message_id=message.message_id,
                        recipient=recipient.email,
                        status="failed",
                        sent_at=datetime.now(timezone.utc),
                        error_message=str(e)
                    )
                
                delivery_statuses.append(status)
                self.delivery_log.append(status)
            
            await server.quit()
            
        except Exception as e:
            # All recipients failed
            for recipient in message.recipients:
                status = EmailDeliveryStatus(
                    message_id=message.message_id,
                    recipient=recipient.email,
                    status="failed",
                    sent_at=datetime.now(timezone.utc),
                    error_message=f"SMTP connection failed: {str(e)}"
                )
                delivery_statuses.append(status)
                self.delivery_log.append(status)
        
        return delivery_statuses
    
    def get_delivery_status(self, message_id: str) -> List[EmailDeliveryStatus]:
        """Get delivery status for a message"""
        return [status for status in self.delivery_log if status.message_id == message_id]
    
    def get_tenant_delivery_history(self, tenant_id: str, limit: int = 100) -> List[EmailDeliveryStatus]:
        """Get delivery history for a tenant"""
        # This is simplified - in production you'd store tenant_id with each status
        return self.delivery_log[-limit:]


def create_notification_system(storage_path: str = "./notifications") -> NotificationSystem:
    """Create and configure notification system"""
    return NotificationSystem(storage_path)
