import bpy
import bmesh
import os
import sys
import platform
import subprocess


def clear():
    os.system("clear")


def get_active():
    return bpy.context.active_object


def make_active(obj):
    bpy.context.view_layer.objects.active = obj
    return obj


def selected_objects():
    return bpy.context.selected_objects


def select_all(string):
    if string == "MESH":
        bpy.ops.mesh.select_all(action='SELECT')
    elif string == "OBJECT":
        bpy.ops.object.select_all(action='SELECT')


def unselect_all(string):
    if string == "MESH":
        bpy.ops.mesh.select_all(action='DESELECT')
    elif string == "OBJECT":
        bpy.ops.object.select_all(action='DESELECT')


def select(objlist):
    for obj in objlist:
        obj.select = True


def hide_all(string):
    if string == "OBJECT":
        select_all(string)
        bpy.ops.object.hide_view_set(unselected=False)
    elif string == "MESH":
        select_all(string)
        bpy.ops.mesh.hide(unselected=False)


def unhide_all(string="OBJECT"):
    if string == "OBJECT":
        for obj in bpy.data.objects:
            obj.hide = False
    elif string == "MESH":
        bpy.ops.mesh.reveal()


def get_mode():
    mode = bpy.context.mode

    if mode == "OBJECT":
        return "OBJECT"
    elif mode == "EDIT_MESH":
        return get_mesh_select_mode()


def get_mesh_select_mode():
    mode = tuple(bpy.context.scene.tool_settings.mesh_select_mode)
    if mode == (True, False, False):
        return "VERT"
    elif mode == (False, True, False):
        return "EDGE"
    elif mode == (False, False, True):
        return "FACE"
    else:
        return None


def set_mode(string, extend=False, expand=False):
    if string == "EDIT":
        bpy.ops.object.mode_set(mode='EDIT')
    elif string == "OBJECT":
        bpy.ops.object.mode_set(mode='OBJECT')
    elif string in ["VERT", "EDGE", "FACE"]:
        bpy.ops.mesh.select_mode(use_extend=extend, use_expand=expand, type=string)



def change_context(string):
    area = bpy.context.area

    print("area:", area)

    old_type = area.type

    print("old type before:", old_type)

    area.type = string

    print("old type after:", old_type)

    return old_type


def change_pivot(string):
    space_data = bpy.context.space_data
    old_type = space_data.pivot_point
    space_data.pivot_point = string
    return old_type


def DM_check():
    return addon_check("DECALmachine")


def MM_check():
    return addon_check("MESHmachine")


def RM_check():
    return addon_check("RIGmachine")


def HOps_check():
    return addon_check("HOps")


def BC_check():
    return addon_check("BoxCutter")


def AM_check():
    return addon_check("asset_management", precise=False)


def GP_check():
    return addon_check("GroupPro")


def addon_check(string, precise=True):
    for addon in bpy.context.user_preferences.addons.keys():
        if precise:
            if string == addon:
                return True
        else:
            if string.lower() in addon.lower():
                return True
    return False


def move_to_cursor(obj, scene):
    obj.select = True
    make_active(obj)
    obj.location = bpy.context.scene.cursor_location


def lock(obj, location=True, rotation=True, scale=True):
    if location:
        for idx, _ in enumerate(obj.lock_location):
            obj.lock_location[idx] = True

    if rotation:
        for idx, _ in enumerate(obj.lock_rotation):
            obj.lock_rotation[idx] = True

    if scale:
        for idx, _ in enumerate(obj.lock_scale):
            obj.lock_scale[idx] = True


def open_folder(pathstring):

    if platform.system() == "Windows":
        os.startfile(pathstring)
    elif platform.system() == "Darwin":
        subprocess.Popen(["open", pathstring])
    else:
        # subprocess.Popen(["xdg-open", pathstring])
        os.system('xdg-open "%s" %s &' % (pathstring, "> /dev/null 2> /dev/null"))  # > sends stdout,  2> sends stderr


def makedir(pathstring):
    if not os.path.exists(pathstring):
        os.makedirs(pathstring)
    return pathstring


def addon_prefs(addonstring):
    return bpy.context.user_preferences.addons[addonstring].preferences


def DM_prefs():
    return bpy.context.user_preferences.addons["DECALmachine"].preferences


def MM_prefs():
    return bpy.context.user_preferences.addons["MESHmachine"].preferences


def RM_prefs():
    return bpy.context.user_preferences.addons["RIGmachine"].preferences


def M3_prefs():
    return bpy.context.user_preferences.addons["MACHIN3tools"].preferences


def make_selection(string, idlist):
    mesh = bpy.context.object.data
    set_mode("OBJECT")
    if string == "VERT":
        for v in idlist:
            mesh.vertices[v].select = True
    elif string == "EDGE":
        for e in idlist:
            mesh.edges[e].select = True
    elif string == "FACE":
        for p in idlist:
            mesh.polygons[p].select = True
    set_mode("EDIT")


def get_selection(string):
    active = bpy.context.active_object
    active.update_from_editmode()

    if string == "VERT":
        return [v.index for v in active.data.vertices if v.select]
    if string == "EDGE":
        return [e.index for e in active.data.edges if e.select]
    if string == "FACE":
        return [f.index for f in active.data.polygons if f.select]


def get_selection_history():
    mesh = bpy.context.object.data
    bm = bmesh.from_edit_mesh(mesh)
    vertlist = [elem.index for elem in bm.select_history if isinstance(elem, bmesh.types.BMVert)]
    return vertlist


def get_scene_scale():
    return bpy.context.scene.unit_settings.scale_length


def lerp(value1, value2, amount):
    if 0 <= amount <= 1:
        return (amount * value2) + ((1 - amount) * value1)


class ShortestPath():
    # "author": "G Bantle, Bagration, MACHIN3",
    # "source": "https://blenderartists.org/forum/showthread.php?58564-Path-Select-script(Update-20060307-Ported-to-C-now-in-CVS",

    # TODO: do edge support?

    def __init__(self, input=False, select=True, multiple=True, silent=True):
        # go out of edit mode to update the vertex indices, in case geometry has been edited
        # go back into edit(vert) mode to retrieve the bmesh selection history

        for mode in ["OBJECT", "EDIT", "VERT"]:
            set_mode(mode)

        self.mesh = bpy.context.object.data
        self.multiple = multiple
        self.input = input

        self.selection = self.get_selection()

        mg = self.build_mesh_graph()

        if self.multiple:
            path = []
            for pair in self.selection:
                path += self.dijkstra_algorithm(mg, pair[0], pair[1])
            self.path = self.f7(path)
        else:
            self.path = self.dijkstra_algorithm(mg, self.selection[0], self.selection[1])

        if not silent:
            print(self.selection)
            print(self.path)

        if select:
            make_selection("VERT", self.path)

    def f7(self, seq):  # removes duplicates, keeps order (https://stackoverflow.com/a/480227)
        seen = set()
        seen_add = seen.add
        return [x for x in seq if not (x in seen or seen_add(x))]

    def dijkstra_algorithm(self, Q, s, t):
        unknownverts = []  # [(shortest dist from s (start vert) to vert, vert)]
        infinity = sys.maxsize

        d = dict.fromkeys(Q.keys(), infinity)  # {vert: shortest dist from s to vert}
        predecessor = dict.fromkeys(Q.keys())  # {vert: predecessor in the shortest path to the vert}

        d[s] = 0
        unknownverts.append((0, s))  # The distance of the start vert to itself is 0

        while s != t:
            unknownverts.sort()
            dist, u = unknownverts[0]  # Get the next vert that is closest to s
            edges = Q[u]

            for v, w in edges:  # v = neighbour vert, w = distance from u to this vert
                if d[v] > d[u] + w:
                    d[v] = d[u] + w
                    unknownverts.append((d[v], v))
                    predecessor[v] = u

            unknownverts.pop(0)  # We just finished exploring this vert, so it can be removed
            s = u  # Set new start vert

        path = []
        endvert = t

        while endvert is not None:  # Backtrace rom the end vertex using the "predecessor" dict
            path.append(endvert)
            endvert = predecessor[endvert]

        return reversed(path)

    def build_mesh_graph(self):
        mesh_graph = {}
        for v in self.mesh.vertices:
            mesh_graph[v.index] = []

        for edge in self.mesh.edges:
            mesh_graph[edge.vertices[0]].append((edge.vertices[1], 1))
            mesh_graph[edge.vertices[1]].append((edge.vertices[0], 1))

        return mesh_graph

    def get_selection(self):
        if self.input is False:
            selection = get_selection_history()
        else:
            selection = self.input

        if self.multiple:
            selpairs = []
            for s in selection[1:]:
                selpairs.append([selection[selection.index(s) - 1], s])
            return selpairs
        else:
            return selection
