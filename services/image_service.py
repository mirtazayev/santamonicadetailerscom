import secrets

from fastapi import UploadFile
from sqlalchemy.orm import Session

from models.images import Image

MEDIA_DIR = "media/images/"


def save_image(file: UploadFile):
    file_name = secrets.token_hex(8) + ".jpg"

    with open(f"{MEDIA_DIR}{file_name}", "wb") as buffer:
        buffer.write(file.file.read())

    file_url = f"/media/images/{file_name}"
    return file_url


def create_image_record(db: Session, file_url: str):
    image = Image(image=file_url)
    db.add(image)
    db.commit()
    db.refresh(image)
    return image


def get_all_images(db: Session):
    return db.query(Image).all()
