from sqlalchemy import String, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column
from nextrip_ai.core.database import Base

class DocumentManifest(Base):
    __tablename__ = "document_manifests"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    document_id: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)
    content_hash: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
