import { useCallback, useEffect, useReducer, useRef, useState } from "react";
import { BoardEditor, type BoardMode, type Direction, type Position } from "./components/BoardEditor";
import { CluePanel } from "./components/CluePanel";
import { QuickInputPanel } from "./components/QuickInputPanel";
import { historyReducer, initHistory } from "./model/history";
import {
  MAX_BOARD_SIZE,
  MIN_BOARD_SIZE,
  clearBoardAndKeys,
  getNumberingMode,
  getPlainText,
  makeNewProject,
  resizeBoard,
  setKeyHeading,
  setKeyText,
  setNumberingMode,
  setTitleText,
  updateCells,
  type ProjectDocument,
} from "./model/project";
import { applyQuickInput, typeIntoBoard } from "./model/quick-input";
import { loadSession, saveSession } from "./storage/autosave";
import {
  downloadProject,
  isAbortError,
  openProjectFile,
  openProjectFolder,
  readUploadedFile,
  saveAsFolder,
  supportsFileSystemAccess,
  targetName,
  writeProject,
  type FileTarget,
  type OpenedProject,
} from "./storage/files";

const UNTITLED = "新しいプロジェクト";

export function App() {
  const [history, dispatch] = useReducer(historyReducer, undefined, () => initHistory(makeNewProject()));
  const document = history.present;
  const data = document.data;
  const [target, setTarget] = useState<FileTarget | null>(null);
  const [name, setName] = useState(UNTITLED);
  const [dirty, setDirty] = useState(false);
  const [message, setMessage] = useState("");
  const [restored, setRestored] = useState(false);
  const [mode, setMode] = useState<BoardMode>("input");
  const [direction, setDirection] = useState<Direction>("right");
  const [newSize, setNewSize] = useState(5);
  const uploadRef = useRef<HTMLInputElement>(null);
  const fsAccess = supportsFileSystemAccess();

  const change = useCallback((next: ProjectDocument, coalesceKey?: string) => {
    dispatch({ type: "change", document: next, coalesceKey });
    setDirty(true);
  }, []);

  // ---------- 自動保存と復元 ----------
  useEffect(() => {
    loadSession().then((session) => {
      if (session) {
        dispatch({ type: "reset", document: session.document });
        setTarget(session.target);
        setName(session.name);
        setDirty(session.dirty);
        setMessage("前回の編集内容を復元しました。");
      }
      setRestored(true);
    });
  }, []);

  useEffect(() => {
    if (!restored) return;
    const timer = window.setTimeout(() => {
      void saveSession({ document, name, target, dirty, savedAt: new Date().toISOString() });
    }, 400);
    return () => window.clearTimeout(timer);
  }, [document, name, target, dirty, restored]);

  useEffect(() => {
    const warn = (event: BeforeUnloadEvent) => {
      if (dirty) event.preventDefault();
    };
    window.addEventListener("beforeunload", warn);
    return () => window.removeEventListener("beforeunload", warn);
  }, [dirty]);

  // ---------- ファイル操作 ----------
  const confirmDiscard = () =>
    !dirty || window.confirm("保存していない変更があります。破棄して続けますか？");

  const loadOpened = (opened: OpenedProject) => {
    dispatch({ type: "reset", document: opened.document });
    setTarget(opened.target);
    setName(opened.name);
    setDirty(false);
    setMessage(`${opened.name} を開きました。`);
  };

  const handleError = (error: unknown) => {
    if (isAbortError(error)) return;
    setMessage(error instanceof Error ? error.message : String(error));
  };

  const newProject = () => {
    if (!confirmDiscard()) return;
    dispatch({ type: "reset", document: makeNewProject(newSize) });
    setTarget(null);
    setName(UNTITLED);
    setDirty(false);
    setMessage(`${newSize}×${newSize} の新しいプロジェクトを作りました。`);
  };

  const openFolder = async () => {
    if (!confirmDiscard()) return;
    try {
      loadOpened(await openProjectFolder());
    } catch (error) {
      handleError(error);
    }
  };

  const openFile = async () => {
    if (!confirmDiscard()) return;
    if (!fsAccess) {
      uploadRef.current?.click();
      return;
    }
    try {
      loadOpened(await openProjectFile());
    } catch (error) {
      handleError(error);
    }
  };

  const saveAs = async () => {
    try {
      const saved = await saveAsFolder(document);
      if (!saved) return;
      setTarget(saved);
      setName(targetName(saved));
      setDirty(false);
      setMessage(`${targetName(saved)} に保存しました。`);
    } catch (error) {
      handleError(error);
    }
  };

  const save = async () => {
    if (!fsAccess) {
      downloadProject(document);
      setDirty(false);
      setMessage("data.json をダウンロードしました。");
      return;
    }
    if (!target) {
      await saveAs();
      return;
    }
    try {
      await writeProject(target, document);
      setDirty(false);
      setMessage(`${targetName(target)} に上書き保存しました。`);
    } catch (error) {
      handleError(error);
    }
  };

  const clearAll = () => {
    if (
      !window.confirm(
        "盤面の文字・黒マスと、指示文・すべてのカギ文・黒塗り・差し込み画像を消します。\nこの操作を実行しますか？",
      )
    ) {
      return;
    }
    change(clearBoardAndKeys(document));
  };

  // ---------- キーボードショートカット ----------
  const saveRef = useRef(save);
  saveRef.current = save;
  useEffect(() => {
    const handler = (event: KeyboardEvent) => {
      if (!(event.ctrlKey || event.metaKey)) return;
      const key = event.key.toLowerCase();
      if (key === "s") {
        event.preventDefault();
        void saveRef.current();
      } else if (key === "z" && !event.shiftKey) {
        // 文章欄の中ではブラウザ標準の取り消しを使う
        if (isTextField(event.target)) return;
        event.preventDefault();
        dispatch({ type: "undo" });
      } else if (key === "y" || (key === "z" && event.shiftKey)) {
        if (isTextField(event.target)) return;
        event.preventDefault();
        dispatch({ type: "redo" });
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, []);

  const undo = () => {
    dispatch({ type: "undo" });
    setDirty(true);
  };
  const redo = () => {
    dispatch({ type: "redo" });
    setDirty(true);
  };

  const size = data.cell.board_size;

  return (
    <div className="app">
      <header className="toolbar">
        <h1>CrossMaker</h1>
        <div className="toolbar-group">
          <select value={newSize} onChange={(event) => setNewSize(Number(event.target.value))} aria-label="新規の盤サイズ">
            {sizes().map((n) => (
              <option key={n} value={n}>
                {n}×{n}
              </option>
            ))}
          </select>
          <button type="button" onClick={newProject}>新規</button>
        </div>
        <div className="toolbar-group">
          {fsAccess && <button type="button" onClick={openFolder}>フォルダを開く</button>}
          <button type="button" onClick={openFile}>{fsAccess ? "data.json を開く" : "開く"}</button>
          <button type="button" className="primary" onClick={save} title="Ctrl+S">
            {fsAccess ? "保存" : "ダウンロード保存"}
          </button>
          {fsAccess && <button type="button" onClick={saveAs}>フォルダに保存…</button>}
          {fsAccess && <button type="button" onClick={() => downloadProject(document)}>ダウンロード</button>}
        </div>
        <div className="toolbar-group">
          <button type="button" onClick={undo} disabled={history.past.length === 0} title="Ctrl+Z">元に戻す</button>
          <button type="button" onClick={redo} disabled={history.future.length === 0} title="Ctrl+Y">やり直し</button>
          <button type="button" className="danger" onClick={clearAll}>盤面とカギを全部消す</button>
        </div>
        <input
          ref={uploadRef}
          type="file"
          accept=".json,application/json"
          hidden
          onChange={async (event) => {
            const file = event.target.files?.[0];
            event.target.value = "";
            if (!file) return;
            try {
              loadOpened(await readUploadedFile(file));
            } catch (error) {
              handleError(error);
            }
          }}
        />
      </header>

      <div className="statusbar">
        <span className="file-name">
          {name}
          {dirty && <span className="dirty">（未保存）</span>}
        </span>
        {message && <span className="message">{message}</span>}
        {!fsAccess && (
          <span className="message">このブラウザでは上書き保存できません。保存はダウンロードになります（Chrome / Edge 推奨）。</span>
        )}
      </div>

      <main className="layout">
        <div className="column">
          <section className="panel">
            <h2>指示文</h2>
            <textarea
              className="title-input"
              value={getPlainText(data.title_text)}
              rows={Math.max(1, getPlainText(data.title_text).split("\n").length)}
              onChange={(event) => change(setTitleText(document, event.target.value), "title")}
              aria-label="指示文"
            />
          </section>

          <section className="panel">
            <div className="board-tools">
              <div className="segmented" role="radiogroup" aria-label="盤面の操作">
                {(
                  [
                    ["input", "文字入力"],
                    ["black", "黒マス"],
                    ["double", "二重マス"],
                  ] as [BoardMode, string][]
                ).map(([value, label]) => (
                  <button
                    key={value}
                    type="button"
                    role="radio"
                    aria-checked={mode === value}
                    className={mode === value ? "active" : ""}
                    onClick={() => setMode(value)}
                  >
                    {label}
                  </button>
                ))}
              </div>
              {mode === "input" && (
                <button
                  type="button"
                  onClick={() => setDirection(direction === "right" ? "down" : "right")}
                  title="Tab キー、または選択中のマスをもう一度クリックでも切り替わります"
                >
                  入力方向：{direction === "right" ? "→ 右" : "↓ 下"}
                </button>
              )}
              <label>
                盤サイズ
                <select
                  value={size}
                  onChange={(event) => change(resizeBoard(document, Number(event.target.value)))}
                >
                  {sizes().map((n) => (
                    <option key={n} value={n}>
                      {n}×{n}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                番号
                <select
                  value={getNumberingMode(data)}
                  onChange={(event) =>
                    change(setNumberingMode(document, event.target.value as "top_priority" | "left_priority"))
                  }
                >
                  <option value="top_priority">上優先</option>
                  <option value="left_priority">左優先</option>
                </select>
              </label>
            </div>
            <p className="hint">{modeHint(mode)}</p>
            <BoardEditor
              data={data}
              mode={mode}
              direction={direction}
              onDirectionChange={setDirection}
              onUpdateCells={(updates) => change(updateCells(document, updates))}
              onType={(start: Position, text: string) => {
                const result = typeIntoBoard(document, start, direction, text);
                change(result.document);
                return result.cursor;
              }}
            />
          </section>

          <QuickInputPanel data={data} onApply={(n, cells) => change(applyQuickInput(document, n, cells))} />
        </div>

        <div className="column">
          <CluePanel
            data={data}
            onKeyText={(dir, index, text) => change(setKeyText(document, dir, index, text), `${dir}-${index}`)}
            onHeading={(which, text) => change(setKeyHeading(document, which, text), which)}
          />
        </div>
      </main>
    </div>
  );
}

function sizes() {
  return Array.from({ length: MAX_BOARD_SIZE - MIN_BOARD_SIZE + 1 }, (_, i) => MIN_BOARD_SIZE + i);
}

function isTextField(target: EventTarget | null) {
  return (
    target instanceof HTMLTextAreaElement ||
    (target instanceof HTMLInputElement && !target.classList.contains("board-input"))
  );
}

function modeHint(mode: BoardMode) {
  switch (mode) {
    case "input":
      return "マスを選んで文字を打つと、入力方向へ1文字ずつ進みます。＊で黒マス、・で空白。矢印キーで移動、Backspace / Delete で消去。";
    case "black":
      return "クリックしたマスの白・黒を切り替えます。";
    case "double":
      return "クリックした白マスの二重マスを切り替えます。";
  }
}
