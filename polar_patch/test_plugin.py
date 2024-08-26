import polars as pl


@pl.api.register_lazyframe_namespace("plugin_namespace")
class LazyPluginImpl:
  pass


@pl.api.register_dataframe_namespace("not_lazy_plugin_namespace")
class PluginImpl:
  pass
