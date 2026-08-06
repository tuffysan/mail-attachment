from sqlalchemy import Boolean, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from mailhub.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class SystemMetadata(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Small key/value table reserved for installation-level metadata."""

    __tablename__ = "system_metadata"

    key: Mapped[str] = mapped_column(String(120), nullable=False, unique=True, index=True)
    value: Mapped[str] = mapped_column(Text, nullable=False)


class User(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Local application user."""

    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(320), nullable=False, unique=True, index=True)
    display_name: Mapped[str] = mapped_column(String(120), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(512), nullable=False)
    is_admin: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")


class EmailAccount(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """IMAP account with an encrypted credential."""

    __tablename__ = "email_accounts"

    name: Mapped[str] = mapped_column(String(120), nullable=False)
    email_address: Mapped[str] = mapped_column(String(320), nullable=False, index=True)
    host: Mapped[str] = mapped_column(String(255), nullable=False)
    port: Mapped[int] = mapped_column(Integer, nullable=False, default=993, server_default="993")
    username: Mapped[str] = mapped_column(String(320), nullable=False)
    encrypted_password: Mapped[str] = mapped_column(Text, nullable=False)
    mailbox: Mapped[str] = mapped_column(String(255), nullable=False, default="INBOX", server_default="INBOX")
    use_ssl: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    is_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    last_test_status: Mapped[str | None] = mapped_column(String(32), nullable=True)
    last_test_message: Mapped[str | None] = mapped_column(Text, nullable=True)
