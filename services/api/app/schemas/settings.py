from pydantic import BaseModel, ConfigDict, Field

class SettingsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    preferred_model: str | None = None
    response_style: str

class SettingsUpdate(BaseModel):
    preferred_model: str | None = Field(default=None, max_length=120)
    response_style: str = Field(default="balanced", pattern="^(concise|balanced|detailed)$")
