from pathlib import Path

from pydantic import BaseModel


class PolarPatchConfig(BaseModel):
  python_interpreter: Path
  scan_paths: list[Path]


class Config(BaseModel):
  polar_patch: PolarPatchConfig
