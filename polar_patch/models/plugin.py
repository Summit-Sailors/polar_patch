from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PluginInfoDC:
  polars_namespace: str
  namespace: str
  cls_name: str


@dataclass(frozen=True, slots=True)
class PluginLockDC(PluginInfoDC):
  modname: str
  pkg_name: str
