// デスクトップ版（app/）と同じ data.json 形式を扱うモデル。
// 未対応のフィールド（黒塗り・文中画像・書式など）は触らずにそのまま保持し、
// Web版で保存してもデスクトップ版の情報が失われないようにする。
import defaultDocument from "./default-project.json";
import { computeNumbering, type NumberingMode } from "./numbering";

export const CELL_WHITE = 0;
export const CELL_BLACK = 1;
export const CELL_DOUBLE = 2;

export const MIN_BOARD_SIZE = 4;
export const MAX_BOARD_SIZE = 9;
export const KEY_NUMBER = 80;
export const CURRENT_FORMAT_VERSION = 2;
const SUPPORTED_VERSIONS = [0, 1, 2];

export type CellData = {
  state: number;
  charactor: string;
  [extra: string]: unknown;
};

// テキスト欄の保存形式: [本文, 黒塗り矩形..., {inline_images: [...]}]
export type TextContent = unknown[];

export type KeyEntry = {
  key_name: TextContent;
  text: TextContent;
  answer: string;
  [extra: string]: unknown;
};

export type ProjectData = {
  cell: {
    board_size: number;
    grid_data: CellData[][];
    board_trans: number;
    numbering_mode?: string;
    [extra: string]: unknown;
  };
  key: {
    row_title: TextContent;
    col_title: TextContent;
    row_key: KeyEntry[];
    col_key: KeyEntry[];
    key_trans: number;
    key_sort: number;
    [extra: string]: unknown;
  };
  world: Record<string, unknown> & { title_text: string };
  title_text: TextContent;
  image_assets?: Record<string, unknown>;
  [extra: string]: unknown;
};

export type ProjectDocument = {
  format_version: number;
  data: ProjectData;
};

export class ProjectFormatError extends Error {}

function clone<T>(value: T): T {
  return structuredClone(value);
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function emptyKeyEntry(): KeyEntry {
  return { key_name: [""], text: [""], answer: "" };
}

function emptyCell(): CellData {
  return { state: CELL_WHITE, charactor: "" };
}

// ---------- テキスト欄 ----------

export function getPlainText(content: unknown): string {
  if (typeof content === "string") return content;
  if (Array.isArray(content) && content.length > 0) return String(content[0]);
  return "";
}

export function setPlainText(content: unknown, text: string): TextContent {
  // 黒塗り矩形や文中画像（先頭以外の要素）はそのまま残す
  if (Array.isArray(content) && content.length > 0) {
    return [text, ...content.slice(1)];
  }
  return [text];
}

export function countBlackouts(content: unknown): number {
  if (!Array.isArray(content)) return 0;
  return content.slice(1).filter((value) => Array.isArray(value)).length;
}

export function countInlineImages(content: unknown): number {
  if (!Array.isArray(content)) return 0;
  for (const value of content.slice(1)) {
    if (isRecord(value) && Array.isArray(value.inline_images)) {
      return value.inline_images.length;
    }
  }
  return 0;
}

// ---------- 読み込み・新規作成 ----------

export function makeNewProject(size = 5): ProjectDocument {
  const document = clone(defaultDocument) as unknown as ProjectDocument;
  resizeBoardInPlace(document.data, size);
  return refreshNumbering(document);
}

export function parseProjectJson(text: string): ProjectDocument {
  let value: unknown;
  try {
    value = JSON.parse(text);
  } catch {
    throw new ProjectFormatError("JSONとして読み込めませんでした。");
  }
  return normalizeProject(value);
}

export function normalizeProject(value: unknown): ProjectDocument {
  if (!isRecord(value) || !isRecord(value.data)) {
    throw new ProjectFormatError("CrossMakerのプロジェクトファイルではありません。");
  }
  const version =
    typeof value.format_version === "number" ? value.format_version : 0;
  if (!SUPPORTED_VERSIONS.includes(version)) {
    throw new ProjectFormatError(`未対応のプロジェクト形式です: version ${version}`);
  }

  const template = clone(defaultDocument) as unknown as ProjectDocument;
  const data = clone(value.data) as Record<string, unknown>;

  // 足りないセクション・項目はデスクトップ版の既定値で補う
  const cell = isRecord(data.cell) ? data.cell : {};
  const size = Number(cell.board_size);
  if (!Number.isInteger(size) || size < MIN_BOARD_SIZE || size > MAX_BOARD_SIZE) {
    throw new ProjectFormatError("盤のサイズが不正です（4～9に対応）。");
  }
  if (!Array.isArray(cell.grid_data)) {
    throw new ProjectFormatError("盤面データがありません。");
  }
  const grid: CellData[][] = [];
  for (let r = 0; r < size; r++) {
    const sourceRow = Array.isArray(cell.grid_data[r]) ? cell.grid_data[r] : [];
    const row: CellData[] = [];
    for (let c = 0; c < size; c++) {
      const source = sourceRow[c];
      row.push(
        isRecord(source)
          ? {
              ...source,
              state: Number(source.state) || CELL_WHITE,
              charactor: typeof source.charactor === "string" ? source.charactor : "",
            }
          : emptyCell(),
      );
    }
    grid.push(row);
  }
  data.cell = {
    ...template.data.cell,
    ...cell,
    board_size: size,
    grid_data: grid,
    board_trans: Number(cell.board_trans) ? 1 : 0,
  };

  const key = isRecord(data.key) ? data.key : {};
  const padKeys = (list: unknown): KeyEntry[] => {
    const source = Array.isArray(list) ? list : [];
    return Array.from({ length: KEY_NUMBER }, (_, index) => {
      const entry = source[index];
      return isRecord(entry)
        ? ({ ...emptyKeyEntry(), ...entry } as KeyEntry)
        : emptyKeyEntry();
    });
  };
  data.key = {
    ...template.data.key,
    ...key,
    row_key: padKeys(key.row_key),
    col_key: padKeys(key.col_key),
    key_trans: Number(key.key_trans) ? 1 : 0,
    key_sort: Number(key.key_sort) ? 1 : 0,
  };

  const world = isRecord(data.world) ? data.world : {};
  data.world = { ...template.data.world, ...world };
  if (data.title_text === undefined) {
    data.title_text = [String((data.world as Record<string, unknown>).title_text ?? "")];
  }
  // デスクトップ版は読み込み時に world.title_text を指示文として表示する
  data.title_text = setPlainText(
    data.title_text,
    String((data.world as Record<string, unknown>).title_text ?? getPlainText(data.title_text)),
  );
  if (!isRecord(data.image_assets)) data.image_assets = {};

  return refreshNumbering({
    format_version: CURRENT_FORMAT_VERSION,
    data: data as unknown as ProjectData,
  });
}

export function serializeProject(document: ProjectDocument): string {
  return JSON.stringify(
    { format_version: CURRENT_FORMAT_VERSION, data: document.data },
    null,
    2,
  );
}

// ---------- 盤面 ----------

export function getNumberingMode(data: ProjectData): NumberingMode {
  return data.cell.numbering_mode === "left_priority" ? "left_priority" : "top_priority";
}

// 盤の転置表示（board_trans）を考慮して、画面上の位置をデータ上の位置へ変換する
export function toDataPosition(data: ProjectData, row: number, col: number): [number, number] {
  return data.cell.board_trans ? [col, row] : [row, col];
}

export function getDisplayCell(data: ProjectData, row: number, col: number): CellData {
  const [r, c] = toDataPosition(data, row, col);
  return data.cell.grid_data[r][c];
}

function resizeBoardInPlace(data: ProjectData, size: number) {
  const old = data.cell.grid_data;
  data.cell.grid_data = Array.from({ length: size }, (_, r) =>
    Array.from({ length: size }, (_, c) => old[r]?.[c] ?? emptyCell()),
  );
  data.cell.board_size = size;
}

export function resizeBoard(document: ProjectDocument, size: number): ProjectDocument {
  if (size < MIN_BOARD_SIZE || size > MAX_BOARD_SIZE) return document;
  const next = clone(document);
  resizeBoardInPlace(next.data, size);
  return refreshNumbering(next);
}

export type CellUpdate = { state?: number; charactor?: string };

// 画面上の位置で複数マスをまとめて更新する
export function updateCells(
  document: ProjectDocument,
  updates: { row: number; col: number; update: CellUpdate }[],
): ProjectDocument {
  if (updates.length === 0) return document;
  const next = clone(document);
  for (const { row, col, update } of updates) {
    const [r, c] = toDataPosition(next.data, row, col);
    const cell = next.data.cell.grid_data[r]?.[c];
    if (!cell) continue;
    if (update.state !== undefined) cell.state = update.state;
    if (update.charactor !== undefined) cell.charactor = update.charactor;
    // 黒マスに文字は残さない（デスクトップ版の盤面列挙反映と同じ扱い）
    if (cell.state === CELL_BLACK) cell.charactor = "";
  }
  return refreshNumbering(next);
}

export function setNumberingMode(document: ProjectDocument, mode: NumberingMode): ProjectDocument {
  const next = clone(document);
  next.data.cell.numbering_mode = mode;
  return refreshNumbering(next);
}

// カギ番号と答えを盤面から計算し直し、カギ欄に書き込む。
// カギ文は「何番目のカギか」で紐づく（デスクトップ版と同じ）。
export function refreshNumbering(document: ProjectDocument): ProjectDocument {
  const { data } = document;
  const states = data.cell.grid_data.map((row) => row.map((cell) => cell.state === CELL_BLACK));
  const chars = data.cell.grid_data.map((row) => row.map((cell) => cell.charactor));
  const result = computeNumbering(states, chars, getNumberingMode(data));
  const apply = (keys: KeyEntry[], entries: { number: number; answer: string }[]) => {
    keys.forEach((key, index) => {
      const entry = entries[index];
      key.key_name = setPlainText(key.key_name, entry ? String(entry.number) : "");
      key.answer = entry ? entry.answer : "";
    });
  };
  apply(data.key.row_key, result.vertical);
  apply(data.key.col_key, result.horizontal);
  return document;
}

export function getBoardNumbers(data: ProjectData): (number | null)[][] {
  const states = data.cell.grid_data.map((row) => row.map((cell) => cell.state === CELL_BLACK));
  const chars = data.cell.grid_data.map((row) => row.map((cell) => cell.charactor));
  return computeNumbering(states, chars, getNumberingMode(data)).numbers;
}

export function clearBoardAndKeys(document: ProjectDocument): ProjectDocument {
  const next = clone(document);
  for (const row of next.data.cell.grid_data) {
    for (const cell of row) {
      cell.state = CELL_WHITE;
      cell.charactor = "";
    }
  }
  // 本文・黒塗り・文中画像を消す。カギ番号と見出しは文字を残して黒塗りだけ消す
  for (const key of [...next.data.key.row_key, ...next.data.key.col_key]) {
    key.text = [""];
    key.key_name = [getPlainText(key.key_name)];
  }
  next.data.key.row_title = [getPlainText(next.data.key.row_title)];
  next.data.key.col_title = [getPlainText(next.data.key.col_title)];
  next.data.title_text = [""];
  next.data.world.title_text = "";
  return refreshNumbering(next);
}

// ---------- 文章 ----------

export type KeyDirection = "row_key" | "col_key";

export function setKeyText(
  document: ProjectDocument,
  direction: KeyDirection,
  index: number,
  text: string,
): ProjectDocument {
  const next = clone(document);
  const key = next.data.key[direction][index];
  if (!key) return document;
  key.text = setPlainText(key.text, text);
  return next;
}

export function setTitleText(document: ProjectDocument, text: string): ProjectDocument {
  const next = clone(document);
  next.data.title_text = setPlainText(next.data.title_text, text);
  next.data.world.title_text = text;
  return next;
}

export function setKeyHeading(
  document: ProjectDocument,
  which: "row_title" | "col_title",
  text: string,
): ProjectDocument {
  const next = clone(document);
  next.data.key[which] = setPlainText(next.data.key[which], text);
  return next;
}
