from pydantic import BaseModel

class InterviewBase(BaseModel):
    title: str | None = None
    assessment: str | None = None
    scheduled_at: str | None = None

class InterviewCreate(InterviewBase):
    pass

class Interview(InterviewBase):
    id: int

    class Config:
        from_attributes = True
