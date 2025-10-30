import os;
import tempfile;
import unittest;
from PIL import Image;
from constants import STRETCH;
from asciiartimage import AsciiArtImage;
from session import Session;


class TestAsciiArtStudio(unittest.TestCase):
    def setUp(self):
        # Skapa en temporär gråskale-bild (80x60) för testerna;
        self.tmpdir = tempfile.TemporaryDirectory();
        self.img_path = os.path.join(self.tmpdir.name, "test.png");
        img = Image.new("L", (80, 60), color=128);
        img.save(self.img_path);

    def tearDown(self):
        self.tmpdir.cleanup();

    def test_height_from_width(self):
        a = AsciiArtImage(self.img_path);
        a.load();
        a.set_width(50);
        expected = max(1, int(round(50 * (60 / 80) * STRETCH)));
        self.assertEqual(a.height, expected);

    def test_width_from_height(self):
        a = AsciiArtImage(self.img_path);
        a.load();
        a.set_height(20);
        # height ≈ width * (h/w)*STRETCH  → width ≈ height / ((h/w)*STRETCH)
        expected = max(1, int(round(20 / ((60 / 80) * STRETCH))));
        self.assertEqual(a.width, expected);

    def test_brightness_validation(self):
        a = AsciiArtImage(self.img_path);
        a.load();
        with self.assertRaises(ValueError):
            a.set_brightness(0);

    def test_render_line_count(self):
        a = AsciiArtImage(self.img_path);
        a.load();
        a.set_width(40);
        art = a.render_to_string();
        lines = art.splitlines();
        self.assertEqual(len(lines), a.height);

    def test_session_save_load_roundtrip(self):
        s1 = Session();
        img = s1.add_image(self.img_path, alias="test");
        img.set_width(42);
        img.set_brightness(1.2);
        tmp_json = os.path.join(self.tmpdir.name, "sess.json");
        s1.save_session(tmp_json);

        s2 = Session();
        s2.load_session(tmp_json);
        self.assertIn("test", s2.images);
        img2 = s2.images["test"];
        self.assertEqual(img2.width, 42);
        self.assertAlmostEqual(img2.brightness, 1.2, places=6);


if __name__ == "__main__":
    unittest.main(verbosity=2);
