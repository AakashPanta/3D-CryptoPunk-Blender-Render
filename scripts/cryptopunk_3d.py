"""
Premium CryptoPunk 3D Character — Blender Python Script
Stylized cinematic portrait recreation
Full scene: character + lighting + camera + render settings
Compatible: Blender 3.6 LTS
"""

import bpy
import math
import os
import sys

# ============================================================
# PARSE OUTPUT ARGS
# ============================================================
argv = sys.argv
output_dir = os.path.join(os.getcwd(), "output")

if "--" in argv:
    args = argv[argv.index("--") + 1:]
    for i, a in enumerate(args):
        if a == "--output-dir" and i + 1 < len(args):
            output_dir = args[i + 1]

os.makedirs(output_dir, exist_ok=True)
OUTPUT_PNG   = os.path.join(output_dir, "cryptopunk_character_render.png")
OUTPUT_BLEND = os.path.join(output_dir, "cryptopunk_character.blend")
OUTPUT_GLB   = os.path.join(output_dir, "cryptopunk_character.glb")
OUTPUT_USDZ  = os.path.join(output_dir, "cryptopunk_character.usdz")

print("=" * 60)
print("  Premium CryptoPunk Character — Blender Pipeline")
print(f"  PNG:   {OUTPUT_PNG}")
print(f"  Blend: {OUTPUT_BLEND}")
print(f"  USDZ:  {OUTPUT_USDZ}")
print(f"  GLB:   {OUTPUT_GLB}")
print("=" * 60)

# ============================================================
# CLEAN SCENE
# ============================================================
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
for bt in [bpy.data.materials, bpy.data.meshes,
           bpy.data.cameras, bpy.data.lights, bpy.data.curves]:
    for b in list(bt):
        bt.remove(b)

print("Scene cleaned")

# ============================================================
# MATERIAL LIBRARY
# ============================================================
mat_cache = {}

def make_mat(name, base_color,
             metallic=0.0, roughness=0.5,
             emission_color=None, emission_strength=0.0,
             subsurface=0.0, subsurface_color=None,
             transmission=0.0, ior=1.45,
             alpha=1.0):
    if name in mat_cache:
        return mat_cache[name]

    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    mat.blend_method = 'OPAQUE' if alpha >= 1.0 else 'BLEND'
    nt    = mat.node_tree
    nodes = nt.nodes
    links = nt.links

    for n in list(nodes):
        nodes.remove(n)

    out  = nodes.new('ShaderNodeOutputMaterial')
    out.location = (600, 0)
    bsdf = nodes.new('ShaderNodeBsdfPrincipled')
    bsdf.location = (200, 0)

    bsdf.inputs['Base Color'].default_value = (*base_color, 1.0)
    bsdf.inputs['Metallic'].default_value   = metallic
    bsdf.inputs['Roughness'].default_value  = roughness

    try:
        bsdf.inputs['IOR'].default_value = ior
    except KeyError:
        pass

    if alpha < 1.0:
        try:
            bsdf.inputs['Alpha'].default_value = alpha
        except KeyError:
            pass

    if transmission > 0:
        for k in ['Transmission Weight', 'Transmission']:
            if k in bsdf.inputs:
                try:
                    bsdf.inputs[k].default_value = transmission
                except Exception:
                    pass
                break

    if subsurface > 0:
        for k in ['Subsurface Weight', 'Subsurface']:
            if k in bsdf.inputs:
                try:
                    bsdf.inputs[k].default_value = subsurface
                except Exception:
                    pass
                break
        if subsurface_color:
            for k in ['Subsurface Color']:
                if k in bsdf.inputs:
                    try:
                        bsdf.inputs[k].default_value = (*subsurface_color, 1.0)
                    except Exception:
                        pass

    if emission_strength > 0 and emission_color:
        for k in ['Emission Color', 'Emission']:
            if k in bsdf.inputs:
                try:
                    bsdf.inputs[k].default_value = (*emission_color, 1.0)
                except Exception:
                    pass
                break
        for k in ['Emission Strength']:
            if k in bsdf.inputs:
                try:
                    bsdf.inputs[k].default_value = emission_strength
                except Exception:
                    pass

    links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])
    mat_cache[name] = mat
    return mat


# ── All character materials ──────────────────────────────────

M_SKIN = make_mat('Skin',
    base_color=(0.91, 0.73, 0.56), roughness=0.55,
    subsurface=0.35, subsurface_color=(0.95, 0.60, 0.45))

M_SKIN_DARK = make_mat('SkinDark',
    base_color=(0.78, 0.60, 0.44), roughness=0.6,
    subsurface=0.2, subsurface_color=(0.85, 0.50, 0.35))

M_EYE_SCLERA = make_mat('EyeSclera',
    base_color=(0.95, 0.94, 0.92), roughness=0.15,
    subsurface=0.1, subsurface_color=(0.95, 0.90, 0.88))

M_EYE_IRIS = make_mat('EyeIris',
    base_color=(0.28, 0.24, 0.10), roughness=0.05)

M_EYE_PUPIL = make_mat('EyePupil',
    base_color=(0.01, 0.01, 0.01), roughness=0.05)

M_EYE_CORNEA = make_mat('EyeCornea',
    base_color=(0.95, 0.95, 0.98), roughness=0.0,
    transmission=0.95, ior=1.38, alpha=0.1)

M_BROW = make_mat('Eyebrow',
    base_color=(0.08, 0.06, 0.04), roughness=0.8)

M_LIP = make_mat('Lips',
    base_color=(0.82, 0.58, 0.48), roughness=0.5,
    subsurface=0.2, subsurface_color=(0.90, 0.55, 0.45))

M_CAP_NAVY = make_mat('CapNavy',
    base_color=(0.08, 0.12, 0.38), roughness=0.75)

M_CAP_BRIM = make_mat('CapBrim',
    base_color=(0.05, 0.08, 0.28), roughness=0.7)

M_CHECK = make_mat('Checkmark',
    base_color=(0.95, 0.95, 0.97), roughness=0.25,
    emission_color=(0.95, 0.95, 0.97), emission_strength=0.5)

M_HAIR = make_mat('Hair',
    base_color=(0.06, 0.04, 0.03), roughness=0.65)

M_SHIRT_GREEN = make_mat('ShirtGreen',
    base_color=(0.28, 0.60, 0.08), roughness=0.7)

M_SHIRT_WHITE = make_mat('ShirtWhite',
    base_color=(0.88, 0.88, 0.86), roughness=0.65)

M_EARRING = make_mat('Earring',
    base_color=(0.02, 0.02, 0.02), roughness=0.2, metallic=0.8)

M_WRISTBAND = make_mat('Wristband',
    base_color=(0.15, 0.35, 0.75), roughness=0.6)

M_WRISTBAND_WHITE = make_mat('WristbandWhite',
    base_color=(0.88, 0.88, 0.90), roughness=0.55)

M_CIG_PAPER = make_mat('CigPaper',
    base_color=(0.90, 0.88, 0.82), roughness=0.75)

M_CIG_TIP = make_mat('CigTip',
    base_color=(0.95, 0.40, 0.05), roughness=0.4,
    emission_color=(1.0, 0.50, 0.05), emission_strength=4.0)

M_LIGHTER_RED = make_mat('LighterRed',
    base_color=(0.80, 0.05, 0.05), roughness=0.2)

M_LIGHTER_CHROME = make_mat('LighterChrome',
    base_color=(0.75, 0.75, 0.78), roughness=0.12, metallic=0.95)

M_FLAME = make_mat('Flame',
    base_color=(1.0, 0.65, 0.08), roughness=0.0,
    emission_color=(1.0, 0.55, 0.05), emission_strength=20.0)

M_SMOKE = make_mat('Smoke',
    base_color=(0.75, 0.75, 0.78), roughness=0.95, alpha=0.35)

M_BG = make_mat('Background',
    base_color=(0.02, 0.02, 0.04), roughness=0.9)

print(f"Created {len(mat_cache)} materials")

# ============================================================
# HELPER FUNCTIONS
# ============================================================

def assign_mat(obj, mat):
    if mat:
        if obj.data.materials:
            obj.data.materials[0] = mat
        else:
            obj.data.materials.append(mat)

def smooth_shade(obj):
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.shade_smooth()

def add_subsurf(obj, levels=2, render_levels=3):
    mod = obj.modifiers.new("Subsurf", 'SUBSURF')
    mod.levels        = levels
    mod.render_levels = render_levels
    return mod

def add_bevel(obj, width=0.02, segments=3):
    mod = obj.modifiers.new("Bevel", 'BEVEL')
    mod.width        = width
    mod.segments     = segments
    mod.limit_method = 'ANGLE'
    return mod

def add_sphere(name, mat, location, radius=1.0, segments=32, rings=16):
    bpy.ops.mesh.primitive_uv_sphere_add(
        radius=radius, segments=segments,
        ring_count=rings, location=location)
    obj = bpy.context.active_object
    obj.name = name
    assign_mat(obj, mat)
    smooth_shade(obj)
    return obj

def add_cube(name, mat, location, scale=(1,1,1), rotation=(0,0,0)):
    bpy.ops.mesh.primitive_cube_add(location=location)
    obj = bpy.context.active_object
    obj.name           = name
    obj.scale          = scale
    obj.rotation_euler = rotation
    assign_mat(obj, mat)
    return obj

def add_cylinder(name, mat, location, radius=1.0, depth=1.0,
                 rotation=(0,0,0), scale=(1,1,1), verts=32):
    bpy.ops.mesh.primitive_cylinder_add(
        radius=radius, depth=depth,
        vertices=verts, location=location)
    obj = bpy.context.active_object
    obj.name           = name
    obj.rotation_euler = rotation
    obj.scale          = scale
    assign_mat(obj, mat)
    smooth_shade(obj)
    return obj

# ============================================================
# BUILD CHARACTER
# ============================================================
print("Building character...")

# ── HEAD ─────────────────────────────────────────────────────
head = add_sphere('Head', M_SKIN, location=(0, 0, 1.75),
                  radius=0.38, segments=64, rings=32)
head.scale = (1.0, 0.88, 1.08)
add_subsurf(head, levels=2, render_levels=3)

neck = add_cylinder('Neck', M_SKIN, location=(0, 0.02, 1.32),
                    radius=0.12, depth=0.22, verts=24)
add_subsurf(neck, levels=1, render_levels=2)

# ── EYES ─────────────────────────────────────────────────────
eye_l_white = add_sphere('EyeL_Sclera', M_EYE_SCLERA,
                          location=(-0.13, -0.30, 1.82),
                          radius=0.065, segments=32, rings=16)
eye_l_white.scale = (1.0, 0.85, 0.75)

eye_l_iris = add_sphere('EyeL_Iris', M_EYE_IRIS,
                         location=(-0.13, -0.355, 1.82),
                         radius=0.042, segments=24, rings=12)
eye_l_iris.scale = (1.0, 0.3, 0.85)

eye_l_pupil = add_sphere('EyeL_Pupil', M_EYE_PUPIL,
                          location=(-0.13, -0.365, 1.82),
                          radius=0.025, segments=16, rings=8)
eye_l_pupil.scale = (1.0, 0.2, 0.8)

eye_r_white = add_sphere('EyeR_Sclera', M_EYE_SCLERA,
                          location=(0.13, -0.30, 1.82),
                          radius=0.065, segments=32, rings=16)
eye_r_white.scale = (1.0, 0.85, 0.75)

eye_r_iris = add_sphere('EyeR_Iris', M_EYE_IRIS,
                         location=(0.13, -0.355, 1.82),
                         radius=0.042, segments=24, rings=12)
eye_r_iris.scale = (1.0, 0.3, 0.85)

eye_r_pupil = add_sphere('EyeR_Pupil', M_EYE_PUPIL,
                          location=(0.13, -0.365, 1.82),
                          radius=0.025, segments=16, rings=8)
eye_r_pupil.scale = (1.0, 0.2, 0.8)

# ── EYEBROWS ─────────────────────────────────────────────────
brow_l = add_cube('BrowL', M_BROW,
                   location=(-0.13, -0.355, 1.895),
                   scale=(0.075, 0.012, 0.018),
                   rotation=(0, math.radians(-8), math.radians(-12)))

brow_r = add_cube('BrowR', M_BROW,
                   location=(0.13, -0.355, 1.895),
                   scale=(0.075, 0.012, 0.018),
                   rotation=(0, math.radians(8), math.radians(12)))

# ── NOSE ─────────────────────────────────────────────────────
nose = add_sphere('Nose', M_SKIN,
                   location=(0, -0.375, 1.73),
                   radius=0.035, segments=16, rings=8)
nose.scale = (0.7, 0.6, 0.5)

# ── LIPS ─────────────────────────────────────────────────────
lip_upper = add_sphere('LipUpper', M_LIP,
                        location=(0, -0.37, 1.66),
                        radius=0.055, segments=16, rings=8)
lip_upper.scale = (1.2, 0.4, 0.4)

lip_lower = add_sphere('LipLower', M_LIP,
                        location=(0, -0.365, 1.635),
                        radius=0.052, segments=16, rings=8)
lip_lower.scale = (1.1, 0.45, 0.35)

# ── EARS ─────────────────────────────────────────────────────
ear_l = add_sphere('EarL', M_SKIN,
                    location=(-0.375, 0.02, 1.76),
                    radius=0.07, segments=16, rings=8)
ear_l.scale = (0.4, 0.25, 0.65)

ear_r = add_sphere('EarR', M_SKIN,
                    location=(0.375, 0.02, 1.76),
                    radius=0.07, segments=16, rings=8)
ear_r.scale = (0.4, 0.25, 0.65)

earring = add_sphere('Earring', M_EARRING,
                      location=(-0.395, 0.02, 1.73),
                      radius=0.018, segments=12, rings=6)

# ── CAP ──────────────────────────────────────────────────────
cap_dome = add_sphere('CapDome', M_CAP_NAVY,
                       location=(0, 0.04, 2.02),
                       radius=0.40, segments=48, rings=24)
cap_dome.scale = (1.02, 0.96, 0.72)
add_subsurf(cap_dome, levels=2, render_levels=2)

bpy.ops.mesh.primitive_cylinder_add(
    radius=0.38, depth=0.04, vertices=48,
    location=(0, -0.18, 1.88))
brim = bpy.context.active_object
brim.name = "CapBrim"
brim.scale = (1.0, 0.55, 1.0)
brim.rotation_euler = (math.radians(15), 0, 0)
assign_mat(brim, M_CAP_BRIM)
smooth_shade(brim)

check_l = add_cube('CheckL', M_CHECK,
                    location=(-0.06, -0.37, 2.02),
                    scale=(0.055, 0.008, 0.022),
                    rotation=(math.radians(10), 0, math.radians(35)))

check_r = add_cube('CheckR', M_CHECK,
                    location=(0.04, -0.375, 2.05),
                    scale=(0.08, 0.008, 0.018),
                    rotation=(math.radians(10), 0, math.radians(-20)))

# ── HAIR ─────────────────────────────────────────────────────
hair_base = add_sphere('HairBase', M_HAIR,
                        location=(0, 0.05, 1.78),
                        radius=0.385, segments=32, rings=16)
hair_base.scale = (1.01, 0.90, 1.0)

# ── TORSO ────────────────────────────────────────────────────
bpy.ops.mesh.primitive_cylinder_add(
    radius=0.32, depth=0.65, vertices=32,
    location=(0, 0.04, 1.0))
torso = bpy.context.active_object
torso.name = "Torso"
torso.scale = (1.0, 0.82, 1.0)
assign_mat(torso, M_SHIRT_WHITE)
smooth_shade(torso)
add_subsurf(torso, levels=1, render_levels=2)

bpy.ops.mesh.primitive_cylinder_add(
    radius=0.34, depth=0.60, vertices=32,
    location=(0, 0.05, 1.02))
shirt = bpy.context.active_object
shirt.name = "GreenShirt"
shirt.scale = (1.02, 0.84, 1.0)
assign_mat(shirt, M_SHIRT_GREEN)
smooth_shade(shirt)
add_subsurf(shirt, levels=1, render_levels=2)

collar_l = add_cube('CollarL', M_SHIRT_GREEN,
                     location=(-0.10, -0.28, 1.38),
                     scale=(0.08, 0.02, 0.12),
                     rotation=(math.radians(-25), 0, math.radians(15)))

collar_r = add_cube('CollarR', M_SHIRT_GREEN,
                     location=(0.10, -0.28, 1.38),
                     scale=(0.08, 0.02, 0.12),
                     rotation=(math.radians(-25), 0, math.radians(-15)))

for i, bz in enumerate([1.18, 1.08, 0.98]):
    add_sphere(f'Button_{i}', M_SHIRT_WHITE,
               location=(0, -0.335, bz),
               radius=0.012, segments=8, rings=4)

# ── SHOULDERS & ARMS ─────────────────────────────────────────
l_shoulder = add_sphere('ShoulderL', M_SHIRT_GREEN,
                          location=(-0.38, 0.02, 1.22),
                          radius=0.16, segments=24, rings=12)
l_shoulder.scale = (0.85, 0.75, 0.8)

l_upper_arm = add_cylinder('UpperArmL', M_SHIRT_GREEN,
                             location=(-0.42, 0.02, 1.05),
                             radius=0.10, depth=0.28,
                             rotation=(math.radians(5), 0, math.radians(12)))

l_forearm = add_cylinder('ForearmL', M_SKIN,
                          location=(-0.44, 0.0, 0.82),
                          radius=0.075, depth=0.26,
                          rotation=(math.radians(8), 0, math.radians(10)))
add_subsurf(l_forearm, levels=1, render_levels=2)

r_shoulder = add_sphere('ShoulderR', M_SHIRT_GREEN,
                          location=(0.38, 0.02, 1.22),
                          radius=0.16, segments=24, rings=12)
r_shoulder.scale = (0.85, 0.75, 0.8)

r_upper_arm = add_cylinder('UpperArmR', M_SHIRT_GREEN,
                             location=(0.40, -0.05, 1.08),
                             radius=0.10, depth=0.28,
                             rotation=(math.radians(-20), 0, math.radians(-15)))

r_forearm = add_cylinder('ForearmR', M_SKIN,
                          location=(0.38, -0.12, 0.88),
                          radius=0.072, depth=0.24,
                          rotation=(math.radians(-35), 0, math.radians(-12)))
add_subsurf(r_forearm, levels=1, render_levels=2)

# ── WRISTBAND ────────────────────────────────────────────────
wrist_band = add_cylinder('WristbandMain', M_WRISTBAND,
                           location=(0.36, -0.20, 0.76),
                           radius=0.082, depth=0.055,
                           rotation=(math.radians(-35), 0, math.radians(-12)))

wrist_stripe = add_cylinder('WristbandStripe', M_WRISTBAND_WHITE,
                              location=(0.36, -0.20, 0.77),
                              radius=0.083, depth=0.018,
                              rotation=(math.radians(-35), 0, math.radians(-12)))

# ── HANDS ────────────────────────────────────────────────────
r_hand = add_sphere('HandR', M_SKIN,
                     location=(0.34, -0.28, 0.68),
                     radius=0.085, segments=24, rings=12)
r_hand.scale = (0.9, 0.65, 0.75)
add_subsurf(r_hand, levels=1, render_levels=2)

for i, (fx, fz) in enumerate([
    (-0.04, 0.04), (-0.01, 0.05), (0.02, 0.04), (0.05, 0.03)
]):
    add_cylinder(f'FingerR_{i}', M_SKIN,
                 location=(0.34 + fx, -0.30, 0.64 + fz),
                 radius=0.018, depth=0.06,
                 rotation=(math.radians(-60), 0, 0))

l_hand = add_sphere('HandL', M_SKIN,
                     location=(-0.08, -0.36, 1.64),
                     radius=0.06, segments=16, rings=8)
l_hand.scale = (0.5, 0.4, 0.35)

# ── LIGHTER ──────────────────────────────────────────────────
lighter_body = add_cube('LighterBody', M_LIGHTER_RED,
                          location=(0.34, -0.32, 0.60),
                          scale=(0.038, 0.022, 0.075))
add_bevel(lighter_body, width=0.008, segments=3)

lighter_top = add_cube('LighterTop', M_LIGHTER_CHROME,
                         location=(0.34, -0.32, 0.678),
                         scale=(0.036, 0.020, 0.022))
add_bevel(lighter_top, width=0.005, segments=2)

flame = add_sphere('Flame', M_FLAME,
                    location=(0.34, -0.32, 0.72),
                    radius=0.022, segments=12, rings=6)
flame.scale = (0.6, 0.5, 1.4)

# ── CIGARETTE ────────────────────────────────────────────────
cig = add_cylinder('Cigarette', M_CIG_PAPER,
                    location=(-0.04, -0.375, 1.645),
                    radius=0.008, depth=0.12,
                    rotation=(0, math.radians(85), math.radians(15)))

cig_tip = add_sphere('CigTip', M_CIG_TIP,
                      location=(0.04, -0.375, 1.648),
                      radius=0.010, segments=8, rings=4)

# ── SMOKE ────────────────────────────────────────────────────
smoke_positions = [
    (0.08, -0.37, 1.68, 0.022),
    (0.12, -0.36, 1.72, 0.030),
    (0.16, -0.35, 1.78, 0.038),
    (0.14, -0.34, 1.85, 0.045),
    (0.18, -0.33, 1.92, 0.035),
    (0.22, -0.32, 1.98, 0.028),
]
for i, (sx, sy, sz, sr) in enumerate(smoke_positions):
    s = add_sphere(f'Smoke_{i}', M_SMOKE,
                   location=(sx, sy, sz),
                   radius=sr, segments=8, rings=4)
    s.scale = (1.0 + i*0.1, 0.6, 1.2 + i*0.08)

print("Character built")

# ============================================================
# BACKGROUND ENVIRONMENT
# ============================================================
print("Building environment...")

bpy.ops.mesh.primitive_plane_add(
    size=12, location=(0, 4.5, 1.5),
    rotation=(math.radians(90), 0, 0))
bg = bpy.context.active_object
bg.name = "Background"
assign_mat(bg, M_BG)

bpy.ops.mesh.primitive_plane_add(size=12, location=(0, 0, 0.0))
floor = bpy.context.active_object
floor.name = "Floor"
mat_floor = make_mat('Floor', (0.02, 0.02, 0.03),
                     roughness=0.2, metallic=0.0)
assign_mat(floor, mat_floor)

bokeh_positions = [
    (-1.5, 3.5, 2.8, (1.0, 0.75, 0.35), 0.12),
    ( 1.8, 4.0, 2.2, (1.0, 0.80, 0.40), 0.10),
    (-0.8, 4.5, 3.5, (0.85, 0.65, 0.30), 0.08),
    ( 2.5, 3.8, 1.8, (1.0, 0.70, 0.30), 0.15),
    (-2.2, 4.2, 1.5, (0.90, 0.80, 0.45), 0.09),
    ( 0.5, 5.0, 3.0, (0.70, 0.80, 1.00), 0.07),
]
for i, (bx, by, bz, bc, br) in enumerate(bokeh_positions):
    mat_bokeh = make_mat(f'Bokeh_{i}', bc,
                          emission_color=bc,
                          emission_strength=8.0,
                          roughness=0.0)
    b_sphere = add_sphere(f'Bokeh_{i}', mat_bokeh,
                           location=(bx, by, bz),
                           radius=br, segments=8, rings=4)

# ============================================================
# LIGHTING
# ============================================================
print("Setting up lights...")

bpy.ops.object.light_add(type='AREA', location=(1.8, -2.5, 3.2))
key = bpy.context.active_object
key.name = "KeyLight"
key.data.energy = 180
key.data.size   = 1.8
key.data.color  = (1.0, 0.88, 0.72)
key.rotation_euler = (
    math.radians(50), math.radians(20), math.radians(-35))

bpy.ops.object.light_add(type='AREA', location=(-2.0, 1.5, 2.8))
rim = bpy.context.active_object
rim.name = "RimLight"
rim.data.energy = 120
rim.data.size   = 1.2
rim.data.color  = (0.45, 0.55, 1.0)
rim.rotation_euler = (
    math.radians(55), math.radians(-25), math.radians(145))

bpy.ops.object.light_add(type='AREA', location=(0.0, -3.5, 1.5))
fill = bpy.context.active_object
fill.name = "FillLight"
fill.data.energy = 30
fill.data.size   = 3.5
fill.data.color  = (0.70, 0.75, 0.95)

bpy.ops.object.light_add(type='AREA', location=(0.2, -0.5, 4.0))
top_l = bpy.context.active_object
top_l.name = "TopLight"
top_l.data.energy = 50
top_l.data.size   = 1.5
top_l.data.color  = (1.0, 0.95, 0.85)
top_l.rotation_euler = (math.radians(90), 0, 0)

bpy.ops.object.light_add(type='POINT', location=(0.34, -0.32, 0.72))
flame_light = bpy.context.active_object
flame_light.name = "FlamePractical"
flame_light.data.energy = 12
flame_light.data.color  = (1.0, 0.55, 0.08)
flame_light.data.shadow_soft_size = 0.05

bpy.ops.object.light_add(type='POINT', location=(0.04, -0.375, 1.648))
cig_light = bpy.context.active_object
cig_light.name = "CigGlow"
cig_light.data.energy = 3
cig_light.data.color  = (1.0, 0.45, 0.05)
cig_light.data.shadow_soft_size = 0.02

# ============================================================
# CAMERA
# ============================================================
print("Setting up camera...")

bpy.ops.object.camera_add(location=(0.15, -2.8, 1.72))
camera = bpy.context.active_object
camera.name = "PortraitCamera"
camera.data.lens               = 85
camera.data.sensor_width       = 36
camera.data.dof.use_dof        = True
camera.data.dof.aperture_fstop = 1.8
camera.data.dof.focus_distance = 2.8
camera.data.clip_start         = 0.1
camera.data.clip_end           = 50.0

target = (0.0, -0.1, 1.78)
dx   = target[0] - camera.location[0]
dy   = target[1] - camera.location[1]
dz_v = target[2] - camera.location[2]
camera.rotation_euler = (
    math.atan2(math.sqrt(dx**2 + dy**2), dz_v),
    0,
    math.atan2(dx, -dy)
)
bpy.context.scene.camera = camera

# ============================================================
# RENDER SETTINGS
# ============================================================
print("Configuring render settings...")

scene = bpy.context.scene
scene.render.engine                     = 'CYCLES'
scene.cycles.device                     = 'CPU'
scene.cycles.samples                    = 256
scene.cycles.use_denoising              = True
scene.cycles.denoiser                   = 'OPENIMAGEDENOISE'
scene.cycles.preview_samples            = 32
scene.render.resolution_x               = 2048
scene.render.resolution_y               = 2048
scene.render.resolution_percentage      = 100
scene.render.film_transparent           = False
scene.render.image_settings.file_format = 'PNG'
scene.render.image_settings.color_mode  = 'RGBA'
scene.render.image_settings.compression = 10

# Tile size (3.x only — ignored safely in newer versions)
try:
    scene.cycles.tile_x = 128
    scene.cycles.tile_y = 128
except AttributeError:
    pass

# ── Color management — SAFE for 3.6 ─────────────────────────
scene.view_settings.view_transform = 'Filmic'
scene.view_settings.exposure = 0.2
scene.view_settings.gamma    = 1.0

# Safe look setter — only apply if the look actually exists
available_looks = [l.name for l in bpy.types.ColorManagedViewSettings.bl_rna.properties['look'].enum_items]
desired_look = 'High Contrast'
if desired_look in available_looks:
    scene.view_settings.look = desired_look
else:
    # Fallback: use whatever is available
    for fallback in ['Medium High Contrast', 'Medium Contrast', 'None']:
        if fallback in available_looks:
            scene.view_settings.look = fallback
            print(f"Color look: using '{fallback}' instead of '{desired_look}'")
            break

world = bpy.data.worlds.get("World") or bpy.data.worlds.new("World")
scene.world = world
world.use_nodes = True
bg_node = world.node_tree.nodes.get("Background")
if bg_node:
    bg_node.inputs['Color'].default_value    = (0.008, 0.008, 0.015, 1.0)
    bg_node.inputs['Strength'].default_value = 0.3

# ============================================================
# COMPOSITOR
# ============================================================
print("Setting up compositor...")

scene.use_nodes = True
comp_tree  = scene.node_tree
comp_nodes = comp_tree.nodes
comp_links = comp_tree.links

for n in list(comp_nodes):
    comp_nodes.remove(n)

rl = comp_nodes.new('CompositorNodeRLayers')
rl.location = (-400, 0)

glare = comp_nodes.new('CompositorNodeGlare')
glare.location   = (-100, 0)
glare.glare_type = 'FOG_GLOW'
glare.quality    = 'HIGH'
glare.threshold  = 0.85
glare.size       = 7
comp_links.new(rl.outputs['Image'], glare.inputs['Image'])

# ── Lens distortion — index-safe for 3.6 ────────────────────
lens = comp_nodes.new('CompositorNodeLensdist')
lens.location = (150, 0)
try:
    lens.inputs['Distort'].default_value    = -0.015
    lens.inputs['Dispersion'].default_value = 0.004
except (KeyError, IndexError):
    try:
        lens.inputs[1].default_value = -0.015
        lens.inputs[2].default_value = 0.004
    except Exception:
        pass
comp_links.new(glare.outputs['Image'], lens.inputs['Image'])

cb = comp_nodes.new('CompositorNodeColorBalance')
cb.location          = (400, 0)
cb.correction_method = 'LIFT_GAMMA_GAIN'
cb.lift  = (0.96, 0.97, 1.02, 1.0)
cb.gamma = (1.02, 1.00, 0.97, 1.0)
cb.gain  = (1.05, 1.02, 0.95, 1.0)
comp_links.new(lens.outputs['Image'], cb.inputs['Image'])

ellipse = comp_nodes.new('CompositorNodeEllipseMask')
ellipse.location = (150, -250)
ellipse.width    = 0.85
ellipse.height   = 0.85

blur_vig = comp_nodes.new('CompositorNodeBlur')
blur_vig.location = (350, -250)
blur_vig.size_x   = 120
blur_vig.size_y   = 120
comp_links.new(ellipse.outputs['Mask'], blur_vig.inputs['Image'])

mix_vig = comp_nodes.new('CompositorNodeMixRGB')
mix_vig.location                = (600, 0)
mix_vig.blend_type              = 'MULTIPLY'
mix_vig.inputs[0].default_value = 0.55
comp_links.new(cb.outputs['Image'],       mix_vig.inputs[1])
comp_links.new(blur_vig.outputs['Image'], mix_vig.inputs[2])

comp_out = comp_nodes.new('CompositorNodeComposite')
comp_out.location = (850, 0)
comp_links.new(mix_vig.outputs['Image'], comp_out.inputs['Image'])

viewer = comp_nodes.new('CompositorNodeViewer')
viewer.location = (850, -150)
comp_links.new(mix_vig.outputs['Image'], viewer.inputs['Image'])

print("Compositor configured")

# ============================================================
# SAVE .BLEND
# ============================================================
print(f"Saving .blend: {OUTPUT_BLEND}")
bpy.ops.wm.save_as_mainfile(filepath=OUTPUT_BLEND)
print("Blend saved")

# ============================================================
# EXPORT GLB
# ============================================================
print(f"Exporting GLB: {OUTPUT_GLB}")
try:
    bpy.ops.export_scene.gltf(
        filepath=OUTPUT_GLB,
        export_format='GLB',
        use_selection=False,
        export_apply=True,
        export_materials='EXPORT',
    )
    print("GLB exported")
except Exception as e:
    print(f"GLB export failed (non-fatal): {e}")

# ============================================================
# EXPORT USDZ
# ============================================================
print(f"Exporting USDZ: {OUTPUT_USDZ}")
usdz_ok = False

try:
    # Blender 3.6 usd_export compatible parameters only
    bpy.ops.wm.usd_export(
        filepath=OUTPUT_USDZ,
        selected_objects_only=False,
        visible_objects_only=True,
        export_animation=False,
        export_uvmaps=True,
        export_normals=True,
        export_materials=True,
        evaluation_mode='RENDER',
    )
    if os.path.exists(OUTPUT_USDZ) and os.path.getsize(OUTPUT_USDZ) > 0:
        usdz_ok = True
        print(f"USDZ exported: {OUTPUT_USDZ}")
except Exception as e:
    print(f"USDZ export attempt 1 failed: {e}")

if not usdz_ok:
    try:
        import zipfile
        usdc_path = OUTPUT_USDZ.replace('.usdz', '.usdc')
        bpy.ops.wm.usd_export(
            filepath=usdc_path,
            selected_objects_only=False,
            export_materials=True)
        with zipfile.ZipFile(OUTPUT_USDZ, 'w', zipfile.ZIP_DEFLATED) as zf:
            zf.write(usdc_path, os.path.basename(usdc_path))
        print(f"USDZ packaged via zip: {OUTPUT_USDZ}")
    except Exception as e2:
        print(f"USDZ fallback failed (non-fatal): {e2}")

# ============================================================
# RENDER PNG
# ============================================================
print("=" * 60)
print("  STARTING RENDER")
print(f"  {scene.render.resolution_x}x{scene.render.resolution_y}")
print(f"  {scene.cycles.samples} samples + OIDN denoiser")
print(f"  Output: {OUTPUT_PNG}")
print("=" * 60)

scene.render.filepath = OUTPUT_PNG
bpy.ops.render.render(write_still=True)

# ============================================================
# FINAL REPORT
# ============================================================
print("=" * 60)
print("  ALL DONE")
print("=" * 60)
for label, path in [
    ("PNG Render",    OUTPUT_PNG),
    ("Blender Scene", OUTPUT_BLEND),
    ("USDZ iPhone",   OUTPUT_USDZ),
    ("GLB Web",       OUTPUT_GLB),
]:
    if os.path.exists(path) and os.path.getsize(path) > 0:
        mb = os.path.getsize(path) / 1048576
        print(f"  OK   {label:<18} {mb:.2f} MB")
    else:
        print(f"  MISS {label:<18} not generated")
print("=" * 60)
print("  iPhone AR: Download .usdz -> AirDrop -> tap in Files app")
print("=" * 60)
