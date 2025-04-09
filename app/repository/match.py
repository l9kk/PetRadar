from typing import List, Optional, Any
from datetime import datetime
import uuid

from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc, and_

from app.models.match import Match
from app.models.pet import Pet
from app.models.found_pet import FoundPet
from app.repository.base import BaseRepository


class MatchRepository(BaseRepository[Match, Any, Any]):
    def __init__(self, db: Session):
        super().__init__(db, Match)

    def get_with_details(self, match_id: uuid.UUID) -> Optional[Match]:
        return (
            self.db.query(Match)
            .options(
                joinedload(Match.lost_pet).joinedload(Match.lost_pet.owner),
                joinedload(Match.found_pet).joinedload(Match.found_pet.finder),
            )
            .filter(Match.id == match_id)
            .first()
        )

    def create_match(
        self,
        *,
        lost_pet_id: uuid.UUID,
        found_pet_id: uuid.UUID,
        similarity: float,
        matching_features: Optional[List[str]] = None,
    ) -> Match:
        existing = (
            self.db.query(Match)
            .filter(
                Match.lost_pet_id == lost_pet_id, Match.found_pet_id == found_pet_id
            )
            .first()
        )

        if existing:
            if similarity > existing.similarity:
                existing.similarity = similarity
                existing.matching_features = matching_features
                self.db.add(existing)
                self.db.commit()
                self.db.refresh(existing)
            return existing

        db_obj = Match(
            lost_pet_id=lost_pet_id,
            found_pet_id=found_pet_id,
            similarity=similarity,
            status="pending",
            matching_features=matching_features,
        )
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def update_match_status(
        self, *, match_id: uuid.UUID, status: str
    ) -> Optional[Match]:
        match = self.get(id=match_id)
        if not match:
            return None

        match.status = status
        if status == "confirmed":
            match.confirmation_date = datetime.utcnow()

        self.db.add(match)
        self.db.commit()
        self.db.refresh(match)
        return match

    def get_user_matches(
        self,
        *,
        user_id: uuid.UUID,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 20,
    ) -> List[Match]:
        query = self.db.query(Match).join(
            Pet, and_(Pet.id == Match.lost_pet_id, Pet.owner_id == user_id)
        )

        if status:
            query = query.filter(Match.status == status)

        return query.order_by(desc(Match.created_at)).offset(skip).limit(limit).all()

    def get_finder_matches(
        self,
        *,
        user_id: uuid.UUID,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 20,
    ) -> List[Match]:
        query = self.db.query(Match).join(
            FoundPet,
            and_(FoundPet.id == Match.found_pet_id, FoundPet.finder_id == user_id),
        )

        if status:
            query = query.filter(Match.status == status)

        return query.order_by(desc(Match.created_at)).offset(skip).limit(limit).all()
