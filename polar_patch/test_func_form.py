import polars as pl

from polar_patch.test_func_form_classes import PluginFuncFormImpl, LazyPluginFuncFormImpl

pl.api.register_lazyframe_namespace("plugin_namespace_func")(LazyPluginFuncFormImpl)


pl.api.register_dataframe_namespace("not_lazy_plugin_namespace_func")(PluginFuncFormImpl)
