import { readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";
import {
  CELL_BLACK,
  CELL_DOUBLE,
  clearBoardAndKeys,
  getPlainText,
  makeNewProject,
  parseProjectJson,
  serializeProject,
  setKeyText,
  setTitleText,
  updateCells,
} from "../src/model/project";
import {
  applyQuickInput,
  formatQuickInput,
  parseQuickInput,
  typeIntoBoard,
} from "../src/model/quick-input";

const sample = readFileSync(new URL("../../save/nasu/data.json", import.meta.url), "utf-8");

describe("プロジェクトの読み書き", () => {
  it("デスクトップ版で保存した data.json を読み、カギ番号と答えが一致する", () => {
    const original = JSON.parse(sample);
    const document = parseProjectJson(sample);
    for (const direction of ["row_key", "col_key"] as const) {
      document.data.key[direction].forEach((key, index) => {
        const source = original.data.key[direction][index];
        expect(getPlainText(key.key_name)).toBe(getPlainText(source.key_name));
        expect(key.answer).toBe(source.answer);
      });
    }
  });

  it("編集していないデータは保存しても内容が変わらない", () => {
    const original = JSON.parse(sample);
    const saved = JSON.parse(serializeProject(parseProjectJson(sample)));
    expect(saved.data.cell.grid_data).toEqual(original.data.cell.grid_data);
    expect(saved.data.key.row_key).toEqual(original.data.key.row_key);
    expect(saved.data.key.col_key).toEqual(original.data.key.col_key);
    expect(saved.data.world).toEqual(original.data.world);
  });

  it("カギ文を編集しても黒塗りの指定は残る", () => {
    const document = parseProjectJson(sample);
    const before = document.data.key.row_key[0].text;
    const next = setKeyText(document, "row_key", 0, "新しい文");
    expect(next.data.key.row_key[0].text).toEqual(["新しい文", ...before.slice(1)]);
    expect(getPlainText(document.data.key.row_key[0].text)).not.toBe("新しい文");
  });

  it("指示文は world.title_text にも書き込む", () => {
    const next = setTitleText(makeNewProject(), "問題");
    expect(next.data.title_text).toEqual(["問題"]);
    expect(next.data.world.title_text).toBe("問題");
  });

  it("新規プロジェクトはデスクトップ版の既定値を持つ", () => {
    const document = makeNewProject(6);
    expect(document.data.cell.board_size).toBe(6);
    expect(document.data.key.row_key).toHaveLength(80);
    expect(document.data.world.format_title).toBeDefined();
    expect(getPlainText(document.data.key.row_key[5].key_name)).toBe("6");
    expect(document.data.key.row_key[6].answer).toBe("");
  });

  it("全消去で盤面・カギ文・指示文が消える", () => {
    const cleared = clearBoardAndKeys(parseProjectJson(sample));
    const cells = cleared.data.cell.grid_data.flat();
    expect(cells.every((cell) => cell.state === 0 && cell.charactor === "")).toBe(true);
    expect(cleared.data.key.row_key.every((key) => key.text.length === 1 && key.text[0] === "")).toBe(true);
    expect(cleared.data.title_text).toEqual([""]);
  });

  it("形式の違うJSONはエラーにする", () => {
    expect(() => parseProjectJson("{}")).toThrow();
    expect(() => parseProjectJson("not json")).toThrow();
  });
});

describe("盤面の一括入力", () => {
  it("盤面をテキストにして戻すと同じ盤面になる", () => {
    const document = parseProjectJson(sample);
    const text = formatQuickInput(document.data);
    expect(text.split("\n")[0]).toBe("か＊つなよし");
    const parsed = parseQuickInput(text);
    if (!parsed.ok) throw new Error("parse failed");
    const applied = applyQuickInput(makeNewProject(), parsed.size, parsed.cells);
    expect(applied.data.cell.grid_data).toEqual(document.data.cell.grid_data);
  });

  it("黒マス・空白マスの記号と区切りの空白を解釈する", () => {
    const parsed = parseQuickInput("あ*い・\nう ■ え .\n\nおかきく\nけこさし\n");
    expect(parsed.ok).toBe(true);
    if (!parsed.ok) return;
    expect(parsed.size).toBe(4);
    expect(parsed.cells[0][1]).toEqual({ black: true });
    expect(parsed.cells[0][3]).toEqual({ black: false, char: "" });
    expect(parsed.cells[1][1]).toEqual({ black: true });
  });

  it("行の長さが揃っていない行を報告する", () => {
    const parsed = parseQuickInput("ああああ\nああ\nああああ\nああああ");
    expect(parsed.ok).toBe(false);
    if (parsed.ok) return;
    expect(parsed.errors).toEqual([
      { line: 2, message: "2行目が2マスです（4行なので4マス必要）。" },
    ]);
  });

  it("盤のサイズ外はエラーにする", () => {
    const parsed = parseQuickInput("あああ\nあああ\nあああ");
    expect(parsed.ok).toBe(false);
  });

  it("二重マスは一括入力で文字を変えても残る", () => {
    let document = makeNewProject(4);
    document = updateCells(document, [{ row: 1, col: 1, update: { state: CELL_DOUBLE } }]);
    const parsed = parseQuickInput("ああああ\nいいいい\nうううう\nええ＊え");
    if (!parsed.ok) throw new Error("parse failed");
    const applied = applyQuickInput(document, parsed.size, parsed.cells);
    expect(applied.data.cell.grid_data[1][1]).toEqual({ state: CELL_DOUBLE, charactor: "い" });
    expect(applied.data.cell.grid_data[3][2].state).toBe(CELL_BLACK);
  });

  it("サイズが変わると盤も変わり、答えも更新される", () => {
    const parsed = parseQuickInput("あいうえお\nかきくけこ\nさしすせそ\nたちつてと\nなにぬねの");
    if (!parsed.ok) throw new Error("parse failed");
    const applied = applyQuickInput(makeNewProject(4), parsed.size, parsed.cells);
    expect(applied.data.cell.board_size).toBe(5);
    expect(applied.data.key.row_key[0].answer).toBe("あかさたな");
    expect(applied.data.key.col_key[0].answer).toBe("あいうえお");
  });
});

describe("盤面への直接入力", () => {
  it("右方向に書き込み、端で止まる", () => {
    const result = typeIntoBoard(makeNewProject(4), { row: 0, col: 1 }, "right", "からすみ");
    const row = result.document.data.cell.grid_data[0].map((cell) => cell.charactor);
    expect(row).toEqual(["", "か", "ら", "す"]);
    expect(result.cursor).toEqual({ row: 0, col: 3 });
  });

  it("下方向に書き込み、＊で黒マスにする", () => {
    const result = typeIntoBoard(makeNewProject(4), { row: 0, col: 0 }, "down", "あ＊い");
    const column = result.document.data.cell.grid_data.map((row) => row[0]);
    expect(column[0].charactor).toBe("あ");
    expect(column[1].state).toBe(CELL_BLACK);
    expect(column[2].charactor).toBe("い");
    expect(result.cursor).toEqual({ row: 3, col: 0 });
  });

  it("転置表示では画面上の位置に書き込む", () => {
    const document = makeNewProject(4);
    document.data.cell.board_trans = 1;
    const result = typeIntoBoard(document, { row: 0, col: 0 }, "right", "あい");
    expect(result.document.data.cell.grid_data[1][0].charactor).toBe("い");
  });
});
