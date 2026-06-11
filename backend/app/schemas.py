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

    @field_validator("role", mode="before")
    @classmethod
    def normalize_enterprise_role(cls, value):
        if isinstance(value, str):
            normalized = value.strip()
            enterprise_aliases = {
                "ADMIN": Role.admin,
                "MANAGER": Role.manager,
                "AGENT": Role.agent,
            }
            return enterprise_aliases.get(normalized.upper(), normalized.lower())
        return value


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


class CustomerMemoryBase(BaseModel):
    objections: list[str] = Field(default_factory=list)
    sentiment: str | None = None
    budget: float | None = None
    preferred_contact_time: str | None = None
    summary: str | None = None
    next_action: str | None = None
    metadata_json: dict = Field(default_factory=dict)


class CustomerMemoryUpdate(CustomerMemoryBase):
    pass


class CustomerMemoryRead(CustomerMemoryBase):
    id: int
    lead_id: int
    created_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}


class LeadIntelligenceRequest(BaseModel):
    notes: str | None = None


class LeadIntelligenceResponse(BaseModel):
    lead_id: int
    lead_score: float
    lead_score_explanation: dict
    sentiment: str
    sentiment_score: float
    intent: str
    objections: list[str]
    next_best_action: str


class FollowUpRequest(BaseModel):
    lead_id: int | None = None
    channel: str | None = None
    objective: str | None = None
    tone: str = "professional"


class FollowUpResponse(BaseModel):
    lead_id: int
    whatsapp_message: str
    email_subject: str
    email_body: str
    call_script: str


class CallingAgentRequest(BaseModel):
    lead_name: str = Field(min_length=1, max_length=160)
    phone_number: str = Field(min_length=7, max_length=40)
    objective: str = Field(min_length=1, max_length=500)
    product: str = Field(min_length=1, max_length=255)
    tone: str = "Professional"
    language: str = "English"
    consent: bool = False

    @field_validator("tone")
    @classmethod
    def validate_tone(cls, value: str) -> str:
        allowed = {"Professional", "Friendly", "Persuasive"}
        normalized = value.strip().title()
        if normalized not in allowed:
            raise ValueError(f"tone must be one of: {', '.join(sorted(allowed))}")
        return normalized

    @field_validator("language")
    @classmethod
    def validate_language(cls, value: str) -> str:
        allowed = {"English", "Hindi", "Hinglish"}
        normalized = value.strip().title()
        if normalized not in allowed:
            raise ValueError(f"language must be one of: {', '.join(sorted(allowed))}")
        return normalized


class CallingAgentScriptResponse(BaseModel):
    opening_line: str
    qualification_questions: list[str]
    objection_handling: list[str]
    closing_line: str
    full_script: str
    session_id: int


class CallingAgentSimulationResponse(BaseModel):
    ai_agent_message: str
    customer_possible_reply: str
    next_ai_response: str
    call_summary: str
    interest_level: str
    sentiment: str
    lead_score: float
    detected_objection: str
    ai_suggested_response: str
    next_best_action: str
    session_id: int


class CallingAgentSaveRequest(CallingAgentRequest):
    script: str | None = None
    simulation: dict = Field(default_factory=dict)
    summary: str | None = None
    interest_level: str | None = None
    sentiment: str | None = None
    lead_score: float = 0.0
    objection: str | None = None
    suggested_response: str | None = None
    next_action: str | None = None


class KnowledgeDocumentRead(BaseModel):
    id: int
    title: str
    source_filename: str | None
    created_at: datetime
    model_config = {"from_attributes": True}


class KnowledgeSearchResult(BaseModel):
    score: float
    document_id: int | None = None
    title: str | None = None
    content: str
    citation: str


class KnowledgeAskRequest(BaseModel):
    question: str


class KnowledgeAskResponse(BaseModel):
    answer: str
    citations: list[KnowledgeSearchResult]
