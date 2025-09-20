from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Text, DateTime, func, ForeignKey, Index
from typing import Optional
from sqlalchemy.dialects.postgresql import UUID
from enum import Enum
from datetime import datetime
import uuid

from models.user import Base, User

class TokenType(str, Enum):
    ACCESS = "access"
    REFRESH = "refresh"


class TokenBlocklist(Base):
    __tablename__ = "token_blocklist"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    jti: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    token_type: Mapped[str] = mapped_column(String(20), nullable=False)
    user_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("users.id"), nullable=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True, nullable=False)
    revoked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    user: Mapped[Optional[User]] = relationship("User")

    __table_args__ = (
        Index("idx_blocklist_jti", "jti"),
        Index("idx_blocklist_expires_at", "expires_at"),
    )

    def __repr__(self) -> str:
        return f"<TokenBlocklist(jti='{self.jti}', type='{self.token_type}')>"


