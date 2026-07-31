"use client";

import {
  useEffect,
  useMemo,
  useRef,
  useState,
  type ChangeEvent,
  type DragEvent,
} from "react";
import {
  getClues,
  getDisplayGrid,
  getInstruction,
  makeEmptyProject,
  parseProjectDocument,
  shouldShow,
  type DisplayClue,
  type ProjectDocument,
} from "./project-model";
import {
  clearProjects,
  createProjectId,
  deleteProject,
  getStorageSummary,
  listProjects,
  loadLastProject,
  requestPersistentStorage,
  saveProject,
  type StorageSummary,
  type StoredProject,
} from "./project-storage";

type SaveState = "loading" | "saved" | "error";

export function CrosswordApp() {
  const [project, setProject] = useState<ProjectDocument>(() =>
    makeEmptyProject(),
  );
  const [projectId, setProjectId] = useState(() => createProjectId());
  const [fileName, setFileName] = useState("新しい盤面.json");
  const [saveState, setSaveState] = useState<SaveState>("loading");
  const [message, setMessage] = useState("前回のプロジェクトを確認しています");
  const [ready, setReady] = useState(false);
  const [storageOpen, setStorageOpen] = useState(false);
  const [storedProjects, setStoredProjects] = useState<StoredProject[]>([]);
  const [storageSummary, setStorageSummary] = useState<StorageSummary>({
    usage: null,
    quota: null,
    persistent: false,
  });
  const [storageBusy, setStorageBusy] = useState(false);
  const fileInput = useRef<HTMLInputElement>(null);
  const skipNextSave = useRef(false);

  useEffect(() => {
    let active = true;
    loadLastProject()
      .then((stored) => {
        if (!active) return;
        if (stored) {
          setProject(parseProjectDocument(stored.document));
          setProjectId(stored.id);
          setFileName(stored.fileName);
          setMessage("前回開いていたプロジェクトを復元しました");
        } else {
          setMessage("新しい盤面を表示しています");
        }
        setSaveState("saved");
      })
      .catch(() => {
        if (!active) return;
        setSaveState("error");
        setMessage("ブラウザ内の保存領域を利用できません");
      })
      .finally(() => {
        if (active) setReady(true);
      });
    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
    if (!ready) return;
    if (skipNextSave.current) {
      skipNextSave.current = false;
      setSaveState("saved");
      return;
    }
    const stored: StoredProject = {
      id: projectId,
      fileName,
      document: project,
      savedAt: new Date().toISOString(),
    };
    setSaveState("loading");
    const timer = window.setTimeout(() => {
      saveProject(stored)
        .then(() => {
          setSaveState("saved");
          setMessage("この端末に自動保存しました");
          if (storageOpen) void refreshStorage();
        })
        .catch(() => {
          setSaveState("error");
          setMessage("自動保存に失敗しました");
        });
    }, 250);
    return () => window.clearTimeout(timer);
  }, [fileName, project, projectId, ready, storageOpen]);

  useEffect(() => {
    if (storageOpen) void refreshStorage();
  }, [storageOpen]);

  const grid = useMemo(() => getDisplayGrid(project), [project]);
  const vertical = useMemo(() => getClues(project, "vertical"), [project]);
  const horizontal = useMemo(
    () => getClues(project, "horizontal"),
    [project],
  );
  const showNumbers = shouldShow(project, "board_number");
  const showText = shouldShow(project, "board_text");

  async function importFile(file: File) {
    try {
      const text = await file.text();
      const nextProject = parseProjectDocument(JSON.parse(text));
      setProject(nextProject);
      setProjectId(createProjectId());
      setFileName(file.name);
      setMessage(`${file.name} を読み込みました`);
      setSaveState("loading");
    } catch (error) {
      setSaveState("error");
      setMessage(
        error instanceof Error
          ? `読み込みできません: ${error.message}`
          : "読み込みできないファイルです",
      );
    }
  }

  function handleFileChange(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (file) void importFile(file);
    event.target.value = "";
  }

  function handleDrop(event: DragEvent<HTMLElement>) {
    event.preventDefault();
    const file = event.dataTransfer.files?.[0];
    if (file) void importFile(file);
  }

  function startNewProject() {
    setProject(makeEmptyProject());
    setProjectId(createProjectId());
    setFileName("新しい盤面.json");
    setMessage("新しい5×5盤面を作成しました");
  }

  async function refreshStorage() {
    try {
      const [projects, summary] = await Promise.all([
        listProjects(),
        getStorageSummary(),
      ]);
      setStoredProjects(projects);
      setStorageSummary(summary);
    } catch {
      setMessage("保存データの一覧を読み込めませんでした");
    }
  }

  function openStoredProject(stored: StoredProject) {
    setProject(parseProjectDocument(stored.document));
    setProjectId(stored.id);
    setFileName(stored.fileName);
    setStorageOpen(false);
    setMessage(`${stored.fileName} を開きました`);
  }

  async function removeStoredProject(stored: StoredProject) {
    if (
      !window.confirm(
        `「${stored.fileName}」をこの端末の保存データから削除しますか？`,
      )
    ) {
      return;
    }
    setStorageBusy(true);
    const removingCurrent = stored.id === projectId;
    try {
      if (removingCurrent) setReady(false);
      await deleteProject(stored.id);
      if (removingCurrent) {
        setProject(makeEmptyProject());
        setProjectId(createProjectId());
        setFileName("新しい盤面.json");
        skipNextSave.current = true;
        setReady(true);
      }
      await refreshStorage();
      setMessage(`${stored.fileName} を削除しました`);
    } catch {
      setMessage(`${stored.fileName} を削除できませんでした`);
    } finally {
      if (removingCurrent) setReady(true);
      setStorageBusy(false);
    }
  }

  async function removeAllStoredProjects() {
    if (
      !window.confirm(
        "このブラウザに保存したCrossMakerのプロジェクトをすべて削除しますか？",
      )
    ) {
      return;
    }
    setStorageBusy(true);
    setReady(false);
    try {
      await clearProjects();
      setProject(makeEmptyProject());
      setProjectId(createProjectId());
      setFileName("新しい盤面.json");
      skipNextSave.current = true;
      setStoredProjects([]);
      await refreshStorage();
      setMessage("保存データをすべて削除しました");
    } catch {
      setMessage("保存データを削除できませんでした");
    } finally {
      setReady(true);
      setStorageBusy(false);
    }
  }

  async function enablePersistentStorage() {
    setStorageBusy(true);
    try {
      const persistent = await requestPersistentStorage();
      await refreshStorage();
      setMessage(
        persistent
          ? "ブラウザの永続保存を有効にしました"
          : "このブラウザでは永続保存を有効にできませんでした",
      );
    } catch {
      setMessage("永続保存の設定を変更できませんでした");
    } finally {
      setStorageBusy(false);
    }
  }

  function exportProject() {
    const document: ProjectDocument = {
      ...project,
      format_version: 2,
    };
    const blob = new Blob([JSON.stringify(document, null, 2)], {
      type: "application/json",
    });
    const url = URL.createObjectURL(blob);
    const link = window.document.createElement("a");
    link.href = url;
    link.download = fileName.endsWith(".json") ? fileName : `${fileName}.json`;
    link.click();
    URL.revokeObjectURL(url);
    setMessage("JSONファイルを書き出しました");
  }

  return (
    <main
      className="app-shell"
      onDragOver={(event) => event.preventDefault()}
      onDrop={handleDrop}
    >
      <header className="topbar">
        <div className="brand">
          <span className="brand-mark" aria-hidden="true">
            十
          </span>
          <div>
            <p className="eyebrow">CROSSWORD WORKSPACE</p>
            <h1>CrossMaker Web</h1>
          </div>
        </div>
        <div className={`save-status save-status-${saveState}`} role="status">
          <span className="status-dot" aria-hidden="true" />
          {message}
        </div>
      </header>

      <section className="toolbar" aria-label="プロジェクト操作">
        <div className="file-summary">
          <span className="file-label">現在のファイル</span>
          <strong>{fileName}</strong>
        </div>
        <div className="toolbar-actions">
          <button className="button button-subtle" onClick={startNewProject}>
            新規盤面
          </button>
          <button
            className="button button-subtle"
            onClick={() => setStorageOpen(true)}
          >
            保存データ管理
          </button>
          <button
            className="button button-primary"
            onClick={() => fileInput.current?.click()}
          >
            JSONを開く
          </button>
          <button className="button button-dark" onClick={exportProject}>
            JSONを書き出す
          </button>
          <input
            ref={fileInput}
            className="visually-hidden"
            type="file"
            accept=".json,application/json"
            onChange={handleFileChange}
          />
        </div>
      </section>

      <section className="workspace">
        <article className="canvas-card">
          <div className="section-heading">
            <div>
              <p className="section-kicker">PUZZLE PREVIEW</p>
              <h2>{getInstruction(project)}</h2>
            </div>
            <span className="board-size">
              {project.data.cell.board_size} × {project.data.cell.board_size}
            </span>
          </div>

          <div
            className="board"
            style={{
              gridTemplateColumns: `repeat(${grid.length}, minmax(0, 1fr))`,
            }}
            aria-label={`${grid.length}×${grid.length}のクロスワード盤面`}
          >
            {grid.flat().map((cell) => {
              const black = cell.state === 1;
              const double = cell.state === 2;
              return (
                <div
                  className={`cell${black ? " cell-black" : ""}${
                    double ? " cell-double" : ""
                  }`}
                  key={`${cell.sourceRow}-${cell.sourceCol}`}
                  aria-label={
                    black
                      ? "黒マス"
                      : `${cell.number ? `${cell.number}番 ` : ""}${
                          cell.charactor || "空白"
                        }`
                  }
                >
                  {!black && showNumbers && cell.number ? (
                    <span className="cell-number">{cell.number}</span>
                  ) : null}
                  {!black && showText && cell.charactor ? (
                    <span className="cell-character">{cell.charactor}</span>
                  ) : null}
                </div>
              );
            })}
          </div>

          <p className="drop-hint">
            この画面へ既存の <strong>data.json</strong> をドロップしても開けます
          </p>
        </article>

        <aside className="clue-panel">
          <ClueSection title={vertical.title} clues={vertical.clues} />
          <ClueSection title={horizontal.title} clues={horizontal.clues} />
        </aside>
      </section>

      <footer className="local-note">
        <span aria-hidden="true">●</span>
        プロジェクトはこの端末のブラウザ内に保存されます。アカウント登録は不要です。
      </footer>

      {storageOpen ? (
        <StorageManager
          currentProjectId={projectId}
          projects={storedProjects}
          summary={storageSummary}
          busy={storageBusy}
          onClose={() => setStorageOpen(false)}
          onOpen={openStoredProject}
          onDelete={(stored) => void removeStoredProject(stored)}
          onDeleteAll={() => void removeAllStoredProjects()}
          onPersist={() => void enablePersistentStorage()}
        />
      ) : null}
    </main>
  );
}

function ClueSection({
  title,
  clues,
}: {
  title: string;
  clues: DisplayClue[];
}) {
  return (
    <section className="clue-section">
      <div className="clue-heading">
        <h2>{title}</h2>
        <span>{clues.length} keys</span>
      </div>
      {clues.length ? (
        <ol className="clue-list">
          {clues.map((clue, index) => (
            <li className="clue-item" key={`${clue.number}-${index}`}>
              <span className="clue-number">{clue.number || "—"}</span>
              <div>
                <p>{clue.text || "カギ文は未入力です"}</p>
                {clue.answer ? (
                  <span className="clue-answer">答え：{clue.answer}</span>
                ) : null}
              </div>
            </li>
          ))}
        </ol>
      ) : (
        <p className="empty-clues">JSONを読み込むとカギが表示されます。</p>
      )}
    </section>
  );
}

function StorageManager({
  currentProjectId,
  projects,
  summary,
  busy,
  onClose,
  onOpen,
  onDelete,
  onDeleteAll,
  onPersist,
}: {
  currentProjectId: string;
  projects: StoredProject[];
  summary: StorageSummary;
  busy: boolean;
  onClose: () => void;
  onOpen: (project: StoredProject) => void;
  onDelete: (project: StoredProject) => void;
  onDeleteAll: () => void;
  onPersist: () => void;
}) {
  return (
    <div className="storage-backdrop" role="presentation" onMouseDown={onClose}>
      <section
        className="storage-dialog"
        role="dialog"
        aria-modal="true"
        aria-labelledby="storage-title"
        onMouseDown={(event) => event.stopPropagation()}
      >
        <div className="storage-header">
          <div>
            <p className="section-kicker">LOCAL PROJECTS</p>
            <h2 id="storage-title">保存データ管理</h2>
          </div>
          <button
            className="close-button"
            onClick={onClose}
            aria-label="保存データ管理を閉じる"
          >
            ×
          </button>
        </div>

        <div className="storage-overview">
          <div>
            <span>保存プロジェクト</span>
            <strong>{projects.length}件</strong>
          </div>
          <div>
            <span>ブラウザ全体の使用量</span>
            <strong>
              {summary.usage === null ? "確認できません" : formatBytes(summary.usage)}
            </strong>
          </div>
          <div>
            <span>保存状態</span>
            <strong>{summary.persistent ? "永続保存" : "通常保存"}</strong>
          </div>
        </div>

        {!summary.persistent ? (
          <div className="persistence-notice">
            <p>
              永続保存を有効にすると、端末の空き容量が少ない場合でもブラウザが
              データを自動整理しにくくなります。
            </p>
            <button
              className="button button-subtle"
              disabled={busy}
              onClick={onPersist}
            >
              永続保存を有効にする
            </button>
          </div>
        ) : null}

        <div className="stored-project-list">
          {projects.length ? (
            projects.map((stored) => (
              <article className="stored-project" key={stored.id}>
                <div className="stored-project-main">
                  <div>
                    <strong>{stored.fileName}</strong>
                    {stored.id === currentProjectId ? (
                      <span className="current-badge">現在開いています</span>
                    ) : null}
                  </div>
                  <span>
                    {formatDate(stored.savedAt)}・
                    {formatBytes(
                      new Blob([JSON.stringify(stored.document)]).size,
                    )}
                  </span>
                </div>
                <div className="stored-project-actions">
                  <button
                    className="mini-button"
                    disabled={busy}
                    onClick={() => onOpen(stored)}
                  >
                    開く
                  </button>
                  <button
                    className="mini-button mini-button-danger"
                    disabled={busy}
                    onClick={() => onDelete(stored)}
                  >
                    削除
                  </button>
                </div>
              </article>
            ))
          ) : (
            <p className="empty-storage">保存されているプロジェクトはありません。</p>
          )}
        </div>

        <div className="storage-footer">
          <span>
            上限目安：
            {summary.quota === null ? "ブラウザが自動管理" : formatBytes(summary.quota)}
          </span>
          <button
            className="delete-all-button"
            disabled={busy || projects.length === 0}
            onClick={onDeleteAll}
          >
            保存データをすべて削除
          </button>
        </div>
      </section>
    </div>
  );
}

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  if (bytes < 1024 * 1024 * 1024) {
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  }
  return `${(bytes / (1024 * 1024 * 1024)).toFixed(1)} GB`;
}

function formatDate(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "保存日時不明";
  return new Intl.DateTimeFormat("ja-JP", {
    month: "numeric",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(date);
}
