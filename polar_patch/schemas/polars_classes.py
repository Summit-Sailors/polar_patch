POLARS_NAMESPACE_TO_DECORATOR = {
  "register_expr_namespace": "Expr",
  "register_dataframe_namespace": "DataFrame",
  "register_lazyframe_namespace": "LazyFrame",
  "register_series_namespace": "Series",
}
POLARS_NAMESPACE_DECORATORS = set(POLARS_NAMESPACE_TO_DECORATOR.keys())
POLARS_NAMESPACES = set(POLARS_NAMESPACE_TO_DECORATOR.values())
