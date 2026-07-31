def blackout_rect(
    square,
    unit_width,
    content_width,
    content_height,
    offset_x=0,
    offset_y=0,
):
    """黒塗り設定値を描画用の (x, y, width, height) に変換する。"""
    x_range, y_range = square

    x1 = int(unit_width * x_range[0] / 10)
    x2 = int(unit_width * x_range[1] / 10)
    y1 = int(content_height * y_range[0] / 10)
    y2 = int(content_height * y_range[1] / 10)

    x1 = min(max(0, x1), content_width)
    x2 = min(max(0, x2), content_width)
    y1 = min(max(0, y1), content_height)
    y2 = min(max(0, y2), content_height)

    left, right = sorted((x1, x2))
    top, bottom = sorted((y1, y2))

    return [
        offset_x + left,
        offset_y + top,
        right - left,
        bottom - top,
    ]


def scaled_dimensions(width, height, scale):
    if scale <= 0:
        raise ValueError("拡大率は0より大きい値を指定してください")
    return round(width * scale), round(height * scale)


def snapped_blackout_square(start_x, end_x, unit_width, text_length):
    """ドラッグした横位置を文字単位の黒塗り範囲へ変換する。"""
    if unit_width <= 0 or text_length <= 0:
        return [[0.0, 0.0], [0.0, 10.0]]

    max_x = unit_width * text_length

    def character_index(x):
        clamped = min(max(float(x), 0.0), max_x)
        if clamped == max_x:
            return text_length - 1
        return int(clamped // unit_width)

    start_index = character_index(start_x)
    end_index = character_index(end_x)
    left = min(start_index, end_index)
    right = max(start_index, end_index) + 1
    return [[float(left * 10), float(right * 10)], [0.0, 10.0]]
