from fastapi import UploadFile, File
from pydantic import BaseModel


class ImageDTO(BaseModel):
    image: UploadFile or None = File(None)
