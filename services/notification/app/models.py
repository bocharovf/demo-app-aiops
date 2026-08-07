import datetime

from sqlalchemy import JSON, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Notification(Base):
    __tablename__ = "notifications"
    __table_args__ = {"schema": "notifications"}

    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int]
    type: Mapped[str]
    status: Mapped[str] = mapped_column(default="sent")
    payload: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime.datetime] = mapped_column(server_default=func.now())
    sent_at: Mapped[datetime.datetime] = mapped_column(server_default=func.now())
