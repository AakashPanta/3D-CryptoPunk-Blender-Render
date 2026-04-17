# CryptoPunk 3D Character Render Pipeline

Premium stylized 3D character rendered via **Blender + GitHub Actions**.

## Output Files

| File | Use |
|------|-----|
| `cryptopunk_character_render.png` | 2048×2048 cinematic render |
| `cryptopunk_character.usdz` | iPhone AR — tap in Files app |
| `cryptopunk_character.blend` | Edit in Blender desktop |
| `cryptopunk_character.glb` | Web 3D viewers |

## How to Get the Files

1. Go to **Actions** tab
2. Click the latest workflow run
3. Download from **Artifacts** section at the bottom

## iPhone AR Instructions

1. Download `character-iPhone-AR-USDZ` from Artifacts
2. AirDrop or iCloud Drive to your iPhone
3. Tap the `.usdz` file in the **Files app**
4. Tap the **AR cube icon** (bottom right corner)
5. Point camera at floor — character appears in your room!

## View GLB in Browser

1. Download `character-web-GLB` from Artifacts
2. Go to [gltf.report](https://gltf.report)
3. Drop the `.glb` file to view in 3D

## Manual Trigger

Go to **Actions** tab → **3D CryptoPunk Character Render** → **Run workflow**

## Render Settings

| Setting | Value |
|---------|-------|
| Engine | Cycles (CPU) |
| Resolution | 2048 × 2048 |
| Samples | 256 + OIDN Denoiser |
| Camera | 85mm f/1.8 Portrait |
| Post FX | Bloom + Vignette + Color Grade |
| Runner | ubuntu-22.04 |
| Blender | 4.1.1 (cached) |
