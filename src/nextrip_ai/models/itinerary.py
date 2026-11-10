from sqlalchemy import ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from nextrip_ai.core.database import Base

class Itinerary(Base):
    __tablename__ = "itineraries"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    trip_id: Mapped[int] = mapped_column(ForeignKey("trips.id"), nullable=False, unique=True)
    days: Mapped[list | None] = mapped_column(JSON, nullable=True)
    generated_by_ai: Mapped[bool] = mapped_column(default=False, nullable=False)
    itinerary_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    trip: Mapped["Trip"] = relationship("Trip", back_populates="itinerary")
