# ProductVerse customizations for Pixal3D

This fork retains upstream Pixal3D code, assets, LICENSE, and NOTICE. ProductVerse experiments live in opt-in utilities instead of replacing the model pipeline.

## First customization: conservative product-photo framing

The `productverse.prepare_input` module runs locally with **Pillow only** (no CUDA, model download, cloud service or API). It can create a square, centered PNG from a product photo.

On Windows, in a clone/download of this **Pixal3D fork**:

```powershell
py -m pip install Pillow==12.0.0
py -m productverse.prepare_input --input "my-motor.jpg" --output "motor-prepared.png" --size 1024
```

The input image is not overwritten. The prepared image appears in the same folder you selected for output. Additional options:

- `--mode auto` (default): trim uniform light/dark borders **when the four corners are similar**; use alpha if already present; otherwise preserve the full photograph.
- `--mode alpha`: trim existing transparent alpha only, otherwise preserve the full photo.
- `--mode none`: preserve original framing; only fit and pad into a square.
- `--margin 0.12`: add 12% margin per side; accepts 0–0.35.
- `--size 1024`: output 1024 x 1024 PNG; valid 256–2048.

You can compare original vs prepared using ordinary image viewer **without running inference**.

### Use during Pixal3D inference (GPU required)

```bash
python inference.py --image my-motor.jpg --output motor.glb --pv_prep
# or, for low-VRAM servers with sufficient GPU RAM:
python inference.py --image my-motor.jpg --output motor.glb --low_vram --pv_prep --pv_prep_mode alpha
```

The original upstream behavior is **unchanged** unless `--pv_prep` is explicitly supplied. Optional image framing occurs just before the original pipeline's `preprocess_image`; upstream background segmentation, camera estimation and GLB generation are otherwise unchanged.

### Limitations

- This is **heuristic crop/pad**, NOT semantic background removal or generative model fine-tuning. It does not repair geometry, metal roughness, lighting, or occluded parts.
- A white product on a white background, logos, shadows, text, reflections, or uneven backgrounds can make automatic bounding-box detection inaccurate. Compare previews. Use `--mode alpha` or `--mode none` when the result is wrong.
- It does not know camera intrinsics. Cropping can alter perceived field-of-view and thus **might make model output worse**. Always compare A/B on identical seeds, source images and settings.
- Pixal3D inference itself requires supported Linux/CUDA GPU hardware. A 2 GB MX450 is not sufficient for published low-VRAM configuration (~10–12 GB).
- The official Hugging Face demo being offline does not mean the weights or source are unavailable; model inference was **not** executed as part of this change.

### Offline tests

```bash
python -m pip install Pillow==12.0.0
python -m unittest discover -s tests -p 'test_productverse_prepare.py' -v
```

Tests also run on GitHub Actions CPU. They require no API key, GPU, model weights, or external generation.

### Next experiments

1. Save prepared images and compare against original inputs on the same real object photo.
2. Measure GLB file size, silhouette and missing parts using ProductVerse Quality Review.
3. Add optional postprocess for GLB export after confirming a stable GPU inference environment.
4. Only consider fine-tuning with legally licensed paired image/3D datasets.

Do not commit Hugging Face credentials, model weights, user photos, or generated private files to this public fork.
