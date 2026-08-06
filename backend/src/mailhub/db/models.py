from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from mailhub.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class SystemMetadata(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Small key/value table reserved for installation-level metadata."""

    __tablename__ = "system_metadata"

    key: Mapped[str] = mapped_column(String(120), nullable=False, unique=True, index=True)
    value: Mapped[str] = mapped_column(Text, nullable=False)
