"""Contracts for the read-only mock notification feed and read receipts."""

from enum import Enum

from pydantic import BaseModel, Field


class NotificationAudience(str, Enum):
    CREATOR = "creator"
    LEARNER = "learner"
    ORGANIZATION = "organization"
    ADMIN = "admin"


class NotificationKind(str, Enum):
    COURSE = "course"
    LEARNING = "learning"
    ASSESSMENT = "assessment"
    CREDENTIAL = "credential"
    ORGANIZATION = "organization"
    PLATFORM = "platform"


class NotificationResponse(BaseModel):
    id: str
    audience: NotificationAudience
    kind: NotificationKind
    title: str
    message: str
    created_at: str
    destination: str
    read: bool


class NotificationFeedResponse(BaseModel):
    audience: NotificationAudience
    items: list[NotificationResponse]
    unread_count: int = Field(ge=0)
