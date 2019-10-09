import bpy
import importlib
from . import plg_import
from . import plg_export
importlib.reload(plg_import)
importlib.reload(plg_export)


bl_info = {
    "name": "PLG format",
    "author": "amicitia",
    "version": (0, 0, 2),
    "blender": (2, 80, 0),
    "location": "File > Import-Export > PLG (.plg)",
    "description": "Import-Export PLG mesh collections",
    "warning": "",
    "wiki_url": "",
    "category": "Import-Export",
}


def register():
    plg_import.register()
    plg_export.register()


def unregister():
    plg_import.unregister()
    plg_export.unregister()


if __name__ == "__main__":
    register()
