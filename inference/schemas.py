from pydantic import BaseModel, Field

class GenerateRequest(BaseModel):
    title: str = Field(..., example="Cozy Wool Sweater")
    description: str = Field(..., example="Soft winter sweater, warm and stylish.")
    category: str = Field("general", example="clothing")

class GenerateResponse(BaseModel):
    creatives: list[str]
