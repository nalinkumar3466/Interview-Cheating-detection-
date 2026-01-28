from sqlalchemy import Column, Integer, String, Text, DateTime, Float, ForeignKey
from sqlalchemy.sql import func
from ml.db.database import Base


class InterviewAnalysis(Base):
    __tablename__ = "interview_analysis"

    id = Column(Integer, primary_key=True, index=True)

    # Must match backend
    interview_id = Column(
        Integer,
        nullable=False,
        index=True
    )

    status = Column(
        String,
        default="pending"
    )  # pending, processing, completed, failed

    event_percentages = Column(Text, nullable=True)

    analysis_report = Column(Text, nullable=True)

    risk_level = Column(String, nullable=True)

    effective_risk_percentage = Column(Float, nullable=True)

    error_message = Column(Text, nullable=True)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    updated_at = Column(
        DateTime(timezone=True),
        onupdate=func.now()
    )
