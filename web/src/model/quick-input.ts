// 盤面のテキスト一括入力。
//   かつなよし
//   らぶ＊めん
// のように1行を盤の1行として書くと盤面に反映する。
import {
  CELL_BLACK,
  CELL_DOUBLE,
  CELL_WHITE,
  MAX_BOARD_SIZE,
  MIN_BOARD_SIZE,
  getDisplayCell,
  resizeBoard,
  updateCells,
  type CellUpdate,
  type ProjectData,
  type ProjectDocument,
} from "./project";

export const BLACK_MARKS = ["＊", "*", "#", "＃", "■"];
export const EMPTY_MARKS = ["・", ".", "．", "□", "_", "＿"];
const OUTPUT_BLACK = "＊";
const OUTPUT_EMPTY = "・";

export type QuickCell = { black: true } | { black: false; char: string };

export type QuickInputError = { line: number | null; message: string };

export type QuickInputResult =
  | { ok: true; size: number; cells: QuickCell[][] }
  | { ok: false; errors: QuickInputError[] };

// 1文字を盤のマスとして解釈する（盤面への直接入力でも使う）
export function interpretChar(char: string): QuickCell {
  if (BLACK_MARKS.includes(char)) return { black: true };
  if (EMPTY_MARKS.includes(char)) return { black: false, char: "" };
  return { black: false, char };
}

export function parseQuickInput(text: string): QuickInputResult {
  // 空白は読みやすさのために入れてよい（マスとしては数えない）
  const lines = text
    .split(/\r?\n/)
    .map((line, index) => ({
      line: index + 1,
      chars: Array.from(line.replace(/[\s　]/g, "")),
    }))
    .filter((entry) => entry.chars.length > 0);

  const size = lines.length;
  const errors: QuickInputError[] = [];
  if (size === 0) {
    return { ok: false, errors: [{ line: null, message: "盤面が入力されていません。" }] };
  }
  if (size < MIN_BOARD_SIZE || size > MAX_BOARD_SIZE) {
    errors.push({
      line: null,
      message: `行数が${size}行です。盤は${MIN_BOARD_SIZE}～${MAX_BOARD_SIZE}行で入力してください。`,
    });
  }
  for (const entry of lines) {
    if (entry.chars.length !== size) {
      errors.push({
        line: entry.line,
        message: `${entry.line}行目が${entry.chars.length}マスです（${size}行なので${size}マス必要）。`,
      });
    }
  }
  if (errors.length > 0) return { ok: false, errors };

  return {
    ok: true,
    size,
    cells: lines.map((entry) => entry.chars.map(interpretChar)),
  };
}

export function formatQuickInput(data: ProjectData): string {
  const size = data.cell.board_size;
  const lines: string[] = [];
  for (let r = 0; r < size; r++) {
    let line = "";
    for (let c = 0; c < size; c++) {
      const cell = getDisplayCell(data, r, c);
      if (cell.state === CELL_BLACK) line += OUTPUT_BLACK;
      else line += cell.charactor || OUTPUT_EMPTY;
    }
    lines.push(line);
  }
  return lines.join("\n");
}

// 二重マスは一括入力とは別に設定するので、白のままのマスでは保持する
function cellUpdateFor(cell: QuickCell, currentState: number): CellUpdate {
  if (cell.black) return { state: CELL_BLACK, charactor: "" };
  return {
    state: currentState === CELL_DOUBLE ? CELL_DOUBLE : CELL_WHITE,
    charactor: cell.char,
  };
}

export function applyQuickInput(
  document: ProjectDocument,
  size: number,
  cells: QuickCell[][],
): ProjectDocument {
  const resized =
    size === document.data.cell.board_size ? document : resizeBoard(document, size);
  const updates = [];
  for (let r = 0; r < size; r++) {
    for (let c = 0; c < size; c++) {
      const current = getDisplayCell(resized.data, r, c).state;
      updates.push({ row: r, col: c, update: cellUpdateFor(cells[r][c], current) });
    }
  }
  return updateCells(resized, updates);
}

// 盤面への直接入力：選択マスから指定方向へ1文字ずつ書き込む
export function typeIntoBoard(
  document: ProjectDocument,
  start: { row: number; col: number },
  direction: "right" | "down",
  text: string,
): { document: ProjectDocument; cursor: { row: number; col: number } } {
  const size = document.data.cell.board_size;
  let { row, col } = start;
  const updates = [];
  const chars = Array.from(text);
  for (let i = 0; i < chars.length; i++) {
    const char = chars[i];
    if (/[\s　]/.test(char)) {
      // 空白は「何もせず次のマスへ」
    } else {
      const current = getDisplayCell(document.data, row, col).state;
      updates.push({ row, col, update: cellUpdateFor(interpretChar(char), current) });
    }
    const nextRow = direction === "down" ? row + 1 : row;
    const nextCol = direction === "right" ? col + 1 : col;
    if (nextRow >= size || nextCol >= size) {
      // 盤の端では止まる（残りの文字は書き込まない）
      if (i < chars.length - 1) break;
      continue;
    }
    row = nextRow;
    col = nextCol;
  }
  return { document: updateCells(document, updates), cursor: { row, col } };
}
