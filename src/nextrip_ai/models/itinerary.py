from sqlalchemy import ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from nextrip_ai.core.database import Base

class Itinerary(Base):
    __tablename__ = "itineraries"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    trip_id: Mapped[int] = mapped_column(ForeignKey("trips.id"), nullable=False, unique=True)
    days: Mapped[list] = mapped_column(JSON, nullable=False)

    trip: Mapped["Trip"] = relationship("Trip", back_populates="itinerary")
