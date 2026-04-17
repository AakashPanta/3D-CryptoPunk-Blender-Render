"""
CryptoPunk 3D Voxel Render — GitHub Actions Compatible
Runs headless in Blender via CLI. Outputs PNG + .blend file.
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

print(f"📁 Output directory: {output_dir}")
print(f"🖼️  Render output:   {OUTPUT_IMAGE}")
print(f"📦 Blend output:     {OUTPUT_BLEND}")

# ============================================================
# CLEAN SCENE
# ============================================================
def clean_scene():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    for block_type in [bpy.data.materials, bpy.data.meshes,
                       bpy.data.cameras, bpy.data.lights]:
        for block in block_type:
            block_type.remove(block)

clean_scene()

# ============================================================
# CONFIG
# ============================================================
VOXEL_SIZE = 0.1
BEVEL_AMOUNT = 0.012
BEVEL_SEGMENTS = 2  # Slightly lower for CI speed
DEPTH_LAYERS = 3

# ============================================================
# COLORS
# ============================================================
COLORS = {
    'skin':        (0.93, 0.75, 0.57, 1.0),
    'skin_shadow': (0.82, 0.65, 0.47, 1.0),
    'cap_blue':    (0.45, 0.55, 0.82, 1.0),
    'cap_brim':    (0.15, 0.15, 0.18, 1.0),
    'check_white': (0.95, 0.95, 0.97, 1.0),
    'eye_black':   (0.02, 0.02, 0.03, 1.0),
    'eye_white':   (0.92, 0.92, 0.92, 1.0),
    'shirt_green': (0.55, 0.85, 0.22, 1.0),
    'shirt_dark':  (0.40, 0.70, 0.15, 1.0),
    'collar_white':(0.90, 0.90, 0.90, 1.0),
    'cigarette':   (0.88, 0.85, 0.78, 1.0),
    'cig_tip':     (0.95, 0.45, 0.08, 1.0),
    'smoke_gray':  (0.65, 0.65, 0.68, 1.0),
    'lighter_red': (0.85, 0.12, 0.10, 1.0),
    'lighter_top': (0.75, 0.75, 0.78, 1.0),
    'flame_orange':(1.0, 0.65, 0.08, 1.0),
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

    output = nodes.new('ShaderNodeOutputMaterial')
    output.location = (400, 0)

    bsdf = nodes.new('ShaderNodeBsdfPrincipled')
    bsdf.location = (0, 0)
    bsdf.inputs['Base Color'].default_value = color
    bsdf.inputs['Metallic'].default_value = metallic
    bsdf.inputs['Roughness'].default_value = roughness

    # Subsurface — handle different Blender versions
    for key in ['Subsurface Weight', 'Subsurface']:
        if key in bsdf.inputs:
            bsdf.inputs[key].default_value = subsurface
            break

    # Emission
    if emission > 0:
        for ekey in ['Emission Strength']:
            if ekey in bsdf.inputs:
                bsdf.inputs[ekey].default_value = emission
                break
        for ckey in ['Emission Color', 'Emission']:
            if ckey in bsdf.inputs:
                try:
                    bsdf.inputs[ckey].default_value = color
                except:
                    pass
                break

    links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
    material_cache[name] = mat
    return mat


# Create all materials
mat_skin       = create_material('Skin', COLORS['skin'],
                                 roughness=0.6, subsurface=0.3)
mat_skin_shd   = create_material('SkinShadow', COLORS['skin_shadow'],
                                 roughness=0.65, subsurface=0.2)
mat_cap        = create_material('CapBlue', COLORS['cap_blue'],
                                 metallic=0.3, roughness=0.35)
mat_brim       = create_material('CapBrim', COLORS['cap_brim'],
                                 metallic=0.1, roughness=0.4)
mat_check      = create_material('CheckWhite', COLORS['check_white'],
                                 roughness=0.3, emission=0.8)
mat_eye_blk    = create_material('EyeBlack', COLORS['eye_black'],
                                 roughness=0.15)
mat_eye_wht    = create_material('EyeWhite', COLORS['eye_white'],
                                 roughness=0.3)
mat_shirt      = create_material('ShirtGreen', COLORS['shirt_green'],
                                 roughness=0.4)
mat_shirt_dk   = create_material('ShirtDark', COLORS['shirt_dark'],
                                 roughness=0.45)
mat_collar     = create_material('Collar', COLORS['collar_white'],
                                 roughness=0.5)
mat_cig        = create_material('Cigarette', COLORS['cigarette'],
                                 roughness=0.7)
mat_cig_tip    = create_material('CigTip', COLORS['cig_tip'],
                                 roughness=0.4, emission=3.0)
mat_smoke      = create_material('Smoke', COLORS['smoke_gray'],
                                 roughness=0.9)
mat_lighter_r  = create_material('LighterRed', COLORS['lighter_red'],
                                 roughness=0.25)
mat_lighter_t  = create_material('LighterTop', COLORS['lighter_top'],
                                 metallic=0.8, roughness=0.15)
mat_flame      = create_material('Flame', COLORS['flame_orange'],
                                 emission=15.0, roughness=0.0)

# ============================================================
# VOXEL PLACEMENT
# ============================================================
all_voxels = []

def place_voxel(x, y, material, depth=None):
    if depth is None:
        depth = DEPTH_LAYERS
    for dz in range(depth):
        bpy.ops.mesh.primitive_cube_add(
            size=VOXEL_SIZE * 0.96,
            location=(x * VOXEL_SIZE, -dz * VOXEL_SIZE, y * VOXEL_SIZE)
        )
        obj = bpy.context.active_object
        obj.name = f"v_{x}_{y}_{dz}"

        bev = obj.modifiers.new(name="Bevel", type='BEVEL')
        bev.width = BEVEL_AMOUNT
        bev.segments = BEVEL_SEGMENTS
        bev.limit_method = 'ANGLE'

        obj.data.materials.append(material)
        all_voxels.append(obj)


# ============================================================
# BUILD THE CHARACTER
# ============================================================
print("🔨 Building character voxels...")

# --- CAP ---
for x in range(5, 12):  place_voxel(x, 23, mat_cap)
for x in range(4, 13):  place_voxel(x, 22, mat_cap)
for x in range(3, 14):  place_voxel(x, 21, mat_cap)
for x in range(3, 14):  place_voxel(x, 20, mat_cap)
for x in range(3, 15):  place_voxel(x, 19, mat_cap)

# Checkmark
for pos in [(7,22),(8,21),(9,22),(10,23),(6,21)]:
    place_voxel(pos[0], pos[1], mat_check, depth=1)

# Brim
for x in range(2, 16):  place_voxel(x, 18, mat_brim)
for x in range(1, 16):  place_voxel(x, 17, mat_brim)

# --- FACE ---
for x in range(4, 13):  place_voxel(x, 16, mat_skin)
for x in range(3, 13):  place_voxel(x, 15, mat_skin)
for x in range(3, 13):  place_voxel(x, 14, mat_skin)

# Eyes
for pos in [(4,14),(5,14),(5,15),(4,13)]:
    place_voxel(pos[0], pos[1], mat_eye_blk, depth=1)
place_voxel(6, 14, mat_eye_wht, depth=1)

# Nose & mid-face
for x in range(3, 12):  place_voxel(x, 13, mat_skin)
place_voxel(2, 13, mat_skin)
place_voxel(2, 12, mat_skin)
for x in range(3, 12):  place_voxel(x, 12, mat_skin)

# Mouth area
for x in range(3, 11):  place_voxel(x, 11, mat_skin)
for x in range(4, 11):  place_voxel(x, 10, mat_skin)

# Chin / jaw
for x in range(5, 11):  place_voxel(x, 9, mat_skin)
for x in range(6, 11):  place_voxel(x, 8, mat_skin)

# --- CIGARETTE ---
for x in [1, 0, -1]:
    place_voxel(x, 11, mat_cig, depth=2)
place_voxel(-2, 11, mat_cig_tip, depth=2)

# Smoke
smoke_positions = [(-3,12),(-3,13),(-4,14),(-3,15),
                   (-4,16),(-4,17),(-3,18),(-4,19)]
for pos in smoke_positions:
    place_voxel(pos[0], pos[1], mat_smoke, depth=1)

# --- NECK ---
for x in range(7, 10):  place_voxel(x, 7, mat_skin)

# --- COLLAR ---
for x in range(5, 11):  place_voxel(x, 6, mat_collar)
place_voxel(6, 7, mat_collar)
place_voxel(10, 7, mat_collar)

# --- SHIRT ---
for x in range(4, 12):  place_voxel(x, 5, mat_shirt)
for x in range(3, 13):  place_voxel(x, 4, mat_shirt)
for x in range(3, 13):  place_voxel(x, 3, mat_shirt)
for x in range(3, 14):  place_voxel(x, 2, mat_shirt)
for x in range(3, 14):  place_voxel(x, 1, mat_shirt)
for x in range(4, 14):  place_voxel(x, 0, mat_shirt)

# Sleeve shading
for pos in [(3,5),(12,5),(13,3),(13,2)]:
    place_voxel(pos[0], pos[1], mat_shirt_dk)

# --- ARM / HAND ---
arm_positions = [(2,5),(1,5),(1,6),(0,6),(0,7),(1,7),
                 (0,8),(1,8),(-1,7),(-1,8),(0,9),(1,9),(-1,9)]
for pos in arm_positions:
    place_voxel(pos[0], pos[1], mat_skin)

# --- LIGHTER ---
place_voxel(0, 9, mat_lighter_r, depth=1)
place_voxel(0, 10, mat_lighter_r, depth=2)
place_voxel(-1, 10, mat_lighter_r, depth=2)
place_voxel(-1, 6, mat_lighter_r, depth=2)
place_voxel(-1, 5, mat_lighter_r, depth=2)
place_voxel(-1, 7, mat_lighter_t, depth=1)

# Flame
for pos in [(-1,8),(-1,9),(-2,9)]:
    place_voxel(pos[0], pos[1], mat_flame, depth=1)

print(f"✅ Placed {len(all_voxels)} voxels")

# ============================================================
# BACKGROUND
# ============================================================
bpy.ops.mesh.primitive_plane_add(size=20, location=(0.5, -0.5, -0.3))
floor = bpy.context.active_object
floor.name = "Floor"

mat_floor = create_material('Floor', (0.02, 0.02, 0.03, 1.0),
                            metallic=0.0, roughness=0.15)
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
# Key light
bpy.ops.object.light_add(type='AREA', location=(2.0, -3.0, 3.0))
key = bpy.context.active_object
key.name = "KeyLight"
key.data.energy = 150
key.data.size = 2.0
key.data.color = (1.0, 0.92, 0.82)
key.rotation_euler = (math.radians(45), math.radians(15), math.radians(-30))

# Rim light
bpy.ops.object.light_add(type='AREA', location=(-1.5, 2.0, 2.5))
rim = bpy.context.active_object
rim.name = "RimLight"
rim.data.energy = 80
rim.data.size = 1.5
rim.data.color = (0.6, 0.65, 1.0)
rim.rotation_euler = (math.radians(60), math.radians(-30), math.radians(150))

# Fill light
bpy.ops.object.light_add(type='AREA', location=(0.0, -4.0, 1.0))
fill = bpy.context.active_object
fill.name = "FillLight"
fill.data.energy = 25
fill.data.size = 4.0
fill.data.color = (0.85, 0.85, 0.95)

# Top accent
bpy.ops.object.light_add(type='AREA', location=(0.5, -1.0, 4.5))
top = bpy.context.active_object
top.name = "TopLight"
top.data.energy = 40
top.data.size = 1.0
top.data.color = (1.0, 0.95, 0.9)
top.rotation_euler = (math.radians(90), 0, 0)

# Flame glow
bpy.ops.object.light_add(
    type='POINT',
    location=(-1 * VOXEL_SIZE, -1 * VOXEL_SIZE, 9 * VOXEL_SIZE)
)
fg = bpy.context.active_object
fg.name = "FlameGlow"
fg.data.energy = 5
fg.data.color = (1.0, 0.6, 0.15)
fg.data.shadow_soft_size = 0.1

# ============================================================
# CAMERA
# ============================================================
bpy.ops.object.camera_add(location=(0.8, -5.5, 1.3))
camera = bpy.context.active_object
camera.name = "MainCamera"
camera.data.lens = 85
camera.data.dof.use_dof = True
camera.data.dof.aperture_fstop = 2.8
camera.data.dof.focus_distance = 5.5
camera.data.sensor_width = 36

target = (0.5, 0, 1.2)
dx = target[0] - camera.location[0]
dy = target[1] - camera.location[1]
dz = target[2] - camera.location[2]
camera.rotation_euler = (
    math.atan2(math.sqrt(dx**2 + dy**2), dz),
    0,
    math.atan2(dx, -dy)
)

bpy.context.scene.camera = camera

# ============================================================
# RENDER SETTINGS (optimized for CI)
# ============================================================
scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.cycles.device = 'CPU'
scene.cycles.samples = 128          # Good quality, CI-friendly
scene.cycles.use_denoising = True
scene.cycles.preview_samples = 32
scene.render.resolution_x = 2048
scene.render.resolution_y = 2048
scene.render.resolution_percentage = 100
scene.render.film_transparent = False
scene.render.image_settings.file_format = 'PNG'
scene.render.image_settings.color_mode = 'RGBA'
scene.render.image_settings.compression = 15

# Tile size optimization for CPU
try:
    scene.cycles.tile_x = 64
    scene.cycles.tile_y = 64
except:
    pass  # Blender 4.x uses automatic tiling

# Color management
scene.view_settings.view_transform = 'Filmic'
try:
    scene.view_settings.look = 'Medium High Contrast'
except:
    scene.view_settings.look = 'High Contrast'

# World
world = bpy.data.worlds.get("World")
if not world:
    world = bpy.data.worlds.new("World")
scene.world = world
world.use_nodes = True
bg_node = world.node_tree.nodes.get("Background")
if bg_node:
    bg_node.inputs['Color'].default_value = (0.01, 0.01, 0.015, 1.0)
    bg_node.inputs['Strength'].default_value = 0.5

# ============================================================
# SAVE .BLEND FILE
# ============================================================
print(f"💾 Saving .blend file to: {OUTPUT_BLEND}")
bpy.ops.wm.save_as_mainfile(filepath=OUTPUT_BLEND)

# ============================================================
# RENDER
# ============================================================
print("=" * 60)
print("  🎬 STARTING RENDER")
print(f"  Resolution: {scene.render.resolution_x}x{scene.render.resolution_y}")
print(f"  Samples:    {scene.cycles.samples}")
print(f"  Engine:     Cycles (CPU)")
print(f"  Output:     {OUTPUT_IMAGE}")
print("=" * 60)

scene.render.filepath = OUTPUT_IMAGE
bpy.ops.render.render(write_still=True)

print("=" * 60)
print("  ✅ RENDER COMPLETE!")
print(f"  📁 Image saved to: {OUTPUT_IMAGE}")
print("=" * 60)
