import bpy
import bmesh
import importlib
from . import plg
importlib.reload(plg)


def coll2plg(filepath, coll, mys, color = False):
    print("running coll2plg...")

    for obj in coll.all_objects:
        if obj.type != 'MESH':
            raise Exception("<{:s}> contains non-mesh objects".format(coll.name))

    tmp = {}
    for obj in sorted(coll.all_objects, key=lambda o: o.name):
        bm = bmesh.new()
        bm.from_mesh(obj.data)

        name = obj.name.split("~")
        name = name[0] if len(name) == 1 else name[1]

        verts = []
        for bmvert in bm.verts:
            plgvert = plg.V10(0xff, 0xff, 0xff, 0xff, bmvert.co.x, -bmvert.co.y, 0)
            plgvert = plgvert._asdict()
            if color:
                plgvert['a'] = 0 if bmvert.is_boundary else 0xff
            plgvert['f'] = 0x00010000 if bmvert.is_boundary else 0x00000000
            verts.append(plgvert)

        cl = None
        if len(bm.loops.layers.color) > 0:
            cl = bm.loops.layers.color[0]

        faces, ngon = [], set()
        for bf in bm.faces:
            plgface = [bv.index for bv in bf.verts]
            faces.append(plgface)
            ngon.add(len(plgface))
            if cl and not color:
                for loop in bf.loops:
                    v = verts[loop.vert.index]
                    v['r'], v['g'], v['b'], v['a'] = [int(x * 0xff) for x in loop[cl]]

        if len(ngon) > 1:
            raise Exception("mixed face n-gons: " + str(ngon))

        tmp[name] = ([plg.V10(**v) for v in verts], faces)

    plg.export_plg(filepath, plg.tmp2plgf(tmp, mys))
    return {'FINISHED'}


from bpy_extras.io_utils import ExportHelper
from bpy.props import StringProperty, BoolProperty, EnumProperty
from bpy.types import Operator


class ExportPLG(Operator, ExportHelper):
    """Export PLG mesh collection"""

    bl_idname = "io_plg.export_plg"
    bl_label = "Export PLG"

    filename_ext = ".plg"

    filter_glob: StringProperty(
        default="*.plg",
        options={'HIDDEN'},
        maxlen=255,
    )

    mys: EnumProperty(
        name = "Mystery Bytes",
        description = "Game/PLG version",
        items = {
            ('0x01000400', "P5 0x38"  , "P5, Header Size 0x38"),
            ('0x01000300', "P5 0x20"  , "P5, Header Size 0x20"),
            ('0x01000200', "P5 0x20*" , "P5, Header Size 0x20 (fclItem)"),
            ('0x02000000', "P3D/P5D/PQ2 0x38", "P3D/P5D/PQ2, Header Size 0x38"),
        },
        default = '0x01000400',
    )

    color: BoolProperty(
        name = "Auto Color",
        description = "Color inner verts with 100% opaque white, outer verts with 100% transparent white",
        default = True
    )

    def execute(self, context):
        alc = context.view_layer.active_layer_collection
        coll = [c for c in bpy.data.collections if c.name == alc.name][0]

        try:
            return coll2plg(self.filepath, coll, int(self.mys, 16), self.color)
        except Exception as e:
            self.report({'ERROR'}, str(e))
            return {'CANCELLED'}


def menu_func_export(self, context):
    self.layout.operator(ExportPLG.bl_idname, text="Export PLG (.plg)")


def register():
    bpy.utils.register_class(ExportPLG)
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)


def unregister():
    bpy.utils.unregister_class(ExportPLG)
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)


if __name__ == "__main__":
    register()

    # test call
    bpy.ops.io_plg.export_plg('INVOKE_DEFAULT')
