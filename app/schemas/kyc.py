"""KYC and Roommate schemas."""

import uuid
from datetime import datetime
from typing import List, Optional
from pydantic import Field

from app.core.constants import KYCDocumentType, KYCStatus
from app.schemas.common import BaseSchema


class KYCSubmitRequest(BaseSchema):
    document_type: KYCDocumentType
    document_number: str = Field(..., min_length=5, max_length=50)
    front_document_url: str
    back_document_url: Optional[str] = None
    student_or_work_id_url: Optional[str] = None


class KYCAdminDecisionRequest(BaseSchema):
    decision: KYCStatus = Field(..., description="APPROVED or REJECTED")
    rejection_reason: Optional[str] = None


class KYCOut(BaseSchema):
    id: uuid.UUID
    user_id: uuid.UUID
    status: KYCStatus
    document_type: KYCDocumentType
    document_number: str
    front_document_url: str
    back_document_url: Optional[str] = None
    student_or_work_id_url: Optional[str] = None
    rejection_reason: Optional[str] = None
    verified_at: Optional[datetime] = None
    created_at: datetime


class RoommatePreferenceCreate(BaseSchema):
    smoking_allowed: bool = False
    sleep_schedule: str = "NORMAL"  # EARLY_BIRD, NIGHT_OWL, NORMAL, FLEXIBLE
    cleanliness_level: int = Field(default=3, ge=1, le=5)
    guests_allowed: bool = True
    dietary_preference: str = "ANY"  # VEG, NON_VEG, ANY
    study_habit: str = "QUIET"
    additional_notes: Optional[str] = None


class RoommatePreferenceOut(RoommatePreferenceCreate):
    id: uuid.UUID
    user_id: uuid.UUID
    created_at: datetime


class CompatibilityResult(BaseSchema):
    candidate_user_id: uuid.UUID
    candidate_name: str
    compatibility_score: float = Field(..., description="Score between 0 and 100")
    matched_factors: List[str] = Field(default_factory=list)
