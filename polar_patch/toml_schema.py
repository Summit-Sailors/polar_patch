from pathlib import Path

from pydantic import BaseModel


class PolarPatchConfig(BaseModel):
  scan_paths: list[Path]


class Config(BaseModel):
  polar_patch: PolarPatchConfig
