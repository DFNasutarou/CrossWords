export type CellData = {
  state: number;
  charactor: string;
};

export type CellSection = {
  board_size: number;
  grid_data: CellData[][];
  board_trans?: number;
};

export type ClueData = {
  key_name?: unknown;
  text?: unknown;
  answer?: unknown;
};

export type KeySection = {
  row_title?: unknown;
  col_title?: unknown;
  row_key?: ClueData[];
  col_key?: ClueData[];
};

export type ProjectData = {
  cell: CellSection;
  key?: KeySection;
  world?: Record<string, unknown>;
  title_text?: unknown;
};

export type ProjectDocument = {
  format_version?: number;
  data: ProjectData;
};

export type NumberedCell = CellData & {
  number: number | null;
  sourceRow: number;
  sourceCol: number;
};

export type DisplayClue = {
  number: string;
  text: string;
  answer: string;
};

const MIN_BOARD_SIZE = 4;
const MAX_BOARD_SIZE = 9;

export function makeEmptyProject(size = 5): ProjectDocument {
  const grid = Array.from({ length: size }, () =>
    Array.from({ length: size }, () => ({
      state: 0,
      charactor: "",
    })),
  );

  return {
    format_version: 2,
    data: {
      cell: {
        board_size: size,
        grid_data: grid,
        board_trans: 0,
      },
      key: {
        row_title: "タテのカギ",
        col_title: "ヨコのカギ",
        row_key: [],
        col_key: [],
      },
      world: {
        title_text: "指示文",
        board_number: 1,
        board_text: 1,
      },
      title_text: ["指示文"],
    },
  };
}

export function parseProjectDocument(value: unknown): ProjectDocument {
  if (!isRecord(value) || !isRecord(value.data)) {
    throw new Error("data項目が見つかりません");
  }

  const data = value.data;
  if (!isRecord(data.cell)) {
    throw new Error("盤面データが見つかりません");
  }

  const size = data.cell.board_size;
  const grid = data.cell.grid_data;
  if (
    !Number.isInteger(size) ||
    typeof size !== "number" ||
    size < MIN_BOARD_SIZE ||
    size > MAX_BOARD_SIZE
  ) {
    throw new Error("盤面サイズは4～9の範囲である必要があります");
  }
  if (!Array.isArray(grid) || grid.length < size) {
    throw new Error("盤面の行数が不足しています");
  }

  const normalizedGrid = grid.slice(0, size).map((row, rowIndex) => {
    if (!Array.isArray(row) || row.length < size) {
      throw new Error(`${rowIndex + 1}行目のマス数が不足しています`);
    }
    return row.slice(0, size).map(normalizeCell);
  });

  const formatVersion = value.format_version;
  if (
    formatVersion !== undefined &&
    formatVersion !== 0 &&
    formatVersion !== 1 &&
    formatVersion !== 2
  ) {
    throw new Error(`未対応の保存形式です: version ${formatVersion}`);
  }

  return {
    ...(value as ProjectDocument),
    format_version: formatVersion ?? 0,
    data: {
      ...(data as ProjectData),
      cell: {
        ...(data.cell as CellSection),
        board_size: size,
        grid_data: normalizedGrid,
      },
    },
  };
}

export function getInstruction(project: ProjectDocument): string {
  const title = extractText(project.data.title_text);
  if (title) return title;
  const worldTitle = project.data.world?.title_text;
  return typeof worldTitle === "string" && worldTitle
    ? worldTitle
    : "指示文";
}

export function getDisplayGrid(project: ProjectDocument): NumberedCell[][] {
  const { board_size: size, grid_data: grid, board_trans: transposed } =
    project.data.cell;
  const numbers = computeNumbers(grid, size);
  const logical = grid.map((row, rowIndex) =>
    row.map((cell, colIndex) => ({
      ...cell,
      number: numbers[rowIndex][colIndex],
      sourceRow: rowIndex,
      sourceCol: colIndex,
    })),
  );

  if (!transposed) return logical;
  return Array.from({ length: size }, (_, row) =>
    Array.from({ length: size }, (_, col) => logical[col][row]),
  );
}

export function getClues(
  project: ProjectDocument,
  direction: "vertical" | "horizontal",
): { title: string; clues: DisplayClue[] } {
  const key = project.data.key;
  const vertical = direction === "vertical";
  const title =
    extractText(vertical ? key?.row_title : key?.col_title) ||
    (vertical ? "タテのカギ" : "ヨコのカギ");
  const source = vertical ? key?.row_key : key?.col_key;
  const clues = (source ?? [])
    .map((clue) => ({
      number: extractText(clue.key_name),
      text: extractText(clue.text),
      answer: extractText(clue.answer),
    }))
    .filter((clue) => clue.number || clue.text || clue.answer);

  return { title, clues };
}

export function shouldShow(
  project: ProjectDocument,
  key: "board_number" | "board_text",
): boolean {
  return project.data.world?.[key] !== 0;
}

function computeNumbers(grid: CellData[][], size: number): (number | null)[][] {
  const numbers = Array.from({ length: size }, () =>
    Array<number | null>(size).fill(null),
  );
  let nextNumber = 1;

  for (let row = 0; row < size; row += 1) {
    for (let col = 0; col < size; col += 1) {
      if (isBlack(grid[row][col])) continue;

      const startsVertical =
        (row === 0 || isBlack(grid[row - 1][col])) &&
        row + 1 < size &&
        !isBlack(grid[row + 1][col]);
      const startsHorizontal =
        (col === 0 || isBlack(grid[row][col - 1])) &&
        col + 1 < size &&
        !isBlack(grid[row][col + 1]);

      if (startsVertical || startsHorizontal) {
        numbers[row][col] = nextNumber;
        nextNumber += 1;
      }
    }
  }

  return numbers;
}

function normalizeCell(value: unknown): CellData {
  if (!isRecord(value)) {
    throw new Error("マスのデータ形式が正しくありません");
  }
  const state =
    typeof value.state === "number" && [0, 1, 2].includes(value.state)
      ? value.state
      : 0;
  const charactor =
    typeof value.charactor === "string" ? [...value.charactor][0] ?? "" : "";
  return { ...value, state, charactor } as CellData;
}

function extractText(value: unknown): string {
  if (typeof value === "string") return value;
  if (Array.isArray(value) && typeof value[0] === "string") return value[0];
  return "";
}

function isBlack(cell: CellData): boolean {
  return cell.state === 1;
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}
