import importlib.util
import os

# The subdirectory name contains a hyphen, which is not a valid Python identifier,
# so we load the plugin module by file path instead of dot-notation import.
_plugin_path = os.path.join(os.path.dirname(__file__), "IT-100_Integration_Module", "plugin.py")
_spec = importlib.util.spec_from_file_location("dsc_it100_plugin", _plugin_path)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)

PLUGIN_CLASS = _mod.PLUGIN_CLASS

__all__ = ["PLUGIN_CLASS"]
