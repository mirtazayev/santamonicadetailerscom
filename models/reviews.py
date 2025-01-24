import datetime

from sqlalchemy import Column, Integer, String, DateTime

from database import Base


class Reviews(Base):
    __tablename__ = 'reviews'
    id: int = Column(Integer, primary_key=True, autoincrement=True)
    name: str = Column(String(255), nullable=False)
    description: str = Column(String(1000), nullable=False)
    created_at: datetime.datetime = Column(DateTime(), default=datetime.datetime.utcnow)
    updated_at: datetime.datetime = Column(DateTime(), default=datetime.datetime.utcnow,
                                           onupdate=datetime.datetime.utcnow)

    def __repr__(self) -> str:
        description_preview = self.description[:50] + "..." if len(self.description) > 50 else self.description
        return f"Reviews(id={self.id!r}, name={self.name!r}, description={description_preview!r})"
