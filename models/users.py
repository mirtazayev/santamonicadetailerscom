from sqlalchemy import Column, Integer, String

from database import Base


class Users(Base):
    __tablename__ = 'user'
    id: int = Column(Integer, primary_key=True, unique=True, index=True, nullable=False)
    fullname: str = Column(String(100), index=False)
    email: str = Column(String(300))

    def __repr__(self) -> str:
        return f"Users(id={self.id!r}, email={self.email!r})"
