from pydantic import BaseModel


class ContactForm(BaseModel):
    name: str
    email: str
    phone: str
    message: str
