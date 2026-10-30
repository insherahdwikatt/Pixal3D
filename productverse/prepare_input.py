"""ProductVerse photo framing for Pixal3D (Pillow-only, CPU-only).

Opt-in preprocessing. Does not generate 3D, remove complex backgrounds,
or promise better model geometry. Keeps the source image unchanged.
"""
from __future__ import annotations

import argparse
from pathlib import Path
from PIL import Image, ImageChops, ImageOps

MAX_PIXELS = 30_000_000


def _uniform_border_bbox(rgb: Image.Image, threshold: int = 30):
    """Conservatively estimate a subject rectangle on a near-uniform backdrop."""
    w, h = rgb.size
    points = ((0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1))
    colors = [rgb.getpixel(p) for p in points]
    backdrop = tuple(round(sum(c[k] for c in colors) / 4) for k in range(3))
    # Mixed corner colors imply a cluttered/inconsistent backdrop: don't guess.
    if max(abs(c[k] - backdrop[k]) for c in colors for k in range(3)) > threshold:
        return None, None
    solid = Image.new("RGB", (w, h), backdrop)
    difference = ImageChops.difference(rgb, solid).convert("L")
    mask = difference.point(lambda v: 255 if v >= threshold else 0)
    bbox = mask.getbbox()
    if bbox is None:
        return None, None
    left, top, right, bottom = bbox
    width_fraction = (right - left) / w
    height_fraction = (bottom - top) / h
    # Don't over-crop unrecognizable images or almost-empty photos.
    if min(width_fraction, height_fraction) < 0.07:
        return None, None
    return bbox, backdrop


def prepare_product_image(image: Image.Image, *, size: int = 1024,
                          margin: float = 0.12, mode: str = "auto") -> Image.Image:
    """Return centered square RGBA image for optional Pixal3D input prep.

    Modes: 'auto' uses the existing alpha mask when present; otherwise it
    trims a nearly uniform corner background. 'alpha' trims only existing
    transparency. 'none' preserves the full rectangular image when framing.
    Backdrop pixels are never deleted in auto mode: this is *cropping*, not
    semantic background removal.
    """
    if not 256 <= size <= 2048:
        raise ValueError("size must be between 256 and 2048")
    if not 0 <= margin <= 0.35:
        raise ValueError("margin must be in [0, 0.35]")
    if mode not in ("auto", "alpha", "none"):
        raise ValueError("mode must be auto, alpha or none")
    if image.width < 2 or image.height < 2 or image.width * image.height > MAX_PIXELS:
        raise ValueError("Unsupported image dimensions")
    src = ImageOps.exif_transpose(image).convert("RGBA")
    w, h = src.size
    alpha = src.getchannel("A")
    has_transparency = alpha.getextrema()[0] < 240

    background = (255, 255, 255, 0) if has_transparency else (255, 255, 255, 255)
    bbox = None
    if mode != "none" and has_transparency:
        bbox = alpha.point(lambda v: 255 if v >= 16 else 0).getbbox()
    elif mode == "auto":
        bbox, bg = _uniform_border_bbox(src.convert("RGB"))
        if bg is not None:
            background = (*bg, 255)
    if bbox is None:
        bbox = (0, 0, w, h)
        if not has_transparency:
            # Use corner color to avoid artificial white seams for no-crop photos.
            background = (*src.getpixel((0, 0))[:3], 255)

    crop = src.crop(bbox)
    available = max(1, round(size * (1 - 2 * margin)))
    scale = min(available / crop.width, available / crop.height)
    new_w = max(1, round(crop.width * scale))
    new_h = max(1, round(crop.height * scale))
    crop = crop.resize((new_w, new_h), Image.Resampling.LANCZOS)

    canvas = Image.new("RGBA", (size, size), background)
    x, y = (size - new_w) // 2, (size - new_h) // 2
    # Composite transparent inputs; opaque images remain opaque.
    canvas.alpha_composite(crop, (x, y))
    return canvas


def main(argv=None):
    parser = argparse.ArgumentParser(description="CPU-only ProductVerse photo preparation")
    parser.add_argument("--input", required=True, type=Path, help="Original product photo")
    parser.add_argument("--output", required=True, type=Path, help="Prepared PNG path")
    parser.add_argument("--size", type=int, default=1024)
    parser.add_argument("--margin", type=float, default=0.12)
    parser.add_argument("--mode", choices=["auto", "alpha", "none"], default="auto")
    args = parser.parse_args(argv)
    if args.input.resolve() == args.output.resolve():
        parser.error("Output must be different from the source image.")
    with Image.open(args.input) as photo:
        prepared = prepare_product_image(photo, size=args.size, margin=args.margin, mode=args.mode)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    prepared.save(args.output, format="PNG")
    print(f"Saved {prepared.size[0]}x{prepared.size[1]} preview to {args.output}")


if __name__ == "__main__":
    main()
