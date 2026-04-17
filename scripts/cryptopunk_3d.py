# ============================================================
# COMPOSITOR
# ============================================================
print("Setting up compositor...")

try:
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

    try:
        lens = comp_nodes.new('CompositorNodeLensdist')
        lens.location = (150, 0)
        lens.inputs[1].default_value = -0.015
        lens.inputs[2].default_value =  0.004
        comp_links.new(glare.outputs['Image'], lens.inputs['Image'])
        last_image_out = lens.outputs['Image']
        print("Lens distortion: OK")
    except Exception as e:
        print(f"Lens distortion skipped: {e}")
        last_image_out = glare.outputs['Image']

    try:
        cb = comp_nodes.new('CompositorNodeColorBalance')
        cb.location          = (400, 0)
        cb.correction_method = 'LIFT_GAMMA_GAIN'
        cb.lift  = (0.96, 0.97, 1.02, 1.0)
        cb.gamma = (1.02, 1.00, 0.97, 1.0)
        cb.gain  = (1.05, 1.02, 0.95, 1.0)
        comp_links.new(last_image_out, cb.inputs['Image'])
        last_image_out = cb.outputs['Image']
        print("Color balance: OK")
    except Exception as e:
        print(f"Color balance skipped: {e}")

    try:
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
        comp_links.new(last_image_out,            mix_vig.inputs[1])
        comp_links.new(blur_vig.outputs['Image'], mix_vig.inputs[2])
        last_image_out = mix_vig.outputs['Image']
        print("Vignette: OK")
    except Exception as e:
        print(f"Vignette skipped: {e}")

    comp_out = comp_nodes.new('CompositorNodeComposite')
    comp_out.location = (850, 0)
    comp_links.new(last_image_out, comp_out.inputs['Image'])

    viewer = comp_nodes.new('CompositorNodeViewer')
    viewer.location = (850, -150)
    comp_links.new(last_image_out, viewer.inputs['Image'])

    print("Compositor configured")

except Exception as e:
    print(f"Compositor failed entirely (non-fatal): {e}")
    print("Continuing without compositor...")
    scene.use_nodes = False
