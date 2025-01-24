from pydantic import BaseModel


class CreateUserDTO(BaseModel):
    fullname: str
    email: str
