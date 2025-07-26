from sqlalchemy import String, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID
from uuid import uuid4
from database import Base

class Transportation(Base):
    __tablename__ = "transportations"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key = True, default= uuid4)
    transportation_details: Mapped[str] = mapped_column(String(10000))