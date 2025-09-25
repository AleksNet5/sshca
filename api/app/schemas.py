from pydantic import BaseModel, Field
from typing import List

class SignRequest(BaseModel):
  username: str = Field(min_length=1)
  principals: List[str]
  pubkey: str
  ttl: str | None = "16h"

class SignResponse(BaseModel):
  key_id: str
  serial: int
  cert: str

class RevokeRequest(BaseModel):
  serial: int
