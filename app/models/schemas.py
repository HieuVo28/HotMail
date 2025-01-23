from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime

class TokenData(BaseModel):
    email: EmailStr
    access_token: str
    expires_at: Optional[datetime] = None

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_at: datetime

class OTPResponse(BaseModel):
    otp: str
    date: str
    subject: str
    from_: str = None

    class Config:
        allow_population_by_field_name = True
        fields = {
            'from_': 'from'
        }

class EmailResponse(BaseModel):
    subject: str
    from_: str
    date: str
    content: str

    class Config:
        allow_population_by_field_name = True
        fields = {
            'from_': 'from'
        }

class EmailSearchQuery(BaseModel):
    query: str
    folders: Optional[List[str]] = None 