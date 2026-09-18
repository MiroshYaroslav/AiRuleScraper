from sqlalchemy import Column, Integer, String
from .base import Base


class ScrapingTask(Base):
    __tablename__ = "scraping_tasks"

    id = Column(Integer, primary_key=True)
    url = Column(String, unique=True, nullable=False)
    status = Column(
        String, default="PENDING", nullable=False
    )  # PENDING, PROCESSING, DONE, ERROR
