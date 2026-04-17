import bpy
import os
import math
import traceback
from mathutils import Vector, Euler

# ============================================================
# GLOBALS / PATHS
# ============================================================
OUTPUT_DIR = os.path.abspath("output")
PNG_PATH = os.path.join(OUTPUT_DIR, "cryptopunk_character_render.png")
BLEND_PATH = os.path.join(OUTPUT_DIR, "cryptopunk_character.blend")
GLB_PATH = os.path.join(OUTPUT_DIR, "cryptopunk_character.glb")

print("Starting CryptoPunk 3D pipeline...")
print(f"OUTPUT_DIR = {OUTPUT_DIR}")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Blender context references
scene = bpy.context.scene
view_layer = bpy.context.view_layer
collection = bpy.context.collection

if scene is None:
    raise RuntimeError("No active Blender scene found")

# ============================================================
# HELPERS
# ============================================================
def clear_scene() -> None:
    print("Clearing scene...")
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)

    for block in bpy.data.meshes:
        if block.users == 0:
            bpy.data.meshes.remove(block)

    for block in bpy.data.materials:
        if block.users == 0:
            bpy.data.materials.remove(block)

    for block in bpy.data.images:
        if block.users == 0:
            bpy.data.images.remove(block)

    for block in bpy.data.cameras:
        if block.users == 0:
            bpy.data.cameras.remove(block)

    for block in bpy.data.lights:
        if block.users == 0:
            bpy.data.lights.remove(block)

    print("Scene cleared.")


def set_active(obj: bpy.types.Object) -> None:
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    view_layer.objects.active = obj


def shade_smooth(obj: bpy.types.Object) -> None:
    set_active(obj)
    try:
        bpy.ops.object.shade_smooth()
    except Exception:
        pass


def apply_transform(obj: bpy.types.Object) -> None:
    set_active(obj)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)


def join_objects(objs, name: str) -> bpy.types.Object:
    valid = [o for o in objs if o is not None]
    if not valid:
        raise RuntimeError(f"No objects to join for {name}")

    bpy.ops.object.select_all(action='DESELECT')
    for obj in valid:
        obj.select_set(True)

    view_layer.objects.active = valid[0]
    bpy.ops.object.join()
    joined = view_layer.objects.active
    joined.name = name
    return joined


def add_cube(name: str, location=(0, 0, 0), scale=(1, 1, 1)) -> bpy.types.Object:
    bpy.ops.mesh.primitive_cube_add(location=location)
    obj = bpy.context.active_object
    obj.name = name
    obj.scale = scale
    apply_transform(obj)
    return obj


def add_cylinder(name: str, location=(0, 0, 0), radius=0.1, depth=1.0, rotation=(0, 0, 0)) -> bpy.types.Object:
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, location=location, rotation=rotation)
    obj = bpy.context.active_object
    obj.name = name
    return obj


def add_uv_sphere(name: str, location=(0, 0, 0), radius=0.1, scale=(1, 1, 1)) -> bpy.types.Object:
    bpy.ops.mesh.primitive_uv_sphere_add(radius=radius, location=location)
    obj = bpy.context.active_object
    obj.name = name
    obj.scale = scale
    apply_transform(obj)
    return obj


def ensure_world() -> None:
    if scene.world is None:
        scene.world = bpy.data.worlds.new("World")

    world = scene.world
    world.use_nodes = True

    bg = world.node_tree.nodes.get("Background")
    if bg:
        bg.inputs[0].default_value = (0.02, 0.02, 0.03, 1.0)
        bg.inputs[1].default_value = 0.6


def make_principled_material(
    name: str,
    base_color=(0.8, 0.8, 0.8, 1.0),
    roughness=0.45,
    metallic=0.0,
    specular=0.5,
    emission=(0.0, 0.0, 0.0, 1.0),
    emission_strength=0.0
) -> bpy.types.Material:
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True

    nodes = mat.node_tree.nodes
    links = mat.node_tree.links

    for n in list(nodes):
        nodes.remove(n)

    out = nodes.new(type="ShaderNodeOutputMaterial")
    out.location = (300, 0)

    bsdf = nodes.new(type="ShaderNodeBsdfPrincipled")
    bsdf.location = (0, 0)
    bsdf.inputs["Base Color"].default_value = base_color
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic

    if "Specular IOR Level" in bsdf.inputs:
        bsdf.inputs["Specular IOR Level"].default_value = specular
    elif "Specular" in bsdf.inputs:
        bsdf.inputs["Specular"].default_value = specular

    if "Emission Color" in bsdf.inputs:
        bsdf.inputs["Emission Color"].default_value = emission
    elif "Emission" in bsdf.inputs:
        bsdf.inputs["Emission"].default_value = emission

    if "Emission Strength" in bsdf.inputs:
        bsdf.inputs["Emission Strength"].default_value = emission_strength

    links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return mat


def assign_material(obj: bpy.types.Object, mat: bpy.types.Material) -> None:
    if obj.data is None:
        return
    if len(obj.data.materials) == 0:
        obj.data.materials.append(mat)
    else:
        obj.data.materials[0] = mat


# ============================================================
# MATERIALS
# ============================================================
def create_materials():
    print("Creating materials...")
    mats = {}

    mats["skin"] = make_principled_material(
        "M_Skin",
        base_color=(0.96, 0.76, 0.58, 1.0),
        roughness=0.7,
        metallic=0.0,
        specular=0.35
    )

    mats["shirt"] = make_principled_material(
        "M_Shirt",
        base_color=(0.12, 0.62, 0.92, 1.0),
        roughness=0.55,
        metallic=0.0,
        specular=0.45
    )

    mats["coat"] = make_principled_material(
        "M_Coat",
        base_color=(0.10, 0.10, 0.12, 1.0),
        roughness=0.35,
        metallic=0.05,
        specular=0.55
    )

    mats["pants"] = make_principled_material(
        "M_Pants",
        base_color=(0.08, 0.09, 0.12, 1.0),
        roughness=0.6,
        metallic=0.0,
        specular=0.35
    )

    mats["shoe"] = make_principled_material(
        "M_Shoe",
        base_color=(0.04, 0.04, 0.05, 1.0),
        roughness=0.4,
        metallic=0.1,
        specular=0.45
    )

    mats["hair"] = make_principled_material(
        "M_Hair",
        base_color=(0.15, 0.08, 0.03, 1.0),
        roughness=0.75,
        metallic=0.0,
        specular=0.2
    )

    mats["eye"] = make_principled_material(
        "M_Eye",
        base_color=(0.03, 0.03, 0.03, 1.0),
        roughness=0.2,
        metallic=0.0,
        specular=0.8
    )

    mats["mouth"] = make_principled_material(
        "M_Mouth",
        base_color=(0.25, 0.06, 0.08, 1.0),
        roughness=0.5,
        metallic=0.0,
        specular=0.3
    )

    mats["glasses"] = make_principled_material(
        "M_Glasses",
        base_color=(0.03, 0.03, 0.04, 1.0),
        roughness=0.15,
        metallic=0.95,
        specular=0.5
    )

    mats["earring"] = make_principled_material(
        "M_Earring",
        base_color=(0.95, 0.75, 0.12, 1.0),
        roughness=0.22,
        metallic=1.0,
        specular=0.5
    )

    mats["bg"] = make_principled_material(
        "M_Background",
        base_color=(0.10, 0.08, 0.18, 1.0),
        roughness=0.9,
        metallic=0.0,
        specular=0.2
    )

    print("Materials created.")
    return mats


# ============================================================
# MODEL
# ============================================================
def create_background(mats):
    bg = add_cube(
        "Background",
        location=(0, 1.9, 0),
        scale=(3.4, 0.05, 3.4)
    )
    assign_material(bg, mats["bg"])
    return bg


def create_character(mats):
    print("Creating character...")

    parts = []

    # Head
    head = add_cube(
        "Head",
        location=(0, 0, 1.65),
        scale=(0.62, 0.24, 0.62)
    )
    assign_material(head, mats["skin"])
    parts.append(head)

    # Neck
    neck = add_cube(
        "Neck",
        location=(0, 0, 1.05),
        scale=(0.16, 0.12, 0.12)
    )
    assign_material(neck, mats["skin"])
    parts.append(neck)

    # Torso / shirt
    torso = add_cube(
        "Torso",
        location=(0, 0, 0.45),
        scale=(0.52, 0.24, 0.48)
    )
    assign_material(torso, mats["shirt"])
    parts.append(torso)

    # Coat panels
    coat_left = add_cube(
        "Coat_Left",
        location=(-0.28, 0.0, 0.45),
        scale=(0.10, 0.26, 0.50)
    )
    coat_right = add_cube(
        "Coat_Right",
        location=(0.28, 0.0, 0.45),
        scale=(0.10, 0.26, 0.50)
    )
    assign_material(coat_left, mats["coat"])
    assign_material(coat_right, mats["coat"])
    parts.extend([coat_left, coat_right])

    # Arms
    arm_l = add_cube(
        "Arm_L",
        location=(-0.72, 0.0, 0.48),
        scale=(0.14, 0.16, 0.46)
    )
    arm_r = add_cube(
        "Arm_R",
        location=(0.72, 0.0, 0.48),
        scale=(0.14, 0.16, 0.46)
    )
    assign_material(arm_l, mats["coat"])
    assign_material(arm_r, mats["coat"])
    parts.extend([arm_l, arm_r])

    # Hands
    hand_l = add_cube(
        "Hand_L",
        location=(-0.72, 0.0, -0.12),
        scale=(0.12, 0.12, 0.12)
    )
    hand_r = add_cube(
        "Hand_R",
        location=(0.72, 0.0, -0.12),
        scale=(0.12, 0.12, 0.12)
    )
    assign_material(hand_l, mats["skin"])
    assign_material(hand_r, mats["skin"])
    parts.extend([hand_l, hand_r])

    # Legs
    leg_l = add_cube(
        "Leg_L",
        location=(-0.20, 0.0, -0.62),
        scale=(0.18, 0.18, 0.52)
    )
    leg_r = add_cube(
        "Leg_R",
        location=(0.20, 0.0, -0.62),
        scale=(0.18, 0.18, 0.52)
    )
    assign_material(leg_l, mats["pants"])
    assign_material(leg_r, mats["pants"])
    parts.extend([leg_l, leg_r])

    # Shoes
    shoe_l = add_cube(
        "Shoe_L",
        location=(-0.20, 0.12, -1.26),
        scale=(0.22, 0.30, 0.10)
    )
    shoe_r = add_cube(
        "Shoe_R",
        location=(0.20, 0.12, -1.26),
        scale=(0.22, 0.30, 0.10)
    )
    assign_material(shoe_l, mats["shoe"])
    assign_material(shoe_r, mats["shoe"])
    parts.extend([shoe_l, shoe_r])

    # Hair
    hair_top = add_cube(
        "Hair_Top",
        location=(0.0, 0.0, 2.10),
        scale=(0.64, 0.25, 0.16)
    )
    assign_material(hair_top, mats["hair"])
    parts.append(hair_top)

    hair_left = add_cube(
        "Hair_Left",
        location=(-0.54, 0.0, 1.86),
        scale=(0.10, 0.24, 0.24)
    )
    hair_right = add_cube(
        "Hair_Right",
        location=(0.54, 0.0, 1.86),
        scale=(0.10, 0.24, 0.24)
    )
    assign_material(hair_left, mats["hair"])
    assign_material(hair_right, mats["hair"])
    parts.extend([hair_left, hair_right])

    # Eyes
    eye_l = add_cube(
        "Eye_L",
        location=(-0.20, -0.245, 1.70),
        scale=(0.09, 0.02, 0.09)
    )
    eye_r = add_cube(
        "Eye_R",
        location=(0.20, -0.245, 1.70),
        scale=(0.09, 0.02, 0.09)
    )
    assign_material(eye_l, mats["eye"])
    assign_material(eye_r, mats["eye"])
    parts.extend([eye_l, eye_r])

    # Mouth
    mouth = add_cube(
        "Mouth",
        location=(0.0, -0.245, 1.42),
        scale=(0.18, 0.02, 0.05)
    )
    assign_material(mouth, mats["mouth"])
    parts.append(mouth)

    # Glasses
    glass_l = add_cube(
        "Glass_L",
        location=(-0.20, -0.27, 1.70),
        scale=(0.18, 0.02, 0.18)
    )
    glass_r = add_cube(
        "Glass_R",
        location=(0.20, -0.27, 1.70),
        scale=(0.18, 0.02, 0.18)
    )
    bridge = add_cube(
        "Glass_Bridge",
        location=(0.0, -0.27, 1.70),
        scale=(0.06, 0.02, 0.03)
    )
    assign_material(glass_l, mats["glasses"])
    assign_material(glass_r, mats["glasses"])
    assign_material(bridge, mats["glasses"])
    parts.extend([glass_l, glass_r, bridge])

    # Earring
    earring = add_cylinder(
        "Earring",
        location=(-0.63, 0.0, 1.46),
        radius=0.055,
        depth=0.02,
        rotation=(math.radians(90), 0, 0)
    )
    assign_material(earring, mats["earring"])
    parts.append(earring)

    # Slight stylization
    for obj in parts:
        shade_smooth(obj)

    print("Character created.")
    return parts


# ============================================================
# CAMERA / LIGHTS
# ============================================================
def setup_camera():
    print("Setting up camera...")
    cam_data = bpy.data.cameras.new("Camera")
    cam = bpy.data.objects.new("Camera", cam_data)
    collection.objects.link(cam)

    cam.location = (0.0, -5.4, 1.15)
    cam.rotation_euler = Euler((math.radians(86.5), 0.0, 0.0), 'XYZ')
    cam.data.lens = 52
    cam.data.sensor_width = 36
    scene.camera = cam
    print("Camera ready.")
    return cam


def add_area_light(name, location, rotation, energy=3000, size=2.0):
    light_data = bpy.data.lights.new(name=name, type='AREA')
    light_data.energy = energy
    light_data.shape = 'RECTANGLE'
    light_data.size = size
    light_data.size_y = size

    light = bpy.data.objects.new(name, light_data)
    collection.objects.link(light)
    light.location = location
    light.rotation_euler = rotation
    return light


def setup_lights():
    print("Setting up lights...")

    key = add_area_light(
        "Key_Light",
        location=(-2.6, -3.2, 3.8),
        rotation=(math.radians(62), 0, math.radians(28)),
        energy=4200,
        size=3.0
    )

    fill = add_area_light(
        "Fill_Light",
        location=(2.5, -2.5, 2.0),
        rotation=(math.radians(74), 0, math.radians(-35)),
        energy=1600,
        size=3.2
    )

    rim = add_area_light(
        "Rim_Light",
        location=(0.0, 2.4, 2.8),
        rotation=(math.radians(-95), 0, 0),
        energy=2400,
        size=2.5
    )

    return [key, fill, rim]


# ============================================================
# RENDER SETTINGS
# ============================================================
def setup_render():
    print("Setting up render settings...")

    scene.render.engine = 'CYCLES'
    scene.cycles.device = 'CPU'
    scene.cycles.samples = 96
    scene.cycles.preview_samples = 24
    scene.cycles.use_adaptive_sampling = True
    scene.cycles.max_bounces = 6
    scene.cycles.diffuse_bounces = 2
    scene.cycles.glossy_bounces = 2
    scene.cycles.transmission_bounces = 2
    scene.cycles.transparent_max_bounces = 4

    scene.render.resolution_x = 1024
    scene.render.resolution_y = 1024
    scene.render.resolution_percentage = 100
    scene.render.film_transparent = False

    scene.render.image_settings.file_format = 'PNG'
    scene.render.image_settings.color_mode = 'RGBA'
    scene.render.image_settings.compression = 15
    scene.render.filepath = PNG_PATH

    scene.view_settings.look = 'None'
    scene.view_settings.exposure = 0.0
    scene.view_settings.gamma = 1.0

    print("Render settings ready.")


# ============================================================
# COMPOSITOR
# ============================================================
def setup_compositor(scene_obj) -> None:
    print("Setting up compositor...")

    if scene_obj is None:
        raise RuntimeError("No active Blender scene found")

    scene_obj.use_nodes = True

    comp_tree = scene_obj.node_tree
    if comp_tree is None:
        raise RuntimeError("Scene node tree is unavailable")

    comp_nodes = comp_tree.nodes
    comp_links = comp_tree.links
    comp_nodes.clear()

    rl = comp_nodes.new(type='CompositorNodeRLayers')
    rl.location = (-400, 0)
    last_image_out = rl.outputs['Image']

    try:
        glare = comp_nodes.new(type='CompositorNodeGlare')
        glare.location = (-100, 0)
        glare.glare_type = 'FOG_GLOW'
        glare.quality = 'HIGH'
        glare.threshold = 0.85
        glare.size = 7
        comp_links.new(last_image_out, glare.inputs['Image'])
        last_image_out = glare.outputs['Image']
        print("Glare: OK")
    except Exception as e:
        print(f"Glare skipped: {e}")

    try:
        lens = comp_nodes.new(type='CompositorNodeLensdist')
        lens.location = (150, 0)
        lens.inputs[1].default_value = -0.015
        lens.inputs[2].default_value = 0.004
        comp_links.new(last_image_out, lens.inputs['Image'])
        last_image_out = lens.outputs['Image']
        print("Lens distortion: OK")
    except Exception as e:
        print(f"Lens distortion skipped: {e}")

    try:
        cb = comp_nodes.new(type='CompositorNodeColorBalance')
        cb.location = (400, 0)
        cb.correction_method = 'LIFT_GAMMA_GAIN'
        cb.lift = (0.96, 0.97, 1.02, 1.0)
        cb.gamma = (1.02, 1.00, 0.97, 1.0)
        cb.gain = (1.05, 1.02, 0.95, 1.0)
        comp_links.new(last_image_out, cb.inputs['Image'])
        last_image_out = cb.outputs['Image']
        print("Color balance: OK")
    except Exception as e:
        print(f"Color balance skipped: {e}")

    try:
        ellipse = comp_nodes.new(type='CompositorNodeEllipseMask')
        ellipse.location = (150, -250)
        ellipse.width = 0.85
        ellipse.height = 0.85

        blur_vig = comp_nodes.new(type='CompositorNodeBlur')
        blur_vig.location = (350, -250)
        blur_vig.size_x = 120
        blur_vig.size_y = 120

        comp_links.new(ellipse.outputs['Mask'], blur_vig.inputs['Image'])

        mix_vig = comp_nodes.new(type='CompositorNodeMixRGB')
        mix_vig.location = (600, 0)
        mix_vig.blend_type = 'MULTIPLY'
        mix_vig.inputs[0].default_value = 0.55

        comp_links.new(last_image_out, mix_vig.inputs[1])
        comp_links.new(blur_vig.outputs['Image'], mix_vig.inputs[2])
        last_image_out = mix_vig.outputs['Image']
        print("Vignette: OK")
    except Exception as e:
        print(f"Vignette skipped: {e}")

    comp_out = comp_nodes.new(type='CompositorNodeComposite')
    comp_out.location = (850, 0)
    comp_links.new(last_image_out, comp_out.inputs['Image'])

    try:
        viewer = comp_nodes.new(type='CompositorNodeViewer')
        viewer.location = (850, -150)
        comp_links.new(last_image_out, viewer.inputs['Image'])
        print("Viewer: OK")
    except Exception as e:
        print(f"Viewer skipped: {e}")

    print("Compositor configured.")


# ============================================================
# EXPORTS
# ============================================================
def save_outputs():
    print("Saving outputs...")

    print(f"Render target: {PNG_PATH}")
    bpy.ops.render.render(write_still=True)
    print("PNG render finished.")

    bpy.ops.wm.save_as_mainfile(filepath=BLEND_PATH)
    print("BLEND saved.")

    try:
        bpy.ops.export_scene.gltf(
            filepath=GLB_PATH,
            export_format='GLB',
            use_selection=False
        )
        print("GLB exported.")
    except Exception as e:
        print(f"GLB export failed (non-fatal): {e}")

    print(f"PNG exists:   {os.path.exists(PNG_PATH)}")
    print(f"BLEND exists: {os.path.exists(BLEND_PATH)}")
    print(f"GLB exists:   {os.path.exists(GLB_PATH)}")


# ============================================================
# MAIN
# ============================================================
def main():
    clear_scene()
    ensure_world()
    mats = create_materials()
    create_background(mats)
    create_character(mats)
    setup_camera()
    setup_lights()
    setup_render()

    try:
        setup_compositor(scene)
    except Exception as e:
        print(f"Compositor failed entirely (non-fatal): {e}")
        if scene is not None:
            scene.use_nodes = False

    save_outputs()

    if not os.path.exists(PNG_PATH):
        raise RuntimeError("Render completed but PNG file was not generated at expected path")

    print("Pipeline complete.")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print("FATAL ERROR in cryptopunk_3d.py")
        print(str(e))
        traceback.print_exc()
        raise
