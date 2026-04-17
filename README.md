# 🎮 CryptoPunk 3D Voxel Render Pipeline

Automated 3D rendering pipeline using **Blender + GitHub Actions**.

Transforms a pixel art CryptoPunk character into a premium 3D voxel sculpture
with cinematic lighting, rendered entirely in CI/CD.

## 🚀 How It Works

1. Push to `main` → GitHub Actions triggers
2. Blender 4.1 is downloaded & cached
3. Python script builds the 3D scene from scratch
4. Cycles renders at 2048×2048 with 128 samples
5. PNG render + `.blend` file uploaded as artifacts

## 📥 Get the Render

1. Go to **Actions** tab
2. Click the latest workflow run
3. Download from **Artifacts** section:
   - `cryptopunk-3d-render` — Final PNG image
   - `cryptopunk-3d-blend-file` — Editable Blender file

## 🖱️ Manual Trigger

Go to **Actions** → **3D CryptoPunk Blender Render** → **Run workflow**

## 🛠️ Customization

Edit `scripts/cryptopunk_3d.py` to modify:
- Resolution, samples, camera angle
- Materials and colors
- Lighting setup
- Character pixel map

## ⏱️ Performance

| Setting | Value |
|---------|-------|
| Render Engine | Cycles (CPU) |
| Resolution | 2048 × 2048 |
| Samples | 128 + Denoising |
| Typical CI Time | ~8-15 minutes |
| Blender Version | 4.1.1 (cached) |
