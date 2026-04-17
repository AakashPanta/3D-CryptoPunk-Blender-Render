<div align="center">

# CryptoPunk 3D

**Automated cinematic 3D character rendering pipeline powered by Blender and GitHub Actions.**

Transform a stylized character concept into a premium 3D render, an iPhone AR experience,
and a web-ready 3D model — fully automated on every push.

[![CI Status](https://github.com/YOUR_USERNAME/YOUR_REPO/actions/workflows/render-character.yml/badge.svg)](https://github.com/YOUR_USERNAME/YOUR_REPO/actions/workflows/render-character.yml)
[![Blender](https://img.shields.io/badge/Blender-4.1.1-orange?logo=blender&logoColor=white)](https://www.blender.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/Runner-ubuntu--22.04-lightgrey?logo=github)](https://github.com/features/actions)

</div>

---

## Overview

CryptoPunk 3D is a fully automated rendering pipeline that builds a premium stylized
3D character scene entirely in code — no manual Blender work required.

Push to `main` and GitHub Actions will:

- Build the full 3D scene from scratch using a Python script
- Render a **2048×2048 cinematic portrait** with Cycles + OIDN denoising
- Export an **iPhone-ready `.usdz`** file for real-world AR placement
- Export a **`.glb`** file for interactive web 3D viewing
- Upload all outputs as downloadable **build artifacts**

> Built for developers, 3D artists, and NFT creators who want a reproducible,
> version-controlled 3D render pipeline with zero manual steps.

---

## Output Files

| Artifact | Format | Use |
|----------|--------|-----|
| `cryptopunk_character_render.png` | PNG | 2048×2048 cinematic render |
| `cryptopunk_character.usdz` | USDZ | iPhone AR via Files app |
| `cryptopunk_character.blend` | BLEND | Edit in Blender desktop |
| `cryptopunk_character.glb` | GLB | Web 3D viewers & model-viewer |

---

## Features

**Rendering**
- Cycles CPU rendering at 2048×2048 resolution
- 256 samples with OpenImageDenoise (OIDN) denoiser
- 85mm portrait camera at f/1.8 with shallow depth of field
- Filmic color management with High Contrast look

**Scene & Character**
- Full stylized 3D character built procedurally in Python
- Multi-layer eyes with cornea, iris, and pupil geometry
- Subsurface scattering skin with warm SSS color
- Layered clothing: green open shirt over white undershirt
- Props: red lighter with chrome top, active flame, cigarette, curling smoke
- Blue/white striped wristband and black earring stud

**Lighting**
- 6-light cinematic rig: key, rim, fill, top, flame practical, cigarette glow
- Warm urban key light + cool blue-purple rim light
- Emissive bokeh spheres simulating city background lights

**Post Processing**
- Compositor: FOG_GLOW bloom on emissive elements
- Subtle lens distortion for cinematic feel
- Lift/Gamma/Gain color grade (warm highlights, cool shadows)
- Ellipse mask vignette with soft blur

**Exports**
- `.blend` scene file saved before render
- `.glb` via Blender's native glTF exporter
- `.usdz` via native USD export with zip fallback

---

## Render Settings

| Setting | Value |
|---------|-------|
| Engine | Cycles (CPU) |
| Resolution | 2048 × 2048 |
| Samples | 256 |
| Denoiser | OpenImageDenoise (OIDN) |
| Camera | 85mm · f/1.8 · Portrait |
| Color | Filmic · High Contrast |
| Post FX | Bloom · Vignette · Color Grade |
| Blender | 4.1.1 |
| Runner | ubuntu-22.04 |

---

## Getting Started

### Prerequisites

- A GitHub account with Actions enabled
- No local Blender installation required — CI handles everything

### Setup

```bash
# 1. Clone or fork this repository
git clone https://github.com/YOUR_USERNAME/YOUR_REPO.git
cd YOUR_REPO

# 2. Push to main to trigger the pipeline
git push origin main
```

The workflow runs automatically on every push to `main`.

### Manual Trigger

1. Go to the **Actions** tab in your repository
2. Select **3D CryptoPunk Character Render**
3. Click **Run workflow** → **Run workflow**

---

## Downloading the Outputs

1. Go to the **Actions** tab
2. Click the latest completed workflow run
3. Scroll to the **Artifacts** section at the bottom
4. Download any of the following:

| Artifact Name | Contents |
|---------------|----------|
| `character-render-PNG` | Final rendered image |
| `character-iPhone-AR-USDZ` | AR file for iPhone |
| `character-blender-scene` | Editable `.blend` file |
| `character-web-GLB` | 3D model for web viewers |
| `all-outputs-bundle` | All files in one ZIP |

---

## iPhone AR Walkthrough

Place the character in your real environment using Apple's AR Quick Look.

```
1. Download  →  character-iPhone-AR-USDZ  from Artifacts
2. Transfer  →  AirDrop or save to iCloud Drive
3. Open      →  Tap the .usdz file in the Files app
4. View AR   →  Tap the AR cube icon (bottom right)
5. Place     →  Point camera at floor — character appears at real scale
```

> Requires iOS 12+ or iPadOS 12+. No app installation needed.

---

## View GLB in Browser

```
1. Download  →  character-web-GLB  from Artifacts
2. Open      →  gltf.report  or  modelviewer.dev/editor
3. Drop      →  Drag the .glb file into the viewer
```

---

## Project Structure

```
├── .github/
│   └── workflows/
│       └── render-character.yml   # CI pipeline definition
│
├── scripts/
│   └── cryptopunk_3d.py           # Full Blender scene + render script
│
├── output/
│   └── .gitkeep                   # Placeholder — outputs generated by CI
│
├── .gitignore
└── README.md
```

---

## How It Works

```
git push
    │
    ▼
GitHub Actions (ubuntu-22.04)
    │
    ├── Cache check → Download Blender 4.1.1 if needed
    ├── Install system OpenGL / display libraries
    ├── Start Xvfb virtual display (1920×1080)
    │
    ▼
Blender --background --python scripts/cryptopunk_3d.py
    │
    ├── Clean scene
    ├── Create 25 materials (SSS skin, emissive flame, glass cornea...)
    ├── Build character geometry (head, eyes, cap, torso, arms, props)
    ├── Place environment (background plane, floor, bokeh lights)
    ├── Configure 6-light cinematic rig
    ├── Set up 85mm portrait camera with DOF
    ├── Configure Cycles render settings
    ├── Build compositor (bloom, vignette, color grade)
    ├── Save .blend file
    ├── Export .glb
    ├── Export .usdz (with zip fallback)
    └── Render PNG → write_still=True
    │
    ▼
Upload Artifacts
    ├── character-render-PNG
    ├── character-iPhone-AR-USDZ
    ├── character-blender-scene
    ├── character-web-GLB
    └── all-outputs-bundle
```

---

## Customization

All scene parameters are defined at the top of `scripts/cryptopunk_3d.py`.

**Change render quality**
```python
scene.cycles.samples = 128        # Lower = faster, Higher = better quality
scene.render.resolution_x = 1024  # Output resolution
scene.render.resolution_y = 1024
```

**Change camera framing**
```python
camera.data.lens               = 85   # Focal length in mm
camera.data.dof.aperture_fstop = 1.8  # Aperture — lower = more blur
camera.data.dof.focus_distance = 2.8  # Focus distance in meters
```

**Change lighting mood**
```python
key.data.color  = (1.0, 0.88, 0.72)  # Warm key light
rim.data.color  = (0.45, 0.55, 1.0)  # Cool rim light
key.data.energy = 180                 # Light intensity
```

**Change skin color**
```python
M_SKIN = make_mat('Skin',
    base_color=(0.91, 0.73, 0.56),   # RGB base color
    subsurface=0.35,                  # SSS intensity
    subsurface_color=(0.95, 0.60, 0.45))
```

---

## CI Performance

| Stage | Typical Duration |
|-------|-----------------|
| Blender download (first run) | ~3–5 min |
| Blender load from cache | ~30 sec |
| Dependency install | ~1–2 min |
| Scene build | ~1 min |
| Render (256 samples, 2048²) | ~15–25 min |
| Export + upload | ~1–2 min |
| **Total (cached)** | **~20–30 min** |

> Blender is cached after the first run using `actions/cache@v4`.
> Subsequent runs skip the download entirely.

---

## Roadmap

- [ ] Animated turntable render (360° rotation)
- [ ] Multiple character variants via workflow inputs
- [ ] Background HDRI environment support
- [ ] Automatic GitHub Release attachment on tag push
- [ ] Web viewer embedded in README via model-viewer
- [ ] GPU rendering support (self-hosted runner)

---

## Contributing

Contributions are welcome.

```bash
# Fork the repository
# Create a feature branch
git checkout -b feature/your-improvement

# Make your changes to scripts/cryptopunk_3d.py
# Test locally if you have Blender installed:
blender --background --python scripts/cryptopunk_3d.py -- --output-dir ./output

# Push and open a pull request
git push origin feature/your-improvement
```

Please keep pull requests focused on a single change.
Include a brief description of what was changed and why.

---

## License

MIT License — see [LICENSE](LICENSE) for details.

---

<div align="center">

Built with [Blender](https://www.blender.org/) · Automated with [GitHub Actions](https://github.com/features/actions)

</div>
