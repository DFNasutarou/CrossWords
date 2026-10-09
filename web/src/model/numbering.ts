// カギ番号の採番。デスクトップ版 CellBoard.reset と同じ規則。
// 「row」はタテ（下方向に読む）、「col」はヨコ（右方向に読む）。

export type NumberingMode = "top_priority" | "left_priority";

export type NumberingEntry = {
  number: number;
  row: number;
  col: number;
  answer: string;
};

export type NumberingResult = {
  numbers: (number | null)[][];
  vertical: NumberingEntry[];
  horizontal: NumberingEntry[];
};

export function computeNumbering(
  black: boolean[][],
  chars: string[][],
  mode: NumberingMode,
): NumberingResult {
  const n = black.length;
  const isBlack = (r: number, c: number) => black[r][c];
  const numbers: (number | null)[][] = Array.from({ length: n }, () =>
    Array.from({ length: n }, () => null),
  );

  const readAnswer = (row: number, col: number, vertical: boolean) => {
    let answer = "";
    while (row < n && col < n && !isBlack(row, col)) {
      answer += chars[row][col] || " ";
      if (vertical) row++;
      else col++;
    }
    return answer;
  };

  const order: [number, number][] = [];
  for (let a = 0; a < n; a++) {
    for (let b = 0; b < n; b++) {
      order.push(mode === "top_priority" ? [a, b] : [b, a]);
    }
  }

  const vertical: NumberingEntry[] = [];
  const horizontal: NumberingEntry[] = [];
  let number = 1;
  for (const [r, c] of order) {
    if (isBlack(r, c)) continue;
    const startsVertical =
      (r === 0 || isBlack(r - 1, c)) && !(r === n - 1 || isBlack(r + 1, c));
    const startsHorizontal =
      (c === 0 || isBlack(r, c - 1)) && !(c === n - 1 || isBlack(r, c + 1));
    if (!startsVertical && !startsHorizontal) continue;
    numbers[r][c] = number;
    if (startsVertical) {
      vertical.push({ number, row: r, col: c, answer: readAnswer(r, c, true) });
    }
    if (startsHorizontal) {
      horizontal.push({ number, row: r, col: c, answer: readAnswer(r, c, false) });
    }
    number++;
  }
  vertical.sort((a, b) => a.number - b.number);
  horizontal.sort((a, b) => a.number - b.number);
  return { numbers, vertical, horizontal };
}
