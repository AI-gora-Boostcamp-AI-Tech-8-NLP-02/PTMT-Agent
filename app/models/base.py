from pydantic import BaseModel


# Error Response Models
class ErrorResponse(BaseModel):
    error_code: str
    message: str
