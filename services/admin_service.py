from sqlalchemy.orm import Session

from models.admins import Admins
from schema.admin_DTO import CreateAdminDTO
from services.auth_service import hash_password  # Assuming this service hashes the password


def create_admin(dto: CreateAdminDTO, db: Session):
    existing_admin = db.query(Admins).filter(Admins.username == dto.username).first()

    if existing_admin:
        raise ValueError(f"Admin with username '{dto.username}' already exists.")

    hashed_password = hash_password(dto.password)

    new_admin = Admins(
        username=dto.username,
        password=hashed_password,
    )

    db.add(new_admin)
    db.commit()
    db.refresh(new_admin)

    return new_admin


def create_default_admin(db: Session):
    existing_admin = db.query(Admins).filter(Admins.username == "aquapowers").first()

    if not existing_admin:
        hashed_password = hash_password("adminpanel")  # Hash the password before storing
        new_admin = Admins(username="aquapowers", password=hashed_password)
        db.add(new_admin)
        db.commit()
        db.refresh(new_admin)
        print("Default admin created successfully.")
    else:
        print("Default admin already exists.")
