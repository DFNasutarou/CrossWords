from collections import deque
from dataclasses import dataclass
from functools import lru_cache
import re
from typing import Callable, Iterable


MIN_ENUMERATOR_SIZE = 4
MAX_ENUMERATOR_SIZE = 9

WHITE = 0
BLACK = 1

NUMBERING_TOP_PRIORITY = "top_priority"
NUMBERING_LEFT_PRIORITY = "left_priority"
NUMBERING_MODES = {
    NUMBERING_TOP_PRIORITY,
    NUMBERING_LEFT_PRIORITY,
}

UNKNOWN_MARKERS = {
    "",
    "?",
    "*",
    "■",
    "●",
    "黒",
    "黒塗り",
}


class BoardEnumerationError(ValueError):
    pass


@dataclass(frozen=True)
class NumberingMatch:
    mode: str
    vertical_numbers: tuple[int, ...]
    horizontal_numbers: tuple[int, ...]


@dataclass(frozen=True)
class BoardCandidate:
    size: int
    grid: tuple[tuple[int, ...], ...]
    numberings: tuple[NumberingMatch, ...]

    @property
    def black_cells(self):
        return tuple(
            (row, col)
            for row in range(self.size)
            for col in range(self.size)
            if self.grid[row][col] == BLACK
        )


@dataclass(frozen=True)
class EnumerationStats:
    explored_states: int
    completed_boards: int
    matched_boards: int
    skipped_sizes: tuple[int, ...]


@dataclass(frozen=True)
class EnumerationOutcome:
    results: tuple[BoardCandidate, ...]
    stats: EnumerationStats
    cancelled: bool
    truncated: bool


def enumerate_boards(
    vertical_clues,
    horizontal_clues,
    sizes: Iterable[int] = range(
        MIN_ENUMERATOR_SIZE,
        MAX_ENUMERATOR_SIZE + 1,
    ),
    numbering_modes: Iterable[str] = (
        NUMBERING_TOP_PRIORITY,
        NUMBERING_LEFT_PRIORITY,
    ),
    limit: int | None = None,
    is_cancelled: Callable[[], bool] | None = None,
    on_progress: Callable[[int, int, int], None] | None = None,
    require_point_symmetry: bool = True,
    allow_unchecked_cells: bool = False,
):
    vertical_pattern = normalize_clue_pattern(vertical_clues)
    horizontal_pattern = normalize_clue_pattern(horizontal_clues)
    modes = normalize_numbering_modes(numbering_modes)
    size_candidates = normalize_sizes(sizes)
    if limit is not None and limit <= 0:
        raise BoardEnumerationError("結果件数の上限は1以上にしてください")

    vertical_count = len(vertical_pattern)
    horizontal_count = len(horizontal_pattern)
    max_known_number = max(
        (
            number
            for number in vertical_pattern + horizontal_pattern
            if number is not None
        ),
        default=0,
    )

    results = []
    skipped_sizes = []
    explored_states = 0
    completed_boards = 0
    cancelled = False
    truncated = False

    for size in size_candidates:
        if is_cancelled and is_cancelled():
            cancelled = True
            break

        if not require_point_symmetry or allow_unchecked_cells:
            if allow_unchecked_cells:
                masks_all = valid_row_masks_unchecked(size)
            else:
                masks_all = valid_row_masks(size)
            counts_by_mask = {
                mask: clue_run_count(mask, size) for mask in masks_all
            }
            min_count = min(counts_by_mask.values())
            max_count = max(counts_by_mask.values())
            if not general_size_feasible(
                size,
                vertical_count,
                horizontal_count,
                max_known_number,
                min_count,
                max_count,
            ):
                skipped_sizes.append(size)
                continue
            # 上優先のみの探索では、確定済み行のカギ番号を
            # 期待パターンと突き合わせて枝刈りできる
            top_only = modes == (NUMBERING_TOP_PRIORITY,)

            rows_stack = []
            # (割り当て済み番号, 確定タテカギ数, 確定ヨコカギ数)
            prefix_states = [(0, 0, 0)]
            stop_size = False

            def process_determined_row(row_index):
                """row_index 行の開始マスを確定し矛盾を調べる。

                行 row_index のタテ開始判定には次の行が必要なため、
                次の行を積んだ後（または盤面完成後）に呼ぶこと。
                矛盾がなければ更新後の状態、あれば None を返す。
                """
                number, v_index, h_index = prefix_states[-1]
                mask = rows_stack[row_index]
                above = rows_stack[row_index - 1] if row_index else None
                below = (
                    rows_stack[row_index + 1]
                    if row_index + 1 < len(rows_stack)
                    else None
                )
                for col in range(size):
                    bit = 1 << col
                    if mask & bit:
                        continue
                    is_vertical = (
                        (row_index == 0 or above & bit)
                        and row_index + 1 < size
                        and below is not None
                        and not below & bit
                    )
                    is_horizontal = (
                        (col == 0 or mask & (bit >> 1))
                        and col + 1 < size
                        and not mask & (bit << 1)
                    )
                    if not (is_vertical or is_horizontal):
                        continue
                    number += 1
                    if is_vertical:
                        if v_index >= vertical_count:
                            return None
                        expected = vertical_pattern[v_index]
                        if (
                            top_only
                            and expected is not None
                            and expected != number
                        ):
                            return None
                        v_index += 1
                    if is_horizontal:
                        if h_index >= horizontal_count:
                            return None
                        expected = horizontal_pattern[h_index]
                        if (
                            top_only
                            and expected is not None
                            and expected != number
                        ):
                            return None
                        h_index += 1
                return (number, v_index, h_index)

            def search_general(depth, clue_sum):
                nonlocal explored_states
                nonlocal completed_boards
                nonlocal cancelled
                nonlocal truncated
                nonlocal stop_size

                if stop_size:
                    return
                explored_states += 1
                if on_progress and explored_states % 1000 == 0:
                    on_progress(explored_states, len(results), size)
                if is_cancelled and is_cancelled():
                    cancelled = True
                    stop_size = True
                    return

                if depth == size:
                    state = process_determined_row(size - 1)
                    if state is None:
                        return
                    _, v_index, h_index = state
                    if (
                        v_index != vertical_count
                        or h_index != horizontal_count
                    ):
                        return
                    rows = tuple(rows_stack)
                    if allow_unchecked_cells:
                        # 1文字マスは許すが、タテヨコ両方とも
                        # クロスしない孤立マスは禁止
                        if not no_isolated_white_cells(rows, size):
                            return
                    elif not no_single_character_clues(rows, size):
                        return
                    if not white_cells_connected(rows, size):
                        return
                    completed_boards += 1
                    matches = matching_numberings(
                        rows,
                        size,
                        vertical_pattern,
                        horizontal_pattern,
                        modes,
                    )
                    if not matches:
                        return
                    grid = tuple(
                        tuple(
                            BLACK if row_mask & (1 << col) else WHITE
                            for col in range(size)
                        )
                        for row_mask in rows
                    )
                    results.append(
                        BoardCandidate(
                            size=size,
                            grid=grid,
                            numberings=matches,
                        )
                    )
                    if limit is not None and len(results) >= limit:
                        truncated = True
                        stop_size = True
                    return

                previous = rows_stack[-1] if rows_stack else None
                previous_previous = (
                    rows_stack[-2] if len(rows_stack) >= 2 else None
                )
                remaining = size - depth - 1
                mirror = size - 1 - depth
                if require_point_symmetry and mirror < depth:
                    # 下半分は上半分の 180 度回転で確定
                    forced = reverse_mask(rows_stack[mirror], size)
                    candidates = (
                        (forced,) if forced in counts_by_mask else ()
                    )
                elif require_point_symmetry and mirror == depth:
                    # 奇数サイズの中央行は自己対称なもののみ
                    candidates = tuple(
                        mask
                        for mask in masks_all
                        if mask == reverse_mask(mask, size)
                    )
                else:
                    candidates = masks_all
                for mask in candidates:
                    new_sum = clue_sum + counts_by_mask[mask]
                    if new_sum + remaining * min_count > horizontal_count:
                        continue
                    if new_sum + remaining * max_count < horizontal_count:
                        continue
                    if previous is not None and previous & mask:
                        continue
                    if _closes_bad_vertical_cell(
                        previous_previous,
                        previous,
                        mask,
                        size,
                        allow_unchecked_cells,
                    ):
                        continue
                    rows_stack.append(mask)
                    state = (
                        prefix_states[-1]
                        if depth == 0
                        else process_determined_row(depth - 1)
                    )
                    if state is not None:
                        prefix_states.append(state)
                        search_general(depth + 1, new_sum)
                        prefix_states.pop()
                    rows_stack.pop()
                    if stop_size:
                        return

            search_general(0, 0)
            if cancelled or truncated:
                break
            continue

        if not size_can_match(
            size,
            vertical_count,
            horizontal_count,
            max_known_number,
        ):
            skipped_sizes.append(size)
            continue

        rows_by_clue_count = _rows_grouped_by_clue_count(size)
        center_rows = _center_rows(
            size,
            vertical_count,
            horizontal_count,
        )
        if size % 2 == 0:
            center_options = (None,)
        else:
            center_options = center_rows
        if not center_options:
            skipped_sizes.append(size)
            continue

        half_height = size // 2
        stop_size = False
        for center_row in center_options:
            center_horizontal_count = (
                0
                if center_row is None
                else row_clue_count(center_row, size)
            )
            remaining_horizontal = (
                horizontal_count - center_horizontal_count
            )
            if remaining_horizontal < 0 or remaining_horizontal % 2:
                continue
            top_target = remaining_horizontal // 2

            top_rows = []

            def search_rows(depth, clue_sum):
                nonlocal explored_states
                nonlocal completed_boards
                nonlocal cancelled
                nonlocal truncated
                nonlocal stop_size

                if stop_size:
                    return
                explored_states += 1
                if on_progress and explored_states % 1000 == 0:
                    on_progress(
                        explored_states,
                        len(results),
                        size,
                    )
                if is_cancelled and is_cancelled():
                    cancelled = True
                    stop_size = True
                    return

                remaining_rows = half_height - depth
                if not _clue_sum_reachable(
                    clue_sum,
                    top_target,
                    remaining_rows,
                    rows_by_clue_count,
                ):
                    return

                if depth == half_height:
                    if clue_sum != top_target:
                        return
                    rows = build_symmetric_rows(
                        top_rows,
                        center_row,
                        size,
                    )
                    if not board_rules_valid(rows, size):
                        return
                    completed_boards += 1
                    if vertical_clue_count(rows, size) != vertical_count:
                        return

                    matches = matching_numberings(
                        rows,
                        size,
                        vertical_pattern,
                        horizontal_pattern,
                        modes,
                    )
                    if not matches:
                        return
                    grid = tuple(
                        tuple(
                            BLACK if row_mask & (1 << col) else WHITE
                            for col in range(size)
                        )
                        for row_mask in rows
                    )
                    results.append(
                        BoardCandidate(
                            size=size,
                            grid=grid,
                            numberings=matches,
                        )
                    )
                    if limit is not None and len(results) >= limit:
                        truncated = True
                        stop_size = True
                    return

                previous = top_rows[-1] if top_rows else None
                previous_previous = (
                    top_rows[-2] if len(top_rows) >= 2 else None
                )
                for clue_count, row_masks in rows_by_clue_count.items():
                    if clue_sum + clue_count > top_target:
                        continue
                    for row_mask in row_masks:
                        if previous is not None and previous & row_mask:
                            continue
                        if _closes_single_vertical_cell(
                            previous_previous,
                            previous,
                            row_mask,
                            size,
                        ):
                            continue
                        top_rows.append(row_mask)
                        search_rows(depth + 1, clue_sum + clue_count)
                        top_rows.pop()
                        if stop_size:
                            return

            search_rows(0, 0)
            if stop_size:
                break

        if cancelled or truncated:
            break

    return EnumerationOutcome(
        results=tuple(results),
        stats=EnumerationStats(
            explored_states=explored_states,
            completed_boards=completed_boards,
            matched_boards=len(results),
            skipped_sizes=tuple(skipped_sizes),
        ),
        cancelled=cancelled,
        truncated=truncated,
    )


def normalize_clue_pattern(values):
    if values is None:
        raise BoardEnumerationError("カギ番号を指定してください")

    normalized = []
    for value in values:
        if value is None:
            normalized.append(None)
            continue
        if isinstance(value, str):
            stripped = value.strip()
            if stripped in UNKNOWN_MARKERS:
                normalized.append(None)
                continue
            try:
                value = int(stripped)
            except ValueError as error:
                raise BoardEnumerationError(
                    f"カギ番号として解釈できません: {value}"
                ) from error
        if isinstance(value, bool) or not isinstance(value, int):
            raise BoardEnumerationError(
                f"カギ番号として解釈できません: {value}"
            )
        if value <= 0:
            raise BoardEnumerationError("カギ番号は1以上にしてください")
        normalized.append(value)

    for index, number in enumerate(normalized):
        if number is not None and number < index + 1:
            raise BoardEnumerationError(
                "見えているカギ番号と黒塗り数が矛盾しています"
            )
    known = [
        (index, number)
        for index, number in enumerate(normalized)
        if number is not None
    ]
    for (left_index, left), (right_index, right) in zip(
        known,
        known[1:],
    ):
        if right - left < right_index - left_index:
            raise BoardEnumerationError(
                "カギ番号は黒塗り部分を含めて単調増加する必要があります"
            )
    return tuple(normalized)


def parse_clue_pattern_text(text):
    if not isinstance(text, str):
        raise BoardEnumerationError("カギ番号を文字列で指定してください")
    tokens = [
        token
        for token in re.split(r"[\s,、]+", text.strip())
        if token
    ]
    if not tokens:
        raise BoardEnumerationError("カギ番号を1つ以上入力してください")
    return normalize_clue_pattern(tokens)


def normalize_numbering_modes(values):
    modes = []
    for value in values:
        if value not in NUMBERING_MODES:
            raise BoardEnumerationError(f"未対応の採番方式です: {value}")
        if value not in modes:
            modes.append(value)
    if not modes:
        raise BoardEnumerationError("採番方式を1つ以上指定してください")
    return tuple(modes)


def normalize_sizes(values):
    sizes = []
    for value in values:
        if (
            isinstance(value, bool)
            or not isinstance(value, int)
            or not MIN_ENUMERATOR_SIZE <= value <= MAX_ENUMERATOR_SIZE
        ):
            raise BoardEnumerationError(
                "盤面サイズは4～9の整数にしてください"
            )
        if value not in sizes:
            sizes.append(value)
    if not sizes:
        raise BoardEnumerationError("盤面サイズを指定してください")
    return tuple(sizes)


def size_can_match(
    size,
    vertical_count,
    horizontal_count,
    max_known_number=0,
):
    if max_known_number > vertical_count + horizontal_count:
        return False
    if size % 2 == 0:
        if vertical_count % 2 or horizontal_count % 2:
            return False
    elif vertical_count % 2 != horizontal_count % 2:
        return False

    return horizontal_count in _possible_horizontal_counts(size)


def general_size_feasible(
    size,
    vertical_count,
    horizontal_count,
    max_known_number,
    min_row_count,
    max_row_count,
):
    """汎用探索でサイズが候補になり得るかを返す。

    列マスクにも行マスクと同じ制約が成り立つため、
    タテのカギ数にも同じ範囲を適用できる。
    """
    if max_known_number > vertical_count + horizontal_count:
        return False
    return (
        size * min_row_count <= horizontal_count <= size * max_row_count
        and size * min_row_count <= vertical_count <= size * max_row_count
    )


def clue_number_cells(rows, size, mode):
    """採番方式 mode における (row, col) -> カギ番号 の辞書を返す。"""
    vertical_starts, horizontal_starts = clue_start_cells(rows, size)
    all_starts = vertical_starts | horizontal_starts
    if mode == NUMBERING_TOP_PRIORITY:
        traversal = (
            (row, col)
            for row in range(size)
            for col in range(size)
        )
    elif mode == NUMBERING_LEFT_PRIORITY:
        traversal = (
            (row, col)
            for col in range(size)
            for row in range(size)
        )
    else:
        raise BoardEnumerationError(f"未対応の採番方式です: {mode}")

    numbers = {}
    next_number = 1
    for cell in traversal:
        if cell in all_starts:
            numbers[cell] = next_number
            next_number += 1
    return numbers


def grid_to_rows(grid):
    """BoardCandidate.grid をビットマスクの行タプルへ変換する。"""
    return tuple(
        sum(
            (1 << col)
            for col, cell in enumerate(row)
            if cell == BLACK
        )
        for row in grid
    )


def matching_numberings(
    rows,
    size,
    vertical_pattern,
    horizontal_pattern,
    modes,
):
    matches = []
    for mode in modes:
        vertical, horizontal = clue_numbers(rows, size, mode)
        if pattern_matches(vertical_pattern, vertical) and pattern_matches(
            horizontal_pattern,
            horizontal,
        ):
            matches.append(
                NumberingMatch(
                    mode=mode,
                    vertical_numbers=vertical,
                    horizontal_numbers=horizontal,
                )
            )
    return tuple(matches)


def clue_numbers(rows, size, mode):
    vertical_starts, horizontal_starts = clue_start_cells(rows, size)
    all_starts = vertical_starts | horizontal_starts
    if mode == NUMBERING_TOP_PRIORITY:
        traversal = (
            (row, col)
            for row in range(size)
            for col in range(size)
        )
    elif mode == NUMBERING_LEFT_PRIORITY:
        traversal = (
            (row, col)
            for col in range(size)
            for row in range(size)
        )
    else:
        raise BoardEnumerationError(f"未対応の採番方式です: {mode}")

    numbers = {}
    next_number = 1
    for cell in traversal:
        if cell in all_starts:
            numbers[cell] = next_number
            next_number += 1

    vertical = tuple(sorted(numbers[cell] for cell in vertical_starts))
    horizontal = tuple(sorted(numbers[cell] for cell in horizontal_starts))
    return vertical, horizontal


def clue_start_cells(rows, size):
    vertical = set()
    horizontal = set()
    for row in range(size):
        for col in range(size):
            if is_black(rows, row, col):
                continue
            if (
                (row == 0 or is_black(rows, row - 1, col))
                and row + 1 < size
                and not is_black(rows, row + 1, col)
            ):
                vertical.add((row, col))
            if (
                (col == 0 or is_black(rows, row, col - 1))
                and col + 1 < size
                and not is_black(rows, row, col + 1)
            ):
                horizontal.add((row, col))
    return vertical, horizontal


def pattern_matches(pattern, actual):
    return len(pattern) == len(actual) and all(
        expected is None or expected == value
        for expected, value in zip(pattern, actual)
    )


def board_rules_valid(rows, size):
    return (
        black_cells_not_adjacent(rows, size)
        and no_single_character_clues(rows, size)
        and white_cells_connected(rows, size)
        and point_symmetric(rows, size)
    )


def black_cells_not_adjacent(rows, size):
    for row_index, row_mask in enumerate(rows):
        if row_mask & (row_mask << 1):
            return False
        if row_index and row_mask & rows[row_index - 1]:
            return False
    return True


def no_single_character_clues(rows, size):
    for row_mask in rows:
        if any(length == 1 for length in white_run_lengths(row_mask, size)):
            return False
    for col in range(size):
        mask = sum(
            (1 << row)
            for row in range(size)
            if is_black(rows, row, col)
        )
        if any(length == 1 for length in white_run_lengths(mask, size)):
            return False
    return True


def white_cells_connected(rows, size):
    start = next(
        (
            (row, col)
            for row in range(size)
            for col in range(size)
            if not is_black(rows, row, col)
        ),
        None,
    )
    if start is None:
        return False

    queue = deque([start])
    visited = {start}
    while queue:
        row, col = queue.popleft()
        for next_row, next_col in (
            (row - 1, col),
            (row + 1, col),
            (row, col - 1),
            (row, col + 1),
        ):
            next_cell = (next_row, next_col)
            if (
                0 <= next_row < size
                and 0 <= next_col < size
                and next_cell not in visited
                and not is_black(rows, next_row, next_col)
            ):
                visited.add(next_cell)
                queue.append(next_cell)

    white_count = size * size - sum(mask.bit_count() for mask in rows)
    return len(visited) == white_count


def point_symmetric(rows, size):
    return all(
        rows[size - 1 - row] == reverse_mask(rows[row], size)
        for row in range(size)
    )


def vertical_clue_count(rows, size):
    return sum(
        len(
            white_run_lengths(
                sum(
                    (1 << row)
                    for row in range(size)
                    if is_black(rows, row, col)
                ),
                size,
            )
        )
        for col in range(size)
    )


def horizontal_clue_count(rows, size):
    return sum(row_clue_count(row, size) for row in rows)


def build_symmetric_rows(top_rows, center_row, size):
    bottom_rows = [
        reverse_mask(row, size)
        for row in reversed(top_rows)
    ]
    if size % 2:
        return tuple(top_rows) + (center_row,) + tuple(bottom_rows)
    return tuple(top_rows) + tuple(bottom_rows)


@lru_cache(maxsize=None)
def valid_row_masks(size):
    masks = []
    for mask in range(1 << size):
        if mask & (mask << 1):
            continue
        if any(length == 1 for length in white_run_lengths(mask, size)):
            continue
        masks.append(mask)
    return tuple(masks)


@lru_cache(maxsize=None)
def valid_row_masks_unchecked(size):
    """1文字（クロスしない）白マスを許す場合の有効な行マスク。

    黒マスの左右隣接だけを禁止する。
    """
    return tuple(
        mask
        for mask in range(1 << size)
        if not mask & (mask << 1)
    )


def clue_run_count(mask, size):
    """カギになる（長さ2以上の）白連続の数を返す。"""
    return sum(
        1
        for length in white_run_lengths(mask, size)
        if length >= 2
    )


def no_isolated_white_cells(rows, size):
    """タテヨコどちらでもクロスしない孤立白マスが無いことを確認する。"""
    for row in range(size):
        for col in range(size):
            if is_black(rows, row, col):
                continue
            horizontal = _run_length_in_mask(rows[row], col, size)
            if horizontal >= 2:
                continue
            column_mask = sum(
                (1 << index)
                for index in range(size)
                if is_black(rows, index, col)
            )
            if _run_length_in_mask(column_mask, row, size) < 2:
                return False
    return True


def _run_length_in_mask(mask, index, size):
    """mask 中の白マス index が属する白連続の長さを返す。"""
    if mask & (1 << index):
        return 0
    length = 1
    step = index - 1
    while step >= 0 and not mask & (1 << step):
        length += 1
        step -= 1
    step = index + 1
    while step < size and not mask & (1 << step):
        length += 1
        step += 1
    return length


def _closes_bad_vertical_cell(
    previous_previous,
    previous,
    current,
    size,
    allow_unchecked,
):
    """current 行を置くと直前行の白マスが縦1マスで閉じるかを調べる。

    1文字マス禁止時は常に枝刈り。許可時も、そのマスが横方向でも
    クロスしていなければ孤立マスになるため枝刈りする。
    """
    if previous is None:
        return False
    for col in range(size):
        bit = 1 << col
        if not current & bit:
            continue
        if previous & bit:
            continue
        starts_at_edge = previous_previous is None
        starts_after_black = (
            previous_previous is not None
            and previous_previous & bit
        )
        if not (starts_at_edge or starts_after_black):
            continue
        if not allow_unchecked:
            return True
        if _run_length_in_mask(previous, col, size) < 2:
            return True
    return False


@lru_cache(maxsize=None)
def _rows_grouped_by_clue_count(size):
    groups = {}
    for mask in valid_row_masks(size):
        groups.setdefault(row_clue_count(mask, size), []).append(mask)
    return {
        count: tuple(masks)
        for count, masks in groups.items()
    }


def row_clue_count(mask, size):
    return len(white_run_lengths(mask, size))


def white_run_lengths(mask, size):
    runs = []
    length = 0
    for index in range(size):
        if mask & (1 << index):
            if length:
                runs.append(length)
                length = 0
        else:
            length += 1
    if length:
        runs.append(length)
    return tuple(runs)


def reverse_mask(mask, size):
    return sum(
        (1 << (size - 1 - index))
        for index in range(size)
        if mask & (1 << index)
    )


def is_black(rows, row, col):
    return bool(rows[row] & (1 << col))


def _center_rows(size, vertical_count, horizontal_count):
    if size % 2 == 0:
        return ()
    center = size // 2
    center_black = vertical_count % 2 == 0
    return tuple(
        mask
        for mask in valid_row_masks(size)
        if mask == reverse_mask(mask, size)
        and bool(mask & (1 << center)) == center_black
    )


def _clue_sum_reachable(
    current,
    target,
    remaining_rows,
    rows_by_clue_count,
):
    if remaining_rows == 0:
        return current == target
    counts = rows_by_clue_count.keys()
    return (
        current + min(counts) * remaining_rows <= target
        <= current + max(counts) * remaining_rows
    )


def _closes_single_vertical_cell(
    previous_previous,
    previous,
    current,
    size,
):
    if previous is None:
        return False
    for col in range(size):
        if current & (1 << col):
            previous_is_white = not previous & (1 << col)
            starts_at_edge = previous_previous is None
            starts_after_black = (
                previous_previous is not None
                and previous_previous & (1 << col)
            )
            if previous_is_white and (starts_at_edge or starts_after_black):
                return True
    return False


@lru_cache(maxsize=None)
def _possible_horizontal_counts(size):
    """点対称な行構成で取り得る横カギ数を返す。"""
    counts = sorted(
        {
            row_clue_count(mask, size)
            for mask in valid_row_masks(size)
        }
    )
    half = size // 2
    partial_sums = {0}
    for _ in range(half):
        partial_sums = {
            current + count
            for current in partial_sums
            for count in counts
        }

    if size % 2 == 0:
        totals = {value * 2 for value in partial_sums}
    else:
        center_counts = {
            row_clue_count(mask, size)
            for mask in valid_row_masks(size)
            if mask == reverse_mask(mask, size)
        }
        totals = {
            value * 2 + center_count
            for value in partial_sums
            for center_count in center_counts
        }
    return tuple(sorted(totals))
