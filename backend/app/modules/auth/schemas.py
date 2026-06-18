from pydantic import BaseModel, EmailStr, Field


class SignupRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    company_name: str = Field(min_length=1)
    nit: str | None = None


class SignupResponse(BaseModel):
    user_id: str
    tenant_id: str
    company_id: str


class MeResponse(BaseModel):
    user_id: str
    email: str | None
    tenant_id: str
    role: str
