from typing import ClassVar

import polars as pl
from nicegui import ui
from typing_extensions import Any


@pl.api.register_lazyframe_namespace("aggrid")
class AggridFrame:
  aggrid_talbe_defaults: ClassVar[dict[str, Any]] = {
    ":getRowId": "(params) => params.data.id",
    "suppressDotNotation": True,
    "undoRedoCellEditing": True,
    "sideBar": ["columns", "filters"],
    "pagination": True,
    "paginationPageSize": 25,
    "paginationPageSizeSelector": True,
    "suppressDragLeaveHidesColumns": True,
    "enableAdvancedFilter": True,
    "multiSortKey": "ctrl",
    "editType": "fullRow",
  }
  aggrid_column_defaults: ClassVar[dict[str, Any]] = {
    "sortable": True,
    "checkboxSelection": True,
    "editable": False,
    "filter": True,
    "floatingFilter": True,
    "resizable": True,
  }

  def __init__(self, df: "pl.LazyFrame") -> None:
    self._df = df
    self._original_row_data: dict[str, Any] | None = None
    self.change_log: dict[str, list[Any]] = {"updates": [], "inserts": [], "deletes": [], "deletions": []}

  def aggrid(self) -> None:
    materlized_df = self._df.collect()
    if not (data := materlized_df.to_dicts()):
      ui.notify("Empty")
      return
    ui.aggrid(
      {
        "columnDefs": [
          {"field": str(materlized_df.columns[0]), **self.aggrid_column_defaults},
          *[
            {"field": str(col), "editable": False, "sortable": True, "filter": True, "floatingFilter": True, "resizable": True}
            for col in materlized_df.columns[1:]
          ],
        ],
        "rowData": data,
        **self.aggrid_talbe_defaults,
      },
      theme="balham-dark",
      auto_size_columns=True,
    ).classes("w-full")
    ui.label().classes("whitespace-pre font-mono").bind_text_from(globals(), "data", lambda x: "Data: \n{0}".format("\n".join([str(y) for y in x])))
