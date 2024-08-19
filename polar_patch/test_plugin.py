import polars as pl


@pl.api.register_lazyframe_namespace("plugin_namespace")
class PluginImpl:
  pass
