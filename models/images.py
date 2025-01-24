from sqlalchemy import Column, Integer, String

from database import Base


class Image(Base):
    __tablename__ = 'images'
    id: int = Column(Integer, primary_key=True, autoincrement=True)
    image: str = Column(String(255), nullable=False)

    def __repr__(self) -> str:
        return f"Image(id={self.id!r}, image={self.image[:50]!r})"
