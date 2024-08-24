from pathlib import Path

from sqlmodel import SQLModel


class PolarPatchConfig(SQLModel):
  include: list[Path]


class Config(SQLModel):
  polar_patch: PolarPatchConfig
