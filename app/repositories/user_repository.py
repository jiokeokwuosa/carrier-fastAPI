"""Database access for User records."""

from typing import List, Optional

from sqlalchemy.orm import Session

from app.models import User, UserRole


class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def find_by_email(self, email: str) -> Optional[User]:
        return self.db.query(User).filter(User.email == email.lower()).first()

    def find_by_id(self, user_id: str) -> Optional[User]:
        return self.db.query(User).filter(User.id == user_id).first()

    def create(self, email: str, password_hash: str, roles: Optional[List[str]] = None) -> User:
        user = User(
            email=email.lower(),  # Normalize so lookups are case-insensitive
            password_hash=password_hash,
            roles=roles or [UserRole.USER.value],
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user
