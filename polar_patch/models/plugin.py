from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PluginInfoDC:
  polars_namespace: str
  plugin_namespace: str
  impl_name: str


@dataclass(frozen=True, slots=True)
class PluginLockDC(PluginInfoDC):
  modpath: str
  package_name: str
