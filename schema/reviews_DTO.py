from pydantic import BaseModel


class ReviewDTO(BaseModel):
    name: str
    description: str


class DeleteReviewsDTO(BaseModel):
    id: int
