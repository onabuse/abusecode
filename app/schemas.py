from pydantic import BaseModel, Field


class KeyIn(BaseModel):
    name: str = Field(default="key", max_length=80)
    api_key: str = Field(min_length=1, max_length=512)


class KeyPatch(BaseModel):
    active: bool


class LoginIn(BaseModel):
    token: str = ""
