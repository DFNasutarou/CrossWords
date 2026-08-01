import unittest

from app.lib.crosswordlib.inline_images import (
    BLACKOUT_NONE,
    BLACKOUT_OPAQUE,
    InlineImageError,
    create_image_asset,
    create_inline_image,
    normalize_image_assets,
    normalize_inline_image,
    normalize_inline_images,
    pack_text_content,
    resolve_asset_path,
    unpack_text_content,
)


class InlineImagesTest(unittest.TestCase):
    def test_creates_relative_asset_reference(self):
        asset_id, asset = create_image_asset(
            "sample.png",
            "picture/inline/sample.png",
            320,
            160,
        )

        self.assertTrue(asset_id)
        self.assertEqual(asset["name"], "sample.png")
        self.assertEqual(asset["path"], "picture/inline/sample.png")
        self.assertEqual((asset["width"], asset["height"]), (320, 160))

    def test_rejects_empty_asset_path(self):
        with self.assertRaises(InlineImageError):
            create_image_asset("empty.png", "", 10, 10)

    def test_clamps_position_and_display_size(self):
        image = normalize_inline_image(
            {
                "asset_id": "asset",
                "position": 99,
                "width": 2,
                "height": 9999,
                "blackout": BLACKOUT_OPAQUE,
            },
            text_length=8,
        )

        self.assertEqual(image["position"], 8)
        self.assertEqual(image["width"], 8)
        self.assertEqual(image["height"], 800)
        self.assertEqual(image["blackout"], BLACKOUT_OPAQUE)

    def test_unknown_blackout_mode_becomes_none(self):
        image = create_inline_image("asset", 2, 80, 40, "unknown")

        self.assertEqual(image["blackout"], BLACKOUT_NONE)

    def test_line_break_flag_round_trip(self):
        # 旧データ（フラグ無し）は False、指定すれば保持される
        legacy = normalize_inline_image({"asset_id": "asset"})
        with_break = create_inline_image(
            "asset", 0, 80, 40, line_break=True
        )
        renormalized = normalize_inline_image(with_break)

        self.assertFalse(legacy["line_break"])
        self.assertTrue(with_break["line_break"])
        self.assertTrue(renormalized["line_break"])

    def test_skips_invalid_entries_and_sorts_by_position(self):
        images = normalize_inline_images(
            [
                {"asset_id": "second", "position": 4},
                "invalid",
                {"asset_id": "first", "position": 1},
            ],
            text_length=5,
        )

        self.assertEqual(
            [image["asset_id"] for image in images],
            ["first", "second"],
        )

    def test_normalizes_asset_dictionary(self):
        assets = normalize_image_assets(
            {
                "ok": {
                    "name": "x.png",
                    "path": "picture/inline/x.png",
                    "width": 20,
                    "height": 10,
                },
                "bad": {"name": "missing data"},
            }
        )

        self.assertEqual(list(assets), ["ok"])
        self.assertEqual(assets["ok"]["mime_type"], "image/png")

    def test_resolves_path_inside_project(self):
        resolved = resolve_asset_path(
            "C:/projects/example",
            "picture/inline/x.png",
        )

        self.assertTrue(
            resolved.replace("\\", "/").endswith(
                "/projects/example/picture/inline/x.png"
            )
        )

    def test_rejects_path_outside_project(self):
        with self.assertRaises(InlineImageError):
            resolve_asset_path("C:/projects/example", "../outside.png")

    def test_text_content_round_trip_keeps_old_blackout_data(self):
        squares = [[[0.0, 10.0], [0.0, 10.0]]]
        images = [create_inline_image("asset", 2, 80, 40)]

        packed = pack_text_content("問題文", squares, images)
        text, loaded_squares, loaded_images = unpack_text_content(packed)

        self.assertEqual(text, "問題文")
        self.assertEqual(loaded_squares, squares)
        self.assertEqual(loaded_images, images)

    def test_unpacks_legacy_text_without_inline_images(self):
        legacy = ["問題文", [[10.0, 20.0], [0.0, 10.0]]]

        text, squares, images = unpack_text_content(legacy)

        self.assertEqual(text, "問題文")
        self.assertEqual(squares, legacy[1:])
        self.assertEqual(images, [])


if __name__ == "__main__":
    unittest.main()
