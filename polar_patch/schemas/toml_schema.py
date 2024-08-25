from pathlib import Path

from pydantic import BaseModel


class PolarPatchConfig(BaseModel):
  include: list[Path]
  name: str


class Config(BaseModel):
  polar_patch: PolarPatchConfig
