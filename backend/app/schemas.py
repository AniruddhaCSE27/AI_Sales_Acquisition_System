from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, field_validator
from app.models import LeadStatus, Role


class Token(BaseModel):
    access_token: str
    refresh_token: str | None = None
    token_type: str = "bearer"
    role: Role


class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str = Field(min_length=8)
    role: Role


class UserRead(BaseModel):
    id: int
    name: str
    email: EmailStr
    role: Role
    is_active: bool
    model_config = {"from_attributes": True}


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class PublisherCreate(BaseModel):
    name: str
    contact_email: EmailStr | None = None
    commission_rate: float = 0


class PublisherRead(PublisherCreate):
    id: int
    quality_score: float
    roi_score: float
    model_config = {"from_attributes": True}


class LeadCreate(BaseModel):
    name: str
    phone: str
    email: EmailStr | None = None
    city: str | None = None
    state: str | None = None
    course_interest: str | None = None
    course: str | None = None
    budget: float | None = None
    lead_source: str = "manual"
    source: str | None = None
    publisher_id: int | None = None
    publisher: str | None = None
    lead_notes: str | None = None
    tags: list[str] = Field(default_factory=list)

    def model_post_init(self, __context) -> None:
        if self.course and not self.course_interest:
            self.course_interest = self.course
        if self.source:
            self.lead_source = self.source


class LeadUpdate(BaseModel):
    status: LeadStatus | None = None
    telecaller_id: int | None = None
    counsellor_id: int | None = None
    follow_up_date: datetime | None = None
    tags: list[str] | None = None


class LeadRead(LeadCreate):
    id: int
    lead_score: float
    conversion_probability: float
    predicted_revenue: float
    quality_class: str
    status: LeadStatus
    last_contacted: datetime | None
    counsellor_id: int | None
    telecaller_id: int | None
    follow_up_date: datetime | None
    sentiment_score: float
    engagement_score: float
    score_explanation: dict
    created_at: datetime
    model_config = {"from_attributes": True}

    @field_validator("publisher", mode="before")
    @classmethod
    def publisher_to_name(cls, value):
        if value is None or isinstance(value, str):
            return value
        return getattr(value, "name", None)


class LeadTimelineEvent(BaseModel):
    id: int
    action: str
    metadata_json: dict
    created_at: datetime
    model_config = {"from_attributes": True}


class BulkAction(BaseModel):
    lead_ids: list[int]
    status: LeadStatus | None = None
    telecaller_id: int | None = None
    counsellor_id: int | None = None
    follow_up_date: datetime | None = None


class ImportPreview(BaseModel):
    headers: list[str]
    suggested_mapping: dict[str, str]
    rows: list[dict]


class ImportResult(BaseModel):
    batch_id: int
    total_rows: int
    created: int
    skipped_duplicates: int
    errors: int
    duplicate_report: list[dict]


class PaginatedLeads(BaseModel):
    items: list[LeadRead]
    total: int
    page: int
    page_size: int


class CallCreate(BaseModel):
    lead_id: int
    user_id: int | None = None


class CallRead(BaseModel):
    id: int
    lead_id: int
    user_id: int | None
    status: str
    duration_seconds: int
    summary: str | None
    sentiment_score: float
    intent: str | None
    next_action: str | None
    created_at: datetime
    model_config = {"from_attributes": True}


class ChatRequest(BaseModel):
    question: str


class ChatResponse(BaseModel):
    answer: str
    recommendations: list[str] = []
