from pydantic import BaseModel


class InsightItem(BaseModel):
    message: str
    type: str = "info"  # "info" | "positive" | "warning"


class InsightsResponse(BaseModel):
    insights: list[InsightItem]
    disclaimer: str
