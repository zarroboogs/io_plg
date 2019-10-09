import bpy
import bmesh
from pathlib import Path
import importlib
from . import plg
importlib.reload(plg)


def plg2coll(context, filepath):
    print("running plg2coll...")
    plgf = plg.import_plg(filepath)

    scene = context.scene

    # create plg file collection
    plgcoll = bpy.data.collections.new(Path(filepath).name)
    scene.collection.children.link(plgcoll)

    objc = 0

    for plgobj in plgf.objs:
        bm = bmesh.new()

        # add verts
        for plgvert in plgobj.verts:
            bm.verts.new((plgvert.x, -plgvert.y, 0))
        bm.verts.ensure_lookup_table()
        bm.verts.index_update()

        # add faces + vert color
        cl = bm.loops.layers.color.new("col")
        for plgface in plgobj.faces:
            face = bm.faces.new([bm.verts[vertidx] for vertidx in plgface])
            for loop in face.loops:
                v = plgobj.verts[loop.vert.index]
                loop[cl] = [v.r / 0xff, v.g / 0xff, v.b / 0xff, v.a / 0xff]
        bm.faces.ensure_lookup_table()

        # create plg object mesh
        n = plg.decode_name(plgobj.obj)
        meshdata = bpy.data.meshes.new("m{:03d}~{:s}".format(objc, n))
        bm.to_mesh(meshdata)
        bm.free()

        # create plg object
        obj = bpy.data.objects.new("o{:03d}~{:s}".format(objc, n), meshdata)
        plgcoll.objects.link(obj)
        objc += 1

    return {'FINISHED'}


from bpy_extras.io_utils import ImportHelper
from bpy.props import StringProperty
from bpy.types import Operator


class ImportPLG(Operator, ImportHelper):
    """Import PLG mesh collection"""

    bl_idname = "io_plg.import_plg"
    bl_label = "Import PLG"

    filename_ext = ".plg"

    filter_glob: StringProperty(
        default="*.plg",
        options={'HIDDEN'},
        maxlen=255,
    )

    def execute(self, context):
        try:
            return plg2coll(context, self.filepath)
        except Exception as e:
            self.report({'ERROR'}, str(e))
            return {'CANCELLED'}


def menu_func_import(self, context):
    self.layout.operator(ImportPLG.bl_idname, text="Import PLG (.plg)")


def register():
    bpy.utils.register_class(ImportPLG)
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)


def unregister():
    bpy.utils.unregister_class(ImportPLG)
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)


if __name__ == "__main__":
    register()

    # test call
    bpy.ops.io_plg.import_plg('INVOKE_DEFAULT')
