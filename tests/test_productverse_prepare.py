import tempfile
import unittest
from pathlib import Path

from PIL import Image, ImageDraw
from productverse.prepare_input import prepare_product_image, main


class PrepareInputTest(unittest.TestCase):
    def test_uniform_white_background_centers_product(self):
        src = Image.new("RGB", (240, 140), "white")
        ImageDraw.Draw(src).rectangle((80, 35, 160, 105), fill=(30, 80, 150))
        out = prepare_product_image(src, size=512, margin=0.15)
        self.assertEqual(out.size, (512, 512))
        self.assertEqual(out.mode, "RGBA")
        self.assertEqual(src.size, (240, 140))
        self.assertEqual(src.getpixel((0, 0)), (255, 255, 255))
        # Centered geometry and white canvas, no geometric distortion.
        self.assertEqual(out.getpixel((256, 256))[:3], (30, 80, 150))
        self.assertEqual(out.getpixel((0, 0))[:3], (255, 255, 255))

    def test_existing_alpha_crop_preserves_transparency(self):
        src = Image.new("RGBA", (200, 130), (0, 0, 0, 0))
        ImageDraw.Draw(src).rectangle((70, 35, 129, 94), fill=(220, 20, 20, 255))
        out = prepare_product_image(src, size=512)
        self.assertEqual(out.getpixel((0, 0))[3], 0)
        self.assertEqual(out.getpixel((256, 256)), (220, 20, 20, 255))

    def test_no_trim_mode_preserves_full_photo_composition(self):
        src = Image.new("RGB", (400, 100), (45, 90, 130))
        a = prepare_product_image(src, size=512, mode="none", margin=0)
        self.assertEqual(a.size, (512, 512))
        self.assertEqual(a.getpixel((256, 256))[:3], (45, 90, 130))

    def test_nonuniform_edges_do_not_get_trimmed(self):
        src = Image.new("RGB", (240, 160), "white")
        ImageDraw.Draw(src).rectangle((0, 0, 40, 50), fill=(220, 10, 20))
        output = prepare_product_image(src, size=512, mode="auto")
        self.assertEqual(output.getpixel((256, 256))[:3], (255, 255, 255))
        self.assertEqual(src.size, (240, 160))

    def test_input_rejections(self):
        image = Image.new("RGB", (64, 64))
        for kwargs in ({"margin": -0.2}, {"margin": 0.5}, {"size": 12}, {"mode": "unknown"}):
            with self.assertRaises(ValueError):
                prepare_product_image(image, **kwargs)

    def test_cli_saves_png_without_overwriting_source(self):
        with tempfile.TemporaryDirectory() as folder:
            src = Path(folder) / "product.jpg"
            output = Path(folder) / "nested" / "prepared.png"
            Image.new("RGB", (160, 120), "white").save(src)
            main(["--input", str(src), "--output", str(output), "--size", "512"])
            self.assertTrue(src.exists())
            self.assertTrue(output.exists())
            with Image.open(output) as result:
                self.assertEqual(result.size, (512, 512))
                self.assertEqual(result.format, "PNG")

    def test_cli_never_overwrites_source(self):
        with tempfile.TemporaryDirectory() as folder:
            src = Path(folder) / "photo.png"
            Image.new("RGBA", (128, 128), "white").save(src)
            with self.assertRaises(SystemExit):
                main(["--input", str(src), "--output", str(src)])


if __name__ == "__main__":
    unittest.main()
