# CryptoPunk 3D Voxel Render Pipeline

Automated 3D rendering pipeline using **Blender + GitHub Actions**.

## Output Files

| File | Use |
|------|-----|
| `cryptopunk_3d_render.png` | 2048×2048 cinematic render |
| `cryptopunk_iphone.usdz` | **iPhone AR** — tap in Files app |
| `cryptopunk_scene.blend` | Edit in Blender desktop |
| `cryptopunk_scene.glb` | Web 3D viewers, model-viewer |

## How to View on iPhone in AR

1. Download **cryptopunk-iphone-AR-usdz** from Actions > Artifacts
2. AirDrop or save to iCloud Drive
3. Tap the `.usdz` file in the **Files app**
4. Tap the **AR button** (cube icon)
5. Point camera at floor → your CryptoPunk appears in your room! 🚀

## How to Trigger

- **Auto**: Push to `main`
- **Manual**: Actions tab → Run workflow

## Settings

| Property | Value |
|----------|-------|
| Engine | Cycles (CPU) |
| Resolution | 2048 × 2048 |
| Samples | 128 + Denoiser |
| Runner | ubuntu-22.04 |
| Blender | 4.1.1 |
