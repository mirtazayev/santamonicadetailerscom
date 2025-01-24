from pydantic import BaseModel


class CreateAdminDTO(BaseModel):
    username: str
    password: str


class AdminDTO(BaseModel):
    username: str

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
        }
