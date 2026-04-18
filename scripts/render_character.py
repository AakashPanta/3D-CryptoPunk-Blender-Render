import bpy
import math
import os
import sys
import traceback
from mathutils import Vector, Euler

# ============================================================
# ARGUMENTS
# ============================================================
def parse_args():
    argv = sys.argv
    output_dir = os.path.join(os.getcwd(), "output")
    reference_image = None
    style_glb = None

    if "--" in argv:
        args = argv[argv.index("--") + 1:]
        i = 0
        while i < len(args):
            if args[i] == "--output-dir" and i + 1 < len(args):
                output_dir = args[i + 1]
                i += 2
                continue
            if args[i] == "--reference-image" and i + 1 < len(args):
                reference_image = args[i + 1]
                i += 2
                continue
            if args[i] == "--style-glb" and i + 1 < len(args):
                style_glb = args[i + 1]
                i += 2
                continue
            i += 1

    return output_dir, reference_image, style_glb


OUTPUT_DIR, REFERENCE_IMAGE, STYLE_GLB = parse_args()
os.makedirs(OUTPUT_DIR, exist_ok=True)

OUTPUT_PNG = os.path.join(OUTPUT_DIR, "character_render.png")
OUTPUT_BLEND = os.path.join(OUTPUT_DIR, "character_scene.blend")
OUTPUT_GLB = os.path.join(OUTPUT_DIR, "character_scene.glb")

print("=" * 80)
print("Automated 3D character reconstruction render")
print("=" * 80)
print(f"OUTPUT_DIR      = {OUTPUT_DIR}")
print(f"REFERENCE_IMAGE = {REFERENCE_IMAGE}")
print(f"STYLE_GLB       = {STYLE_GLB}")
print(f"OUTPUT_PNG      = {OUTPUT_PNG}")
print(f"OUTPUT_BLEND    = {OUTPUT_BLEND}")
print(f"OUTPUT_GLB      = {OUTPUT_GLB}")

# ============================================================
# GLOBALS
# ============================================================
scene = bpy.context.scene
view_layer = bpy.context.view_layer
collection = bpy.context.collection
mat_cache = {}

# ============================================================
# RESET
# ============================================================
def clear_scene():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)

    datablocks = [
        bpy.data.meshes,
        bpy.data.materials,
        bpy.data.images,
        bpy.data.lights,
        bpy.data.cameras,
        bpy.data.curves,
        bpy.data.worlds,
    ]

    for blockset in datablocks:
        for block in list(blockset):
            try:
                blockset.remove(block)
            except Exception:
                pass


clear_scene()

# ============================================================
# HELPERS
# ============================================================
def set_active(obj):
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    view_layer.objects.active = obj


def apply_transforms(obj):
    set_active(obj)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)


def smooth(obj):
    set_active(obj)
    try:
        bpy.ops.object.shade_smooth()
    except Exception:
        pass


def add_subsurf(obj, levels=2, render_levels=2):
    mod = obj.modifiers.new("Subsurf", 'SUBSURF')
    mod.levels = levels
    mod.render_levels = render_levels
    return mod


def add_bevel(obj, width=0.01, segments=3):
    mod = obj.modifiers.new("Bevel", 'BEVEL')
    mod.width = width
    mod.segments = segments
    mod.limit_method = 'ANGLE'
    return mod


def add_solidify(obj, thickness=0.004):
    mod = obj.modifiers.new("Solidify", 'SOLIDIFY')
    mod.thickness = thickness
    return mod


def add_weighted_normal(obj):
    mod = obj.modifiers.new("WeightedNormal", 'WEIGHTED_NORMAL')
    mod.keep_sharp = True
    return mod


def assign_mat(obj, mat):
    if not obj.data:
        return
    if obj.data.materials:
        obj.data.materials[0] = mat
    else:
        obj.data.materials.append(mat)


def make_principled(
    name,
    base_color=(0.8, 0.8, 0.8, 1.0),
    roughness=0.5,
    metallic=0.0,
    specular=0.5,
    emission_color=None,
    emission_strength=0.0,
    alpha=1.0,
    transmission=0.0,
    subsurface=0.0,
):
    if name in mat_cache:
        return mat_cache[name]

    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    mat.blend_method = 'OPAQUE' if alpha >= 1.0 else 'BLEND'

    nt = mat.node_tree
    nodes = nt.nodes
    links = nt.links
    nodes.clear()

    out = nodes.new(type="ShaderNodeOutputMaterial")
    out.location = (600, 0)

    bsdf = nodes.new(type="ShaderNodeBsdfPrincipled")
    bsdf.location = (260, 0)
    bsdf.inputs["Base Color"].default_value = base_color
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic

    if "Specular IOR Level" in bsdf.inputs:
        bsdf.inputs["Specular IOR Level"].default_value = specular
    elif "Specular" in bsdf.inputs:
        bsdf.inputs["Specular"].default_value = specular

    if "Transmission Weight" in bsdf.inputs:
        bsdf.inputs["Transmission Weight"].default_value = transmission
    elif "Transmission" in bsdf.inputs:
        bsdf.inputs["Transmission"].default_value = transmission

    if "Subsurface Weight" in bsdf.inputs:
        bsdf.inputs["Subsurface Weight"].default_value = subsurface
    elif "Subsurface" in bsdf.inputs:
        bsdf.inputs["Subsurface"].default_value = subsurface

    if "Alpha" in bsdf.inputs:
        bsdf.inputs["Alpha"].default_value = alpha

    if emission_color is not None:
        if "Emission Color" in bsdf.inputs:
            bsdf.inputs["Emission Color"].default_value = emission_color
        elif "Emission" in bsdf.inputs:
            bsdf.inputs["Emission"].default_value = emission_color

    if "Emission Strength" in bsdf.inputs:
        bsdf.inputs["Emission Strength"].default_value = emission_strength

    links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    mat_cache[name] = mat
    return mat


def make_helmet_style_material(
    name,
    base_color=(0.26, 0.30, 0.34, 1.0),
    accent_color=(0.74, 0.28, 0.10, 1.0),
    edge_color=(0.62, 0.66, 0.70, 1.0),
    roughness=0.42,
    metallic=0.72,
):
    """
    Damaged hard-surface material language inspired by the uploaded helmet:
    - base color albedo
    - metallic/roughness breakup
    - edge wear
    - grime noise
    - subtle emissive traces
    """
    if name in mat_cache:
        return mat_cache[name]

    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True

    nt = mat.node_tree
    nodes = nt.nodes
    links = nt.links
    nodes.clear()

    out = nodes.new("ShaderNodeOutputMaterial")
    out.location = (1300, 0)

    bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.location = (1000, 0)
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness
    if "Specular IOR Level" in bsdf.inputs:
        bsdf.inputs["Specular IOR Level"].default_value = 0.45
    elif "Specular" in bsdf.inputs:
        bsdf.inputs["Specular"].default_value = 0.45

    texcoord = nodes.new("ShaderNodeTexCoord")
    texcoord.location = (-1200, 100)

    mapping = nodes.new("ShaderNodeMapping")
    mapping.location = (-980, 100)
    mapping.inputs["Scale"].default_value = (4.0, 4.0, 4.0)

    noise_large = nodes.new("ShaderNodeTexNoise")
    noise_large.location = (-760, 240)
    noise_large.inputs["Scale"].default_value = 3.2
    noise_large.inputs["Detail"].default_value = 8.0
    noise_large.inputs["Roughness"].default_value = 0.55

    noise_fine = nodes.new("ShaderNodeTexNoise")
    noise_fine.location = (-760, -20)
    noise_fine.inputs["Scale"].default_value = 24.0
    noise_fine.inputs["Detail"].default_value = 10.0
    noise_fine.inputs["Roughness"].default_value = 0.65

    voronoi = nodes.new("ShaderNodeTexVoronoi")
    voronoi.location = (-760, -260)
    voronoi.feature = 'DISTANCE_TO_EDGE'
    voronoi.inputs["Scale"].default_value = 12.0

    ramp_wear = nodes.new("ShaderNodeValToRGB")
    ramp_wear.location = (-500, -260)
    ramp_wear.color_ramp.elements[0].position = 0.25
    ramp_wear.color_ramp.elements[1].position = 0.55

    ramp_grime = nodes.new("ShaderNodeValToRGB")
    ramp_grime.location = (-500, 220)
    ramp_grime.color_ramp.elements[0].position = 0.34
    ramp_grime.color_ramp.elements[1].position = 0.78

    mix_base_grime = nodes.new("ShaderNodeMixRGB")
    mix_base_grime.location = (-120, 180)
    mix_base_grime.blend_type = 'MULTIPLY'
    mix_base_grime.inputs[0].default_value = 0.35
    mix_base_grime.inputs[1].default_value = base_color

    mix_edge = nodes.new("ShaderNodeMixRGB")
    mix_edge.location = (120, 40)
    mix_edge.blend_type = 'MIX'
    mix_edge.inputs[1].default_value = base_color
    mix_edge.inputs[2].default_value = edge_color

    mix_accent = nodes.new("ShaderNodeMixRGB")
    mix_accent.location = (360, -80)
    mix_accent.blend_type = 'MIX'
    mix_accent.inputs[1].default_value = base_color
    mix_accent.inputs[2].default_value = accent_color

    rough_mix = nodes.new("ShaderNodeMixRGB")
    rough_mix.location = (360, 240)
    rough_mix.blend_type = 'MIX'
    rough_mix.inputs[1].default_value = (roughness, roughness, roughness, 1.0)
    rough_mix.inputs[2].default_value = (min(roughness + 0.24, 1.0),) * 3 + (1.0,)

    bump = nodes.new("ShaderNodeBump")
    bump.location = (720, 240)
    bump.inputs["Strength"].default_value = 0.08
    bump.inputs["Distance"].default_value = 0.08

    emission_mix = nodes.new("ShaderNodeMixRGB")
    emission_mix.location = (720, -220)
    emission_mix.blend_type = 'MIX'
    emission_mix.inputs[1].default_value = (0.0, 0.0, 0.0, 1.0)
    emission_mix.inputs[2].default_value = (0.75, 0.24, 0.08, 1.0)

    links.new(texcoord.outputs["Object"], mapping.inputs["Vector"])
    links.new(mapping.outputs["Vector"], noise_large.inputs["Vector"])
    links.new(mapping.outputs["Vector"], noise_fine.inputs["Vector"])
    links.new(mapping.outputs["Vector"], voronoi.inputs["Vector"])

    links.new(noise_large.outputs["Fac"], ramp_grime.inputs["Fac"])
    links.new(voronoi.outputs["Distance"], ramp_wear.inputs["Fac"])

    links.new(ramp_grime.outputs["Color"], mix_base_grime.inputs[2])
    links.new(ramp_wear.outputs["Color"], mix_edge.inputs[0])
    links.new(mix_base_grime.outputs["Color"], mix_edge.inputs[1])

    links.new(noise_fine.outputs["Fac"], mix_accent.inputs[0])
    links.new(mix_edge.outputs["Color"], mix_accent.inputs[1])

    links.new(noise_large.outputs["Fac"], rough_mix.inputs[0])
    links.new(rough_mix.outputs["Color"], bsdf.inputs["Roughness"])
    links.new(noise_fine.outputs["Fac"], bump.inputs["Height"])
    links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])

    bsdf.inputs["Base Color"].default_value = base_color
    links.new(mix_accent.outputs["Color"], bsdf.inputs["Base Color"])

    if "Emission Color" in bsdf.inputs:
        links.new(ramp_wear.outputs["Color"], emission_mix.inputs[0])
        links.new(emission_mix.outputs["Color"], bsdf.inputs["Emission Color"])
    elif "Emission" in bsdf.inputs:
        links.new(ramp_wear.outputs["Color"], emission_mix.inputs[0])
        links.new(emission_mix.outputs["Color"], bsdf.inputs["Emission"])

    if "Emission Strength" in bsdf.inputs:
        bsdf.inputs["Emission Strength"].default_value = 0.18

    links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])

    mat_cache[name] = mat
    return mat


def sphere(name, loc, radius, scale=(1, 1, 1), mat=None, seg=32, rings=16):
    bpy.ops.mesh.primitive_uv_sphere_add(
        radius=radius,
        segments=seg,
        ring_count=rings,
        location=loc
    )
    obj = bpy.context.active_object
    obj.name = name
    obj.scale = scale
    apply_transforms(obj)
    if mat:
        assign_mat(obj, mat)
    smooth(obj)
    return obj


def cube(name, loc, scale=(1, 1, 1), rot=(0, 0, 0), mat=None):
    bpy.ops.mesh.primitive_cube_add(location=loc, rotation=rot)
    obj = bpy.context.active_object
    obj.name = name
    obj.scale = scale
    apply_transforms(obj)
    if mat:
        assign_mat(obj, mat)
    return obj


def cylinder(name, loc, radius, depth, rot=(0, 0, 0), scale=(1, 1, 1), mat=None, verts=32):
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=verts,
        radius=radius,
        depth=depth,
        location=loc,
        rotation=rot
    )
    obj = bpy.context.active_object
    obj.name = name
    obj.scale = scale
    apply_transforms(obj)
    if mat:
        assign_mat(obj, mat)
    smooth(obj)
    return obj


def torus(name, loc, major_radius, minor_radius, rot=(0, 0, 0), mat=None):
    bpy.ops.mesh.primitive_torus_add(
        major_radius=major_radius,
        minor_radius=minor_radius,
        location=loc,
        rotation=rot
    )
    obj = bpy.context.active_object
    obj.name = name
    if mat:
        assign_mat(obj, mat)
    smooth(obj)
    return obj


def curve_smoke(name, points, bevel_depth, mat):
    curve = bpy.data.curves.new(name=name, type='CURVE')
    curve.dimensions = '3D'
    curve.resolution_u = 18
    spline = curve.splines.new('BEZIER')
    spline.bezier_points.add(len(points) - 1)

    for i, p in enumerate(points):
        bp = spline.bezier_points[i]
        bp.co = Vector(p)
        bp.handle_left_type = 'AUTO'
        bp.handle_right_type = 'AUTO'

    curve.bevel_depth = bevel_depth
    curve.bevel_resolution = 4

    obj = bpy.data.objects.new(name, curve)
    collection.objects.link(obj)
    obj.data.materials.append(mat)
    return obj


def area_light(name, location, rotation, energy, size, color):
    data = bpy.data.lights.new(name=name, type='AREA')
    data.energy = energy
    data.shape = 'RECTANGLE'
    data.size = size
    data.size_y = size
    data.color = color
    obj = bpy.data.objects.new(name, data)
    collection.objects.link(obj)
    obj.location = location
    obj.rotation_euler = rotation
    return obj


def point_light(name, location, energy, color, radius):
    data = bpy.data.lights.new(name=name, type='POINT')
    data.energy = energy
    data.color = color
    data.shadow_soft_size = radius
    obj = bpy.data.objects.new(name, data)
    collection.objects.link(obj)
    obj.location = location
    return obj


def import_style_glb(style_glb_path):
    """
    Imports the uploaded GLB as a side reference object and extracts its first material
    so the render scene carries the same hard-surface damaged design language.
    """
    imported_objects = []

    if not style_glb_path:
        return imported_objects, None

    if not os.path.exists(style_glb_path):
        print(f"Style GLB not found: {style_glb_path}")
        return imported_objects, None

    before = set(bpy.data.objects)
    try:
        bpy.ops.import_scene.gltf(filepath=style_glb_path)
        after = set(bpy.data.objects)
        imported_objects = list(after - before)
        print(f"Imported style GLB objects: {len(imported_objects)}")
    except Exception as e:
        print(f"Style GLB import failed: {e}")
        return [], None

    style_material = None
    for obj in imported_objects:
        obj.name = f"StyleRef_{obj.name}"
        if obj.type == 'MESH' and obj.data and obj.data.materials and not style_material:
            style_material = obj.data.materials[0]

    # Move imported style object to side reference area
    for obj in imported_objects:
        if obj.type == 'MESH':
            obj.location.x += 2.7
            obj.location.y += 0.2
            obj.location.z += 0.6
            obj.scale *= 0.55

    return imported_objects, style_material


def build_mech_panels():
    """
    Extra design elements that borrow the damaged helmet language and inject it
    into the cap, collar, wrist, and lighter area so the scene reads in the same style family.
    """
    panel_mat = make_helmet_style_material(
        "M_HelmetStyle_Main",
        base_color=(0.24, 0.28, 0.32, 1.0),
        accent_color=(0.78, 0.30, 0.08, 1.0),
        edge_color=(0.74, 0.76, 0.80, 1.0),
        roughness=0.38,
        metallic=0.78,
    )

    dark_panel = make_helmet_style_material(
        "M_HelmetStyle_Dark",
        base_color=(0.10, 0.12, 0.15, 1.0),
        accent_color=(0.62, 0.18, 0.04, 1.0),
        edge_color=(0.54, 0.56, 0.60, 1.0),
        roughness=0.48,
        metallic=0.84,
    )

    orange_glow = make_principled(
        "M_HelmetGlow",
        base_color=(0.18, 0.07, 0.02, 1.0),
        roughness=0.10,
        metallic=0.10,
        emission_color=(0.95, 0.36, 0.08, 1.0),
        emission_strength=1.8,
    )

    # Cap armor side plates
    cap_plate_l = cube(
        "CapArmorL",
        (-0.33, -0.08, 2.06),
        scale=(0.12, 0.05, 0.11),
        rot=(math.radians(18), math.radians(-6), math.radians(8)),
        mat=panel_mat,
    )
    add_bevel(cap_plate_l, width=0.01, segments=2)
    add_weighted_normal(cap_plate_l)

    cap_plate_r = cube(
        "CapArmorR",
        (0.31, -0.09, 2.01),
        scale=(0.10, 0.04, 0.09),
        rot=(math.radians(18), math.radians(5), math.radians(-6)),
        mat=dark_panel,
    )
    add_bevel(cap_plate_r, width=0.008, segments=2)
    add_weighted_normal(cap_plate_r)

    # Jaw-side cheek armor hint
    cheek_l = cube(
        "CheekArmorL",
        (-0.23, -0.18, 1.70),
        scale=(0.06, 0.02, 0.12),
        rot=(math.radians(10), math.radians(18), math.radians(22)),
        mat=dark_panel,
    )
    add_bevel(cheek_l, width=0.004, segments=2)

    # Collar mechanical tags
    collar_plate_l = cube(
        "CollarPlateL",
        (-0.18, -0.22, 1.28),
        scale=(0.08, 0.02, 0.14),
        rot=(math.radians(-12), math.radians(10), math.radians(15)),
        mat=panel_mat,
    )
    add_bevel(collar_plate_l, width=0.005, segments=2)

    collar_plate_r = cube(
        "CollarPlateR",
        (0.18, -0.22, 1.23),
        scale=(0.07, 0.02, 0.12),
        rot=(math.radians(-10), math.radians(-10), math.radians(-12)),
        mat=dark_panel,
    )
    add_bevel(collar_plate_r, width=0.005, segments=2)

    # Wrist module
    wrist_module = cube(
        "WristModule",
        (0.60, -0.29, 0.70),
        scale=(0.06, 0.028, 0.05),
        rot=(math.radians(54), math.radians(8), math.radians(16)),
        mat=panel_mat,
    )
    add_bevel(wrist_module, width=0.006, segments=2)

    wrist_glow = cube(
        "WristGlow",
        (0.625, -0.31, 0.715),
        scale=(0.016, 0.004, 0.025),
        rot=(math.radians(54), math.radians(8), math.radians(16)),
        mat=orange_glow,
    )
    add_bevel(wrist_glow, width=0.002, segments=2)

    # Lighter body shell to match helmet style
    lighter_shell = cube(
        "LighterShell",
        (0.73, -0.42, 0.64),
        scale=(0.065, 0.032, 0.122),
        rot=(math.radians(2), math.radians(4), math.radians(8)),
        mat=panel_mat,
    )
    add_bevel(lighter_shell, width=0.008, segments=3)

    lighter_glow = cube(
        "LighterGlowPanel",
        (0.752, -0.435, 0.655),
        scale=(0.012, 0.004, 0.028),
        rot=(math.radians(2), math.radians(4), math.radians(8)),
        mat=orange_glow,
    )
    add_bevel(lighter_glow, width=0.002, segments=2)

# ============================================================
# MATERIALS
# ============================================================
M_SKIN = make_principled("M_Skin", (0.93, 0.77, 0.61, 1.0), roughness=0.46, specular=0.32, subsurface=0.16)
M_SKIN_DARK = make_principled("M_SkinDark", (0.70, 0.55, 0.44, 1.0), roughness=0.62, specular=0.18)
M_HAIR = make_principled("M_Hair", (0.10, 0.07, 0.05, 1.0), roughness=0.72)
M_BROW = make_principled("M_Brow", (0.07, 0.04, 0.03, 1.0), roughness=0.86)
M_EYE_WHITE = make_principled("M_EyeWhite", (0.97, 0.97, 0.96, 1.0), roughness=0.08, specular=0.85)
M_IRIS = make_principled("M_Iris", (0.39, 0.31, 0.14, 1.0), roughness=0.14, specular=0.70)
M_PUPIL = make_principled("M_Pupil", (0.02, 0.02, 0.02, 1.0), roughness=0.06)
M_SHINE = make_principled("M_Shine", (1.0, 1.0, 1.0, 1.0), roughness=0.0, emission_color=(1.0, 1.0, 1.0, 1.0), emission_strength=1.6)
M_LIP = make_principled("M_Lip", (0.80, 0.61, 0.55, 1.0), roughness=0.36, specular=0.32, subsurface=0.06)

M_CAP = make_principled("M_Cap", (0.06, 0.13, 0.47, 1.0), roughness=0.75, specular=0.20)
M_CAP_UNDER = make_principled("M_CapUnder", (0.03, 0.07, 0.23, 1.0), roughness=0.82)
M_CAP_LOGO = make_principled("M_CapLogo", (0.96, 0.96, 0.97, 1.0), roughness=0.18, specular=0.55)

M_GREEN = make_principled("M_Green", (0.53, 0.72, 0.27, 1.0), roughness=0.82, specular=0.22)
M_WHITE = make_principled("M_White", (0.94, 0.94, 0.93, 1.0), roughness=0.72)
M_DARK = make_principled("M_Dark", (0.08, 0.09, 0.11, 1.0), roughness=0.68)

M_EARRING = make_principled("M_Earring", (0.02, 0.02, 0.03, 1.0), roughness=0.12, metallic=0.90)
M_WRIST_BLUE = make_principled("M_WristBlue", (0.22, 0.38, 0.65, 1.0), roughness=0.42)
M_WRIST_WHITE = make_principled("M_WristWhite", (0.96, 0.97, 0.98, 1.0), roughness=0.34)

M_LIGHTER_RED = make_principled("M_LighterRed", (0.78, 0.05, 0.05, 1.0), roughness=0.22, specular=0.56)
M_CHROME = make_principled("M_Chrome", (0.76, 0.77, 0.80, 1.0), roughness=0.08, metallic=1.0)
M_FLAME = make_principled("M_Flame", (1.0, 0.72, 0.18, 1.0), roughness=0.0, emission_color=(1.0, 0.56, 0.08, 1.0), emission_strength=20.0)
M_FLAME_OUTER = make_principled("M_FlameOuter", (1.0, 0.82, 0.32, 1.0), roughness=0.0, emission_color=(1.0, 0.72, 0.16, 1.0), emission_strength=14.0, alpha=0.95)

M_CIG_WHITE = make_principled("M_CigWhite", (0.94, 0.94, 0.94, 1.0), roughness=0.55)
M_CIG_FILTER = make_principled("M_CigFilter", (0.77, 0.49, 0.19, 1.0), roughness=0.62)
M_CIG_EMBER = make_principled("M_CigEmber", (0.96, 0.38, 0.06, 1.0), roughness=0.0, emission_color=(1.0, 0.30, 0.02, 1.0), emission_strength=8.0)
M_SMOKE = make_principled("M_Smoke", (0.94, 0.94, 0.96, 1.0), roughness=0.18, alpha=0.14)

M_BG = make_principled("M_BG", (0.02, 0.03, 0.05, 1.0), roughness=0.96)
M_FLOOR = make_principled("M_Floor", (0.03, 0.03, 0.05, 1.0), roughness=0.16)

# ============================================================
# WORLD
# ============================================================
world = bpy.data.worlds.new("World")
scene.world = world
world.use_nodes = True
bg_node = world.node_tree.nodes.get("Background")
bg_node.inputs[0].default_value = (0.01, 0.01, 0.02, 1.0)
bg_node.inputs[1].default_value = 0.45

# ============================================================
# REFERENCE BOARD
# ============================================================
if REFERENCE_IMAGE and os.path.exists(REFERENCE_IMAGE):
    try:
        ref_img = bpy.data.images.load(REFERENCE_IMAGE)

        ref_mat = bpy.data.materials.new("M_Reference")
        ref_mat.use_nodes = True
        ref_mat.blend_method = 'BLEND'
        n = ref_mat.node_tree.nodes
        l = ref_mat.node_tree.links
        n.clear()

        out = n.new("ShaderNodeOutputMaterial")
        em = n.new("ShaderNodeEmission")
        tex = n.new("ShaderNodeTexImage")
        tex.image = ref_img

        l.new(tex.outputs["Color"], em.inputs["Color"])
        l.new(em.outputs["Emission"], out.inputs["Surface"])

        bpy.ops.mesh.primitive_plane_add(size=2.8, location=(3.2, 0.0, 1.8), rotation=(0, math.radians(90), 0))
        ref_plane = bpy.context.active_object
        ref_plane.name = "ReferencePlane"
        assign_mat(ref_plane, ref_mat)
    except Exception as e:
        print(f"Reference plane skipped: {e}")

# ============================================================
# IMPORT STYLE GLB
# ============================================================
STYLE_IMPORTED_OBJECTS, STYLE_IMPORTED_MATERIAL = import_style_glb(STYLE_GLB)

# ============================================================
# SUBJECT
# ============================================================
print("Building subject...")

head = sphere("Head", (0.0, 0.00, 1.73), 0.40, scale=(1.05, 0.88, 1.12), mat=M_SKIN, seg=64, rings=32)
add_subsurf(head, 2, 3)

jaw = sphere("Jaw", (0.0, -0.01, 1.64), 0.26, scale=(1.06, 0.78, 0.55), mat=M_SKIN, seg=32, rings=16)
chin_shadow = sphere("Stubble", (0.0, -0.31, 1.59), 0.10, scale=(1.18, 0.36, 0.48), mat=M_SKIN_DARK, seg=24, rings=12)

neck = cylinder("Neck", (0.0, -0.02, 1.28), 0.115, 0.24, rot=(math.radians(90), 0, 0), scale=(1.0, 0.82, 1.0), mat=M_SKIN, verts=24)

hair = sphere("Hair", (-0.03, 0.03, 1.83), 0.39, scale=(1.02, 0.91, 0.88), mat=M_HAIR, seg=48, rings=24)

ear_l = sphere("EarL", (-0.43, -0.02, 1.76), 0.072, scale=(0.42, 0.22, 0.75), mat=M_SKIN, seg=16, rings=8)
ear_r = sphere("EarR", (0.41, -0.04, 1.77), 0.065, scale=(0.34, 0.18, 0.62), mat=M_SKIN, seg=16, rings=8)
earring = torus("Earring", (-0.456, -0.07, 1.70), 0.022, 0.006, rot=(math.radians(90), 0.0, math.radians(12)), mat=M_EARRING)

def build_eye(side, x, y, z, brow_rot):
    sphere(f"EyeWhite_{side}", (x, y, z), 0.078, scale=(1.10, 0.42, 0.80), mat=M_EYE_WHITE, seg=32, rings=16)
    sphere(f"Iris_{side}", (x + (0.003 if x > 0 else -0.002), y - 0.045, z - 0.004), 0.038, scale=(1.0, 0.22, 1.0), mat=M_IRIS, seg=24, rings=12)
    sphere(f"Pupil_{side}", (x + (0.003 if x > 0 else -0.002), y - 0.052, z - 0.004), 0.020, scale=(1.0, 0.16, 1.0), mat=M_PUPIL, seg=16, rings=8)
    sphere(f"Shine1_{side}", (x - 0.013, y - 0.058, z + 0.016), 0.010, scale=(1.0, 0.12, 1.0), mat=M_SHINE, seg=12, rings=6)
    sphere(f"Shine2_{side}", (x + 0.014, y - 0.056, z - 0.010), 0.006, scale=(1.0, 0.10, 1.0), mat=M_SHINE, seg=10, rings=5)
    cube(f"Brow_{side}", (x + (0.012 if x > 0 else -0.012), y - 0.05, z + 0.13), scale=(0.105, 0.015, 0.022), rot=(math.radians(5), 0.0, math.radians(brow_rot)), mat=M_BROW)
    cube(f"Lash_{side}", (x + (0.015 if x > 0 else -0.015), y - 0.052, z + 0.060), scale=(0.088, 0.010, 0.010), rot=(math.radians(3), 0.0, math.radians(10 if x > 0 else -10)), mat=M_BROW)

build_eye("L", -0.128, -0.305, 1.82, -16)
build_eye("R", 0.145, -0.330, 1.80, 16)

nose_bridge = sphere("NoseBridge", (0.03, -0.355, 1.74), 0.022, scale=(0.55, 0.35, 0.90), mat=M_SKIN, seg=16, rings=8)
nose_tip = sphere("NoseTip", (0.05, -0.392, 1.71), 0.026, scale=(0.62, 0.42, 0.52), mat=M_SKIN, seg=16, rings=8)

lip_upper = sphere("LipUpper", (0.07, -0.368, 1.633), 0.040, scale=(1.10, 0.24, 0.34), mat=M_LIP, seg=18, rings=9)
lip_lower = sphere("LipLower", (0.068, -0.362, 1.609), 0.036, scale=(1.00, 0.26, 0.28), mat=M_LIP, seg=18, rings=9)

cap_dome = sphere("CapDome", (0.0, 0.0, 2.12), 0.43, scale=(1.04, 1.00, 0.72), mat=M_CAP, seg=48, rings=24)
cap_band = cube("CapBand", (0.0, -0.10, 1.96), scale=(0.44, 0.10, 0.07), rot=(math.radians(7), 0, 0), mat=M_CAP)
add_bevel(cap_band, width=0.01, segments=3)

bpy.ops.mesh.primitive_cylinder_add(vertices=64, radius=0.39, depth=0.05, location=(0.16, -0.35, 1.88), rotation=(math.radians(18), math.radians(2), math.radians(-2)))
cap_brim = bpy.context.active_object
cap_brim.name = "CapBrim"
cap_brim.scale = (1.12, 0.58, 1.0)
apply_transforms(cap_brim)
assign_mat(cap_brim, M_CAP)
smooth(cap_brim)

bpy.ops.mesh.primitive_cylinder_add(vertices=64, radius=0.375, depth=0.02, location=(0.16, -0.35, 1.865), rotation=(math.radians(18), math.radians(2), math.radians(-2)))
cap_under = bpy.context.active_object
cap_under.name = "CapUnder"
cap_under.scale = (1.12, 0.58, 1.0)
apply_transforms(cap_under)
assign_mat(cap_under, M_CAP_UNDER)
smooth(cap_under)

sphere("CapButton", (0.0, 0.02, 2.42), 0.018, mat=M_CAP, seg=10, rings=5)
logo_left = cube("LogoLeft", (-0.04, -0.377, 2.08), scale=(0.055, 0.012, 0.018), rot=(math.radians(8), math.radians(3), math.radians(38)), mat=M_CAP_LOGO)
logo_right = cube("LogoRight", (0.065, -0.382, 2.105), scale=(0.108, 0.012, 0.018), rot=(math.radians(8), math.radians(2), math.radians(-24)), mat=M_CAP_LOGO)
add_bevel(logo_left, width=0.004, segments=2)
add_bevel(logo_right, width=0.004, segments=2)

cylinder("Chest", (0.00, -0.02, 1.00), 0.26, 0.66, rot=(math.radians(90), 0, 0), scale=(1.0, 0.82, 1.0), mat=M_WHITE, verts=32)
cylinder("Shirt", (-0.01, -0.01, 1.02), 0.31, 0.62, rot=(math.radians(90), 0, 0), scale=(1.03, 0.84, 1.0), mat=M_GREEN, verts=32)

cube("ShirtL", (-0.16, -0.22, 1.05), scale=(0.12, 0.03, 0.31), rot=(math.radians(-8), 0, math.radians(4)), mat=M_GREEN)
cube("ShirtR", (0.12, -0.21, 1.03), scale=(0.10, 0.03, 0.29), rot=(math.radians(-8), 0, math.radians(-4)), mat=M_GREEN)
cube("CollarL", (-0.10, -0.27, 1.36), scale=(0.09, 0.018, 0.11), rot=(math.radians(-32), math.radians(4), math.radians(18)), mat=M_GREEN)
cube("CollarR", (0.10, -0.28, 1.34), scale=(0.08, 0.018, 0.10), rot=(math.radians(-28), math.radians(-4), math.radians(-14)), mat=M_GREEN)
cube("InnerBlack", (0.00, -0.18, 0.95), scale=(0.05, 0.018, 0.26), mat=M_DARK)

for i, z in enumerate([1.22, 1.08, 0.95]):
    sphere(f"Button_{i}", (-0.035, -0.300, z), 0.016, scale=(1.0, 0.35, 1.0), mat=M_WHITE, seg=12, rings=6)

sphere("ShoulderL", (-0.38, -0.02, 1.18), 0.14, scale=(0.9, 0.8, 0.8), mat=M_GREEN, seg=24, rings=12)
cylinder("UpperL", (-0.50, -0.02, 0.98), 0.085, 0.30, rot=(math.radians(10), 0, math.radians(20)), mat=M_GREEN, verts=20)
cylinder("ForeL", (-0.58, -0.04, 0.77), 0.065, 0.25, rot=(math.radians(12), 0, math.radians(18)), mat=M_SKIN, verts=20)
sphere("HandL", (-0.62, -0.07, 0.60), 0.07, scale=(0.8, 0.52, 0.75), mat=M_SKIN, seg=18, rings=9)

sphere("ShoulderR", (0.30, -0.04, 1.12), 0.14, scale=(0.95, 0.85, 0.82), mat=M_GREEN, seg=24, rings=12)
cylinder("UpperR", (0.42, -0.14, 0.99), 0.09, 0.28, rot=(math.radians(-28), 0, math.radians(-22)), mat=M_GREEN, verts=20)
cylinder("ForeR", (0.54, -0.28, 0.84), 0.072, 0.25, rot=(math.radians(-44), 0, math.radians(-18)), mat=M_SKIN, verts=20)

torus("WristBlue", (0.58, -0.31, 0.69), 0.082, 0.018, rot=(math.radians(58), 0, math.radians(14)), mat=M_WRIST_BLUE)
torus("WristWhite", (0.582, -0.31, 0.69), 0.065, 0.008, rot=(math.radians(58), 0, math.radians(14)), mat=M_WRIST_WHITE)

sphere("HandR", (0.67, -0.38, 0.63), 0.10, scale=(0.98, 0.70, 0.78), mat=M_SKIN, seg=24, rings=12)
cylinder("ThumbR", (0.62, -0.34, 0.62), 0.018, 0.08, rot=(math.radians(10), math.radians(72), math.radians(-10)), mat=M_SKIN, verts=12)

for i, (fx, fy, fz, rx) in enumerate([
    (0.714, -0.402, 0.67, -64),
    (0.722, -0.405, 0.63, -66),
    (0.720, -0.406, 0.59, -68),
    (0.714, -0.405, 0.55, -70),
]):
    cylinder(f"Finger_{i}", (fx, fy, fz), 0.014, 0.072, rot=(math.radians(rx), 0, math.radians(10)), mat=M_SKIN, verts=12)

lighter_body = cube("LighterBody", (0.73, -0.42, 0.64), scale=(0.06, 0.03, 0.115), rot=(math.radians(2), math.radians(4), math.radians(8)), mat=M_LIGHTER_RED)
add_bevel(lighter_body, width=0.008, segments=3)

lighter_top = cube("LighterTop", (0.733, -0.420, 0.760), scale=(0.05, 0.025, 0.028), rot=(math.radians(2), math.radians(4), math.radians(8)), mat=M_CHROME)
add_bevel(lighter_top, width=0.004, segments=2)

cylinder("LighterWheel", (0.720, -0.401, 0.776), 0.010, 0.020, rot=(math.radians(90), 0, math.radians(10)), mat=M_CHROME, verts=14)

sphere("FlameInner", (0.73, -0.43, 0.815), 0.018, scale=(0.45, 0.35, 1.35), mat=M_FLAME, seg=12, rings=6)
sphere("FlameOuter", (0.73, -0.43, 0.832), 0.024, scale=(0.55, 0.45, 1.45), mat=M_FLAME_OUTER, seg=12, rings=6)

cylinder("CigBody", (0.39, -0.386, 1.64), 0.018, 0.29, rot=(math.radians(86), math.radians(8), math.radians(4)), mat=M_CIG_WHITE, verts=24)
cylinder("CigFilter", (0.27, -0.375, 1.64), 0.0185, 0.075, rot=(math.radians(86), math.radians(8), math.radians(4)), mat=M_CIG_FILTER, verts=24)
cylinder("CigEmber", (0.52, -0.397, 1.64), 0.015, 0.020, rot=(math.radians(86), math.radians(8), math.radians(4)), mat=M_CIG_EMBER, verts=20)

curve_smoke("Smoke0", [(0.55, -0.39, 1.67), (0.67, -0.27, 1.74), (0.79, -0.22, 1.84), (0.90, -0.18, 1.98)], 0.014, M_SMOKE)
curve_smoke("Smoke1", [(0.57, -0.37, 1.65), (0.67, -0.30, 1.77), (0.76, -0.26, 1.92), (0.83, -0.18, 2.06)], 0.011, M_SMOKE)
curve_smoke("Smoke2", [(0.56, -0.40, 1.66), (0.62, -0.32, 1.79), (0.70, -0.24, 1.90), (0.77, -0.12, 2.00)], 0.009, M_SMOKE)

# Inject style-inspired hard-surface elements
build_mech_panels()

# If the imported GLB brought a usable material, place it onto one hero prop shell too
if STYLE_IMPORTED_MATERIAL:
    try:
        assign_mat(lighter_body, STYLE_IMPORTED_MATERIAL)
        print("Applied imported style material to lighter body.")
    except Exception as e:
        print(f"Imported style material application skipped: {e}")

# ============================================================
# ENVIRONMENT
# ============================================================
print("Building environment...")

bpy.ops.mesh.primitive_plane_add(size=14, location=(0, 3.6, 1.6), rotation=(math.radians(90), 0, 0))
bg_plane = bpy.context.active_object
bg_plane.name = "BGPlane"
assign_mat(bg_plane, M_BG)

bpy.ops.mesh.primitive_plane_add(size=12, location=(0, 0, 0))
floor = bpy.context.active_object
floor.name = "Floor"
assign_mat(floor, M_FLOOR)

def add_bokeh(idx, loc, color, strength, radius):
    m = make_principled(
        f"M_Bokeh_{idx}",
        base_color=(*color, 1.0),
        roughness=0.0,
        emission_color=(*color, 1.0),
        emission_strength=strength
    )
    sphere(f"Bokeh_{idx}", loc, radius, mat=m, seg=12, rings=6)

for i, spec in enumerate([
    ((-2.6, 3.2, 2.3), (1.00, 0.62, 0.25), 12.0, 0.22),
    ((-1.4, 3.9, 0.8), (0.98, 0.56, 0.20), 10.0, 0.18),
    ((1.8, 3.4, 2.8), (0.98, 0.58, 0.21), 12.0, 0.16),
    ((2.7, 3.0, 1.1), (1.00, 0.68, 0.25), 11.0, 0.20),
    ((-0.9, 4.2, 3.1), (0.40, 0.52, 0.95), 8.0, 0.10),
    ((0.9, 4.1, 0.9), (0.35, 0.44, 0.95), 8.0, 0.09),
    ((-2.9, 3.5, 1.3), (0.95, 0.73, 0.42), 9.0, 0.12),
]):
    add_bokeh(i, *spec)

# ============================================================
# LIGHTS
# ============================================================
print("Building lights...")

area_light("Key", (-1.2, -2.1, 2.5), (math.radians(62), math.radians(2), math.radians(20)), 4500, 2.3, (1.0, 0.88, 0.76))
area_light("Fill", (1.9, -1.7, 1.8), (math.radians(76), 0, math.radians(-34)), 1500, 2.8, (0.68, 0.76, 1.0))
area_light("Rim", (0.8, 1.6, 2.4), (math.radians(-108), 0, math.radians(12)), 2200, 1.8, (1.0, 0.74, 0.45))
point_light("FlameLight", (0.73, -0.43, 0.82), 350, (1.0, 0.45, 0.10), 0.06)
point_light("EmberLight", (0.53, -0.39, 1.65), 120, (1.0, 0.28, 0.05), 0.04)

# ============================================================
# CAMERA
# ============================================================
print("Setting camera...")

cam_data = bpy.data.cameras.new("Camera")
cam = bpy.data.objects.new("Camera", cam_data)
collection.objects.link(cam)
scene.camera = cam

cam.location = (-0.85, -3.55, 1.74)
cam.rotation_euler = Euler((math.radians(86.4), 0.0, math.radians(-17.0)), 'XYZ')
cam.data.lens = 85
cam.data.sensor_width = 36
cam.data.dof.use_dof = True
cam.data.dof.aperture_fstop = 1.8
cam.data.dof.focus_distance = 3.1

# ============================================================
# RENDER
# ============================================================
print("Setting render...")

scene.render.engine = 'CYCLES'
scene.cycles.device = 'CPU'
scene.cycles.samples = 128
scene.cycles.preview_samples = 24
scene.cycles.use_adaptive_sampling = True
scene.cycles.max_bounces = 6
scene.cycles.diffuse_bounces = 2
scene.cycles.glossy_bounces = 3
scene.cycles.transparent_max_bounces = 4

scene.render.resolution_x = 1280
scene.render.resolution_y = 1280
scene.render.resolution_percentage = 100
scene.render.film_transparent = False
scene.render.image_settings.file_format = 'PNG'
scene.render.image_settings.color_mode = 'RGBA'
scene.render.filepath = OUTPUT_PNG

try:
    scene.view_settings.look = 'None'
except Exception:
    pass
scene.view_settings.exposure = 0.15
scene.view_settings.gamma = 1.0

# ============================================================
# COMPOSITOR
# ============================================================
print("Setting compositor...")

def setup_compositor(scene_obj):
    scene_obj.use_nodes = True
    tree = scene_obj.node_tree
    nodes = tree.nodes
    links = tree.links
    nodes.clear()

    rl = nodes.new(type="CompositorNodeRLayers")
    rl.location = (-500, 0)

    last_out = rl.outputs["Image"]

    try:
        glare = nodes.new(type="CompositorNodeGlare")
        glare.location = (-220, 0)
        glare.glare_type = 'FOG_GLOW'
        glare.quality = 'HIGH'
        glare.threshold = 0.78
        glare.size = 7
        links.new(last_out, glare.inputs["Image"])
        last_out = glare.outputs["Image"]
        print("Glare: OK")
    except Exception as e:
        print(f"Glare skipped: {e}")

    try:
        lens = nodes.new(type="CompositorNodeLensdist")
        lens.location = (20, 0)
        try:
            lens.inputs[1].default_value = -0.008
            lens.inputs[2].default_value = 0.002
        except Exception:
            pass
        links.new(last_out, lens.inputs["Image"])
        last_out = lens.outputs["Image"]
        print("Lens distortion: OK")
    except Exception as e:
        print(f"Lens distortion skipped: {e}")

    try:
        cb = nodes.new(type="CompositorNodeColorBalance")
        cb.location = (260, 0)
        cb.correction_method = 'LIFT_GAMMA_GAIN'
        cb.lift = (0.98, 0.99, 1.02)
        cb.gamma = (1.02, 1.00, 0.98)
        cb.gain = (1.04, 1.02, 0.98)
        links.new(last_out, cb.inputs["Image"])
        last_out = cb.outputs["Image"]
        print("Color balance: OK")
    except Exception as e:
        print(f"Color balance skipped: {e}")

    try:
        ellipse = nodes.new(type="CompositorNodeEllipseMask")
        ellipse.location = (260, -260)
        ellipse.width = 0.88
        ellipse.height = 0.84

        blur = nodes.new(type="CompositorNodeBlur")
        blur.location = (460, -260)
        blur.size_x = 160
        blur.size_y = 160
        links.new(ellipse.outputs["Mask"], blur.inputs["Image"])

        mix = nodes.new(type="CompositorNodeMixRGB")
        mix.location = (520, 0)
        mix.blend_type = 'MULTIPLY'
        mix.inputs[0].default_value = 0.34
        links.new(last_out, mix.inputs[1])
        links.new(blur.outputs["Image"], mix.inputs[2])
        last_out = mix.outputs["Image"]
        print("Vignette: OK")
    except Exception as e:
        print(f"Vignette skipped: {e}")

    comp = nodes.new(type="CompositorNodeComposite")
    comp.location = (760, 0)
    links.new(last_out, comp.inputs["Image"])

    try:
        viewer = nodes.new(type="CompositorNodeViewer")
        viewer.location = (760, -140)
        links.new(last_out, viewer.inputs["Image"])
    except Exception:
        pass


setup_compositor(scene)

# ============================================================
# SAVE / EXPORT
# ============================================================
def save_outputs():
    print("Rendering still...")
    bpy.ops.render.render(write_still=True)
    print("PNG render complete.")

    print("Saving blend...")
    bpy.ops.wm.save_as_mainfile(filepath=OUTPUT_BLEND)
    print("BLEND saved.")

    print("Exporting GLB...")
    try:
        bpy.ops.export_scene.gltf(
            filepath=OUTPUT_GLB,
            export_format='GLB',
            use_selection=False
        )
        print("GLB exported.")
    except Exception as e:
        print(f"GLB export skipped: {e}")

    print(f"PNG exists   = {os.path.exists(OUTPUT_PNG)}")
    print(f"BLEND exists = {os.path.exists(OUTPUT_BLEND)}")
    print(f"GLB exists   = {os.path.exists(OUTPUT_GLB)}")


try:
    save_outputs()
    if not os.path.exists(OUTPUT_PNG):
        raise RuntimeError("PNG output missing")
    print("Pipeline complete.")
except Exception as e:
    print("FATAL ERROR")
    print(str(e))
    traceback.print_exc()
    raise
