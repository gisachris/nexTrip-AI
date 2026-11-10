from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from nextrip_ai.core.database import Base

class Trip(Base):
    __tablename__ = "trips"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    destination: Mapped[str] = mapped_column(String, nullable=False)
    days: Mapped[int] = mapped_column(nullable=False)
    budget: Mapped[int] = mapped_column(nullable=False)
    trip_style: Mapped[str] = mapped_column(String, nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)

    itinerary: Mapped["Itinerary"] = relationship("Itinerary", back_populates="trip", uselist=False)
