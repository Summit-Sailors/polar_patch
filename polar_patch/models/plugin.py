from sqlmodel import SQLModel


class PluginInfoSM(SQLModel, Table=True):
  modname: str
  polars_namespace: str
  namespace: str
  cls_name: str
