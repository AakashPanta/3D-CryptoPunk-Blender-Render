"""
CryptoPunk 3D Voxel Render - GitHub Actions Compatible
Outputs: PNG render + .blend + .usdz (iPhone AR) + .glb (web)
"""

import bpy
import math
import sys
import os

# ============================================================
# PARSE CLI ARGUMENTS
# ============================================================
argv = sys.argv
output_dir = os.getcwd() + "/output"

if "--" in argv:
    custom_args = argv[argv.index("--") + 1:]
    for i, arg in enumerate(custom_args):
        if arg == "--output-dir" and i + 1 < len(custom_args):
            output_dir = custom_args[i + 1]

os.makedirs(output_dir, exist_ok=True)

OUTPUT_IMAGE = os.path.join(output_dir, "cryptopunk_3d_render.png")
OUTPUT_BLEND = os.path.join(output_dir, "cryptopunk_scene.blend")
OUTPUT_USDZ  = os.path.join(output_dir, "cryptopunk_iphone.usdz")
OUTPUT_USDC  = os.path.join(output_dir, "cryptopunk_scene.usdc")
OUTPUT_GLB   = os.path.join(output_dir, "cryptopunk_scene.glb")

print("=" * 60)
print("  CryptoPunk 3D — Blender Headless Pipeline")
print("=" * 60)
print(f"  Output dir:  {output_dir}")
print(f"  PNG:         {OUTPUT_IMAGE}")
print(f"  Blend:       {OUTPUT_BLEND}")
print(f"  USDZ:        {OUTPUT_USDZ}")
print(f"  GLB:         {OUTPUT_GLB}")
print("=" * 60)

# ============================================================
# CLEAN SCENE
# ============================================================
def clean_scene():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    for bt in [bpy.data.materials, bpy.data.meshes,
               bpy.data.cameras, bpy.data.lights]:
        for b in bt:
            bt.remove(b)

clean_scene()
print("Scene cleaned")

# ============================================================
# CONFIG
# ============================================================
VOXEL_SIZE     = 0.1
BEVEL_AMOUNT   = 0.012
BEVEL_SEGMENTS = 2
DEPTH_LAYERS   = 3

# ============================================================
# COLORS
# ============================================================
COLORS = {
    'skin':         (0.93, 0.75, 0.57, 1.0),
    'skin_shadow':  (0.82, 0.65, 0.47, 1.0),
    'cap_blue':     (0.45, 0.55, 0.82, 1.0),
    'cap_brim':     (0.15, 0.15, 0.18, 1.0),
    'check_white':  (0.95, 0.95, 0.97, 1.0),
    'eye_black':    (0.02, 0.02, 0.03, 1.0),
    'eye_white':    (0.92, 0.92, 0.92, 1.0),
    'shirt_green':  (0.55, 0.85, 0.22, 1.0),
    'shirt_dark':   (0.40, 0.70, 0.15, 1.0),
    'collar_white': (0.90, 0.90, 0.90, 1.0),
    'cigarette':    (0.88, 0.85, 0.78, 1.0),
    'cig_tip':      (0.95, 0.45, 0.08, 1.0),
    'smoke_gray':   (0.65, 0.65, 0.68, 1.0),
    'lighter_red':  (0.85, 0.12, 0.10, 1.0),
    'lighter_top':  (0.75, 0.75, 0.78, 1.0),
    'flame_orange': (1.0,  0.65, 0.08, 1.0),
}

# ============================================================
# MATERIAL CREATION
# ============================================================
material_cache = {}

def create_material(name, color, metallic=0.0, roughness=0.5,
                    emission=0.0, subsurface=0.0):
    if name in material_cache:
        return material_cache[name]

    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links

    for node in nodes:
        nodes.remove(node)

    out_node = nodes.new('ShaderNodeOutputMaterial')
    out_node.location = (400, 0)

    bsdf = nodes.new('ShaderNodeBsdfPrincipled')
    bsdf.location = (0, 0)
    bsdf.inputs['Base Color'].default_value = color
    bsdf.inputs['Metallic'].default_value   = metallic
    bsdf.inputs['Roughness'].default_value  = roughness

    # Subsurface — Blender version safe
    for key in ['Subsurface Weight', 'Subsurface']:
        if key in bsdf.inputs:
            try:
                bsdf.inputs[key].default_value = subsurface
            except Exception:
                pass
            break

    # Emission — Blender version safe
    if emission > 0:
        for ekey in ['Emission Strength']:
            if ekey in bsdf.inputs:
                try:
                    bsdf.inputs[ekey].default_value = emission
                except Exception:
                    pass
                break
        for ckey in ['Emission Color', 'Emission']:
            if ckey in bsdf.inputs:
                try:
                    bsdf.inputs[ckey].default_value = color
                except Exception:
                    pass
                break

    links.new(bsdf.outputs['BSDF'], out_node.inputs['Surface'])
    material_cache[name] = mat
    return mat


# ============================================================
# CREATE ALL MATERIALS
# ============================================================
print("Creating materials...")

mat_skin      = create_material('Skin',         COLORS['skin'],
                                roughness=0.6,  subsurface=0.3)
mat_skin_shd  = create_material('SkinShadow',   COLORS['skin_shadow'],
                                roughness=0.65, subsurface=0.2)
mat_cap       = create_material('CapBlue',      COLORS['cap_blue'],
                                metallic=0.3,   roughness=0.35)
mat_brim      = create_material('CapBrim',      COLORS['cap_brim'],
                                metallic=0.1,   roughness=0.4)
mat_check     = create_material('CheckWhite',   COLORS['check_white'],
                                roughness=0.3,  emission=0.8)
mat_eye_blk   = create_material('EyeBlack',     COLORS['eye_black'],
                                roughness=0.15)
mat_eye_wht   = create_material('EyeWhite',     COLORS['eye_white'],
                                roughness=0.3)
mat_shirt     = create_material('ShirtGreen',   COLORS['shirt_green'],
                                roughness=0.4)
mat_shirt_dk  = create_material('ShirtDark',    COLORS['shirt_dark'],
                                roughness=0.45)
mat_collar    = create_material('Collar',       COLORS['collar_white'],
                                roughness=0.5)
mat_cig       = create_material('Cigarette',    COLORS['cigarette'],
                                roughness=0.7)
mat_cig_tip   = create_material('CigTip',       COLORS['cig_tip'],
                                roughness=0.4,  emission=3.0)
mat_smoke     = create_material('Smoke',        COLORS['smoke_gray'],
                                roughness=0.9)
mat_lighter_r = create_material('LighterRed',   COLORS['lighter_red'],
                                roughness=0.25)
mat_lighter_t = create_material('LighterTop',   COLORS['lighter_top'],
                                metallic=0.8,   roughness=0.15)
mat_flame     = create_material('Flame',        COLORS['flame_orange'],
                                emission=15.0,  roughness=0.0)

print(f"Created {len(material_cache)} materials")

# ============================================================
# VOXEL PLACEMENT
# ============================================================
all_voxels = []

def place_voxel(x, y, material, depth=None):
    """Place a beveled voxel cube at grid position (x, y)."""
    if depth is None:
        depth = DEPTH_LAYERS
    for dz in range(depth):
        bpy.ops.mesh.primitive_cube_add(
            size=VOXEL_SIZE * 0.96,
            location=(
                x  * VOXEL_SIZE,
                -dz * VOXEL_SIZE,
                y  * VOXEL_SIZE
            )
        )
        obj = bpy.context.active_object
        obj.name = f"v_{x}_{y}_{dz}"

        bev = obj.modifiers.new(name="Bevel", type='BEVEL')
        bev.width          = BEVEL_AMOUNT
        bev.segments       = BEVEL_SEGMENTS
        bev.limit_method   = 'ANGLE'

        obj.data.materials.append(material)
        all_voxels.append(obj)


# ============================================================
# BUILD THE CHARACTER
# ============================================================
print("Building character...")

# ── CAP ──────────────────────────────────────────────────
for x in range(5, 12): place_voxel(x, 23, mat_cap)
for x in range(4, 13): place_voxel(x, 22, mat_cap)
for x in range(3, 14): place_voxel(x, 21, mat_cap)
for x in range(3, 14): place_voxel(x, 20, mat_cap)
for x in range(3, 15): place_voxel(x, 19, mat_cap)

# Checkmark
for px, py in [(7,22),(8,21),(9,22),(10,23),(6,21)]:
    place_voxel(px, py, mat_check, depth=1)

# Brim
for x in range(2, 16): place_voxel(x, 18, mat_brim)
for x in range(1, 16): place_voxel(x, 17, mat_brim)

# ── FACE ─────────────────────────────────────────────────
for x in range(4, 13): place_voxel(x, 16, mat_skin)
for x in range(3, 13): place_voxel(x, 15, mat_skin)
for x in range(3, 13): place_voxel(x, 14, mat_skin)

# Eyes
for px, py in [(4,14),(5,14),(5,15),(4,13)]:
    place_voxel(px, py, mat_eye_blk, depth=1)
place_voxel(6, 14, mat_eye_wht, depth=1)

# Nose & mid-face
for x in range(3, 12): place_voxel(x, 13, mat_skin)
place_voxel(2, 13, mat_skin)
place_voxel(2, 12, mat_skin)
for x in range(3, 12): place_voxel(x, 12, mat_skin)

# Mouth
for x in range(3, 11): place_voxel(x, 11, mat_skin)
for x in range(4, 11): place_voxel(x, 10, mat_skin)

# Chin / jaw
for x in range(5, 11): place_voxel(x, 9, mat_skin)
for x in range(6, 11): place_voxel(x, 8, mat_skin)

# ── CIGARETTE ────────────────────────────────────────────
for x in [1, 0, -1]:
    place_voxel(x, 11, mat_cig, depth=2)
place_voxel(-2, 11, mat_cig_tip, depth=2)

# Smoke
for px, py in [(-3,12),(-3,13),(-4,14),(-3,15),
               (-4,16),(-4,17),(-3,18),(-4,19)]:
    place_voxel(px, py, mat_smoke, depth=1)

# ── NECK ─────────────────────────────────────────────────
for x in range(7, 10): place_voxel(x, 7, mat_skin)

# ── COLLAR ───────────────────────────────────────────────
for x in range(5, 11): place_voxel(x, 6, mat_collar)
place_voxel(6, 7, mat_collar)
place_voxel(10, 7, mat_collar)

# ── SHIRT ────────────────────────────────────────────────
for x in range(4, 12): place_voxel(x, 5, mat_shirt)
for x in range(3, 13): place_voxel(x, 4, mat_shirt)
for x in range(3, 13): place_voxel(x, 3, mat_shirt)
for x in range(3, 14): place_voxel(x, 2, mat_shirt)
for x in range(3, 14): place_voxel(x, 1, mat_shirt)
for x in range(4, 14): place_voxel(x, 0, mat_shirt)

for px, py in [(3,5),(12,5),(13,3),(13,2)]:
    place_voxel(px, py, mat_shirt_dk)

# ── ARM / HAND ───────────────────────────────────────────
for px, py in [(2,5),(1,5),(1,6),(0,6),(0,7),(1,7),
               (0,8),(1,8),(-1,7),(-1,8),
               (0,9),(1,9),(-1,9)]:
    place_voxel(px, py, mat_skin)

# ── LIGHTER ──────────────────────────────────────────────
place_voxel( 0,  9, mat_lighter_r, depth=1)
place_voxel( 0, 10, mat_lighter_r, depth=2)
place_voxel(-1, 10, mat_lighter_r, depth=2)
place_voxel(-1,  6, mat_lighter_r, depth=2)
place_voxel(-1,  5, mat_lighter_r, depth=2)
place_voxel(-1,  7, mat_lighter_t, depth=1)

# ── FLAME ────────────────────────────────────────────────
for px, py in [(-1,8),(-1,9),(-2,9)]:
    place_voxel(px, py, mat_flame, depth=1)

print(f"Placed {len(all_voxels)} voxels")

# ============================================================
# BACKGROUND ENVIRONMENT
# ============================================================
print("Building environment...")

bpy.ops.mesh.primitive_plane_add(size=20, location=(0.5, -0.5, -0.3))
floor = bpy.context.active_object
floor.name = "Floor"
mat_floor = create_material('Floor', (0.02, 0.02, 0.03, 1.0), roughness=0.15)
floor.data.materials.append(mat_floor)

bpy.ops.mesh.primitive_plane_add(
    size=20, location=(0.5, 5.0, 5.0),
    rotation=(math.radians(90), 0, 0)
)
wall = bpy.context.active_object
wall.name = "BackWall"
mat_wall = create_material('Wall', (0.03, 0.03, 0.05, 1.0), roughness=0.8)
wall.data.materials.append(mat_wall)

# ============================================================
# LIGHTING
# ============================================================
print("Setting up lights...")

# Key Light
bpy.ops.object.light_add(type='AREA', location=(2.0, -3.0, 3.0))
key = bpy.context.active_object
key.name = "KeyLight"
key.data.energy = 150
key.data.size   = 2.0
key.data.color  = (1.0, 0.92, 0.82)
key.rotation_euler = (math.radians(45), math.radians(15), math.radians(-30))

# Rim Light
bpy.ops.object.light_add(type='AREA', location=(-1.5, 2.0, 2.5))
rim = bpy.context.active_object
rim.name = "RimLight"
rim.data.energy = 80
rim.data.size   = 1.5
rim.data.color  = (0.6, 0.65, 1.0)
rim.rotation_euler = (math.radians(60), math.radians(-30), math.radians(150))

# Fill Light
bpy.ops.object.light_add(type='AREA', location=(0.0, -4.0, 1.0))
fill = bpy.context.active_object
fill.name = "FillLight"
fill.data.energy = 25
fill.data.size   = 4.0
fill.data.color  = (0.85, 0.85, 0.95)

# Top Accent
bpy.ops.object.light_add(type='AREA', location=(0.5, -1.0, 4.5))
top = bpy.context.active_object
top.name = "TopLight"
top.data.energy = 40
top.data.size   = 1.0
top.data.color  = (1.0, 0.95, 0.9)
top.rotation_euler = (math.radians(90), 0, 0)

# Flame Glow
bpy.ops.object.light_add(
    type='POINT',
    location=(-1*VOXEL_SIZE, -1*VOXEL_SIZE, 9*VOXEL_SIZE)
)
fg = bpy.context.active_object
fg.name = "FlameGlow"
fg.data.energy = 5
fg.data.color  = (1.0, 0.6, 0.15)
fg.data.shadow_soft_size = 0.1

# ============================================================
# CAMERA
# ============================================================
print("Setting up camera...")

bpy.ops.object.camera_add(location=(0.8, -5.5, 1.3))
camera = bpy.context.active_object
camera.name = "MainCamera"
camera.data.lens              = 85
camera.data.dof.use_dof       = True
camera.data.dof.aperture_fstop = 2.8
camera.data.dof.focus_distance = 5.5
camera.data.sensor_width      = 36

target = (0.5, 0, 1.2)
dx    = target[0] - camera.location[0]
dy    = target[1] - camera.location[1]
dz_v  = target[2] - camera.location[2]
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
scene.render.engine                      = 'CYCLES'
scene.cycles.device                      = 'CPU'
scene.cycles.samples                     = 128
scene.cycles.use_denoising               = True
scene.cycles.preview_samples             = 32
scene.render.resolution_x                = 2048
scene.render.resolution_y                = 2048
scene.render.resolution_percentage       = 100
scene.render.film_transparent            = False
scene.render.image_settings.file_format  = 'PNG'
scene.render.image_settings.color_mode   = 'RGBA'
scene.render.image_settings.compression  = 15

try:
    scene.cycles.tile_x = 64
    scene.cycles.tile_y = 64
except AttributeError:
    pass

scene.view_settings.view_transform = 'Filmic'
try:
    scene.view_settings.look = 'Medium High Contrast'
except TypeError:
    try:
        scene.view_settings.look = 'High Contrast'
    except Exception:
        pass

# World
world = bpy.data.worlds.get("World") or bpy.data.worlds.new("World")
scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes.get("Background")
if bg:
    bg.inputs['Color'].default_value    = (0.01, 0.01, 0.015, 1.0)
    bg.inputs['Strength'].default_value = 0.5

# ============================================================
# APPLY ALL MODIFIERS (required for clean USD/GLB export)
# ============================================================
print("Applying modifiers for export...")

bpy.ops.object.select_all(action='DESELECT')
for obj in all_voxels:
    if obj and obj.name in bpy.data.objects:
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        try:
            bpy.ops.object.modifier_apply(modifier="Bevel")
        except Exception as e:
            pass  # Some may already be applied

bpy.ops.object.select_all(action='DESELECT')
print("Modifiers applied")

# ============================================================
# SAVE .BLEND FILE
# ============================================================
print(f"Saving .blend: {OUTPUT_BLEND}")
bpy.ops.wm.save_as_mainfile(filepath=OUTPUT_BLEND)
print("Blend file saved")

# ============================================================
# EXPORT GLB (Web 3D — widely supported)
# ============================================================
print(f"Exporting GLB: {OUTPUT_GLB}")
try:
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.export_scene.gltf(
        filepath=OUTPUT_GLB,
        export_format='GLB',
        use_selection=False,
        export_apply=True,
        export_materials='EXPORT',
        export_colors=True,
        export_cameras=False,
        export_lights=False,
    )
    print("GLB exported successfully")
except Exception as e:
    print(f"GLB export failed: {e}")

# ============================================================
# EXPORT USD / USDZ (iPhone AR)
# ============================================================
print(f"Exporting USDZ: {OUTPUT_USDZ}")

usdz_exported = False

# Method 1: Native Blender USDZ export (Blender 3.x+)
try:
    bpy.ops.wm.usd_export(
        filepath=OUTPUT_USDZ,
        selected_objects_only=False,
        visible_objects_only=True,
        export_animation=False,
        export_hair=False,
        export_uvmaps=True,
        export_normals=True,
        export_materials=True,
        use_instancing=False,
        evaluation_mode='RENDER',
    )
    if os.path.exists(OUTPUT_USDZ) and os.path.getsize(OUTPUT_USDZ) > 0:
        print(f"USDZ exported via native Blender: {OUTPUT_USDZ}")
        usdz_exported = True
    else:
        print("Native USDZ export produced empty file, trying fallback...")
except Exception as e:
    print(f"Native USDZ export failed: {e}")

# Method 2: Export USDC first, then zip to USDZ
if not usdz_exported:
    print(f"Trying USDC export: {OUTPUT_USDC}")
    try:
        bpy.ops.wm.usd_export(
            filepath=OUTPUT_USDC,
            selected_objects_only=False,
            visible_objects_only=True,
            export_animation=False,
            export_hair=False,
            export_uvmaps=True,
            export_normals=True,
            export_materials=True,
            use_instancing=False,
            evaluation_mode='RENDER',
        )
        print(f"USDC exported: {OUTPUT_USDC}")

        # Package USDC into USDZ (USDZ is just a zip with .usdz extension)
        import zipfile
        print(f"Packaging USDC into USDZ: {OUTPUT_USDZ}")
        with zipfile.ZipFile(OUTPUT_USDZ, 'w', zipfile.ZIP_DEFLATED) as zf:
            zf.write(OUTPUT_USDC, os.path.basename(OUTPUT_USDC))
        print(f"USDZ packaged successfully: {OUTPUT_USDZ}")
        usdz_exported = True

    except Exception as e:
        print(f"USDC/USDZ fallback failed: {e}")

# Method 3: GLB → USDZ conversion using Python usd-core if available
if not usdz_exported:
    print("Attempting GLB to USDZ conversion via usd-core...")
    try:
        from pxr import Usd, UsdGeom
        print("usd-core available but direct conversion not implemented")
        print("USDZ will not be available for this build")
    except ImportError:
        print("usd-core not available — USDZ export skipped")

if usdz_exported:
    size = os.path.getsize(OUTPUT_USDZ)
    print(f"USDZ ready: {OUTPUT_USDZ} ({size:,} bytes)")
else:
    print("WARNING: USDZ could not be exported on this platform")
    print("Use the .blend file to manually export USDZ in Blender desktop")

# ============================================================
# RENDER PNG
# ============================================================
print("=" * 60)
print("  STARTING PNG RENDER")
print(f"  Resolution: {scene.render.resolution_x} x {scene.render.resolution_y}")
print(f"  Samples:    {scene.cycles.samples} + Denoiser")
print(f"  Engine:     Cycles (CPU)")
print(f"  Voxels:     {len(all_voxels)}")
print(f"  Output:     {OUTPUT_IMAGE}")
print("=" * 60)

scene.render.filepath = OUTPUT_IMAGE
bpy.ops.render.render(write_still=True)

# ============================================================
# FINAL SUMMARY
# ============================================================
print("=" * 60)
print("  ALL EXPORTS COMPLETE")
print("=" * 60)

files_to_check = [
    ("PNG Render",    OUTPUT_IMAGE),
    ("Blender Scene", OUTPUT_BLEND),
    ("USDZ (iPhone)", OUTPUT_USDZ),
    ("USDC",          OUTPUT_USDC),
    ("GLB (Web)",     OUTPUT_GLB),
]

for label, path in files_to_check:
    if os.path.exists(path) and os.path.getsize(path) > 0:
        size_mb = os.path.getsize(path) / (1024 * 1024)
        print(f"  OK  {label:<20} {size_mb:.2f} MB  {path}")
    else:
        print(f"  --  {label:<20} (not generated)")

print("=" * 60)
print("  iPhone AR Instructions:")
print("  1. Download cryptopunk_iphone.usdz from Artifacts")
print("  2. AirDrop or iCloud it to your iPhone")
print("  3. Tap in Files app → tap AR button → place in room!")
print("=" * 60)
