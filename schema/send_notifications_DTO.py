from pydantic import BaseModel


class SendNotificationDTO(BaseModel):
    subject: str
    body: str
