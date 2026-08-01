import mimetypes
import os
import uuid


INLINE_IMAGES_KEY = "inline_images"
IMAGE_ASSETS_KEY = "image_assets"

BLACKOUT_NONE = "none"
BLACKOUT_OPAQUE = "opaque"
BLACKOUT_ALL = "all"
BLACKOUT_MODES = {
    BLACKOUT_NONE,
    BLACKOUT_OPAQUE,
    BLACKOUT_ALL,
}

MAX_IMAGE_BYTES = 20 * 1024 * 1024
MIN_DISPLAY_SIZE = 8
MAX_DISPLAY_SIZE = 800


class InlineImageError(ValueError):
    pass


def create_image_asset(
    file_name,
    relative_path,
    width,
    height,
    asset_id=None,
):
    if not isinstance(relative_path, str) or not relative_path.strip():
        raise InlineImageError("画像の保存先が指定されていません")
    if width <= 0 or height <= 0:
        raise InlineImageError("画像サイズを取得できません")

    mime_type = mimetypes.guess_type(file_name)[0] or "image/png"
    return str(asset_id or uuid.uuid4()), {
        "name": os.path.basename(file_name),
        "path": relative_path.replace("\\", "/"),
        "mime_type": mime_type,
        "width": int(width),
        "height": int(height),
    }


def create_inline_image(
    asset_id,
    position,
    width,
    height,
    blackout=BLACKOUT_NONE,
    line_break=False,
):
    return normalize_inline_image(
        {
            "id": str(uuid.uuid4()),
            "asset_id": asset_id,
            "position": position,
            "width": width,
            "height": height,
            "blackout": blackout,
            "line_break": line_break,
        }
    )


def normalize_inline_image(value, text_length=None):
    if not isinstance(value, dict):
        raise InlineImageError("画像差し込みデータの形式が不正です")

    asset_id = str(value.get("asset_id", "")).strip()
    if not asset_id:
        raise InlineImageError("登録画像が指定されていません")

    position = _clamped_int(value.get("position", 0), 0, text_length)
    width = _clamped_int(
        value.get("width", 80),
        MIN_DISPLAY_SIZE,
        MAX_DISPLAY_SIZE,
    )
    height = _clamped_int(
        value.get("height", 80),
        MIN_DISPLAY_SIZE,
        MAX_DISPLAY_SIZE,
    )
    blackout = value.get("blackout", BLACKOUT_NONE)
    if blackout not in BLACKOUT_MODES:
        blackout = BLACKOUT_NONE

    return {
        "id": str(value.get("id") or uuid.uuid4()),
        "asset_id": asset_id,
        "position": position,
        "width": width,
        "height": height,
        "blackout": blackout,
        # 画像の直後で改行する（旧データには無いので既定 False）
        "line_break": bool(value.get("line_break", False)),
    }


def normalize_inline_images(values, text_length=None):
    if not isinstance(values, list):
        return []

    normalized = []
    known_ids = set()
    for value in values:
        try:
            image = normalize_inline_image(value, text_length)
        except InlineImageError:
            continue
        if image["id"] in known_ids:
            image["id"] = str(uuid.uuid4())
        known_ids.add(image["id"])
        normalized.append(image)
    return sorted(
        normalized,
        key=lambda image: (image["position"], image["id"]),
    )


def normalize_image_assets(values):
    if not isinstance(values, dict):
        return {}

    normalized = {}
    for asset_id, value in values.items():
        if not isinstance(value, dict):
            continue
        path = value.get("path")
        if not isinstance(path, str) or not path.strip():
            continue
        normalized[str(asset_id)] = {
            "name": str(value.get("name", "画像")),
            "path": path.replace("\\", "/"),
            "mime_type": str(value.get("mime_type", "image/png")),
            "width": _clamped_int(
                value.get("width", 80),
                1,
                None,
            ),
            "height": _clamped_int(
                value.get("height", 80),
                1,
                None,
            ),
        }
    return normalized


def make_asset_relative_path(file_name, asset_id):
    extension = os.path.splitext(file_name)[1].lower()
    if extension not in {
        ".png",
        ".jpg",
        ".jpeg",
        ".bmp",
        ".gif",
        ".webp",
    }:
        extension = ".png"
    return f"picture/inline/{asset_id}{extension}"


def resolve_asset_path(project_root, relative_path):
    if not project_root:
        raise InlineImageError("プロジェクトフォルダが設定されていません")
    if not isinstance(relative_path, str) or not relative_path.strip():
        raise InlineImageError("画像の相対パスが不正です")
    if os.path.isabs(relative_path):
        raise InlineImageError("画像には相対パスを指定してください")

    root = os.path.realpath(project_root)
    target = os.path.realpath(
        os.path.join(root, relative_path.replace("/", os.sep))
    )
    try:
        inside_project = os.path.commonpath([root, target]) == root
    except ValueError:
        inside_project = False
    if not inside_project:
        raise InlineImageError("プロジェクト外の画像は参照できません")
    return target


def referenced_asset_ids(targets):
    return {
        image["asset_id"]
        for target in targets
        for image in target.get_inline_images()
    }


def pack_text_content(text, squares, inline_images):
    data = [str(text)]
    data.extend(squares)
    if inline_images:
        data.append(
            {
                INLINE_IMAGES_KEY: [
                    dict(image) for image in inline_images
                ]
            }
        )
    return data


def unpack_text_content(data):
    if isinstance(data, str):
        return data, [], []
    if not isinstance(data, list) or not data:
        return "", [], []

    squares = []
    inline_images = []
    for value in data[1:]:
        if isinstance(value, dict) and INLINE_IMAGES_KEY in value:
            inline_images = value[INLINE_IMAGES_KEY]
        elif isinstance(value, list):
            squares.append(value)
    return str(data[0]), squares, inline_images


def _clamped_int(value, minimum, maximum):
    try:
        converted = int(value)
    except (TypeError, ValueError):
        converted = minimum
    converted = max(minimum, converted)
    if maximum is not None:
        converted = min(maximum, converted)
    return converted
