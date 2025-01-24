from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from models.reviews import Reviews
from schema.reviews_DTO import ReviewDTO


def get_all_reviews(db: Session):
    reviews = db.query(Reviews).all()
    return reviews


def create_review(dto: ReviewDTO, db: Session):
    try:
        review = Reviews(**dto.dict())
        db.add(review)
        db.commit()
        db.refresh(review)
        return review
    except SQLAlchemyError as e:
        db.rollback()
        raise RuntimeError(f"Database error: {e}")
