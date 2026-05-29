"""FitLife — Diary Entry Model"""
from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional


@dataclass
class DiaryEntry:
    id: int
    user_id: int
    title: str
    body: str
    entry_date: date
    tags: Optional[str] = None
    is_pinned: bool = False
    is_deleted: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
