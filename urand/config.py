"""Utilities shared across modules"""

import confuse
import os

from pluginbase import PluginBase

root_path = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
plugin_dirs = ["./plugins"]
plugin_base = PluginBase(
    package="plugins", searchpath=[os.path.join(root_path, "plugins")]
)
plugins = plugin_base.make_plugin_source(searchpath=plugin_dirs)

config = confuse.LazyConfig("UrnRandomization", __name__)
# Allow config.yaml at project root with highest priority
if os.path.isfile("config.yaml"):
    config.set_file("config.yaml")

# Change database URI to absolute path format for access by flask login
db_uri = config["db"].get().split(":", 1)[1]
if (len(db_uri) - len(db_uri.lstrip("/"))) == 3:
    db_uri = (
        config["db"].get().split(":", 1)[0]
        + ":///"
        + os.path.join(root_path, config["db"].get().split(":", 1)[1][3:])
    )

config["db"] = db_uri
