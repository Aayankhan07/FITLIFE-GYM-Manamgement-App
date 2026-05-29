"""FitLife — Notification Model"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Notification:
    id: int
    user_id: int
    title: str
    message: str
    notif_type: str = "info"
    is_read: bool = False
    created_at: Optional[datetime] = None


@dataclass
class NotificationSettings:
    id: int
    user_id: int
    email_notifications: bool = True
    whatsapp_notifications: bool = True
    phone_number: Optional[str] = None
    email: Optional[str] = None
