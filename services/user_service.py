from fastapi import HTTPException
from sqlalchemy.orm import Session

from models.users import Users
from schema.user_DTO import CreateUserDTO


def create_user(dto: CreateUserDTO, db: Session):
    existing_user = db.query(Users).filter(Users.email == dto.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail=f"User is already registered with '{dto.email}'")

    new_user = Users(**dto.dict())
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user


def get_user(db: Session):
    return db.query(Users).all()
