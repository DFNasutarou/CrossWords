// ローカルファイルの読み書き。
// Chrome / Edge では File System Access API でプロジェクトフォルダを開き、同じ場所へ上書き保存する。
// 対応していないブラウザでは、ファイル選択で読み込み・ダウンロードで保存する。
import { parseProjectJson, serializeProject, type ProjectDocument } from "../model/project";

export const DATA_FILE_NAME = "data.json";
const PICTURE_FOLDER_NAME = "picture";

// TypeScript の DOM 型に未収録の API をここで宣言する
type PickerWindow = Window & {
  showDirectoryPicker?: (options?: { mode?: "read" | "readwrite"; id?: string }) => Promise<FileSystemDirectoryHandle>;
  showOpenFilePicker?: (options?: unknown) => Promise<FileSystemFileHandle[]>;
};
type PermissionHandle = FileSystemHandle & {
  queryPermission?: (options: { mode: "readwrite" }) => Promise<PermissionState>;
  requestPermission?: (options: { mode: "readwrite" }) => Promise<PermissionState>;
};

export type FileTarget =
  | { kind: "folder"; folder: FileSystemDirectoryHandle; file: FileSystemFileHandle }
  | { kind: "file"; file: FileSystemFileHandle };

export type OpenedProject = {
  document: ProjectDocument;
  target: FileTarget | null;
  name: string;
};

const pickerWindow = window as PickerWindow;

export function supportsFileSystemAccess(): boolean {
  return typeof pickerWindow.showDirectoryPicker === "function";
}

export function isAbortError(error: unknown): boolean {
  return error instanceof DOMException && error.name === "AbortError";
}

export function targetName(target: FileTarget): string {
  return target.kind === "folder" ? `${target.folder.name}/${DATA_FILE_NAME}` : target.file.name;
}

async function readTarget(file: FileSystemFileHandle): Promise<ProjectDocument> {
  const text = await (await file.getFile()).text();
  return parseProjectJson(text);
}

// プロジェクトフォルダ（data.json と picture/ を含む）を開く
export async function openProjectFolder(): Promise<OpenedProject> {
  const folder = await pickerWindow.showDirectoryPicker!({ mode: "readwrite", id: "crossmaker" });
  let file: FileSystemFileHandle;
  try {
    file = await folder.getFileHandle(DATA_FILE_NAME);
  } catch {
    throw new Error(`選んだフォルダに ${DATA_FILE_NAME} がありません。`);
  }
  const target: FileTarget = { kind: "folder", folder, file };
  return { document: await readTarget(file), target, name: targetName(target) };
}

// data.json を単体で開く
export async function openProjectFile(): Promise<OpenedProject> {
  const [file] = await pickerWindow.showOpenFilePicker!({
    id: "crossmaker",
    types: [{ description: "CrossMaker プロジェクト", accept: { "application/json": [".json"] } }],
  });
  const target: FileTarget = { kind: "file", file };
  return { document: await readTarget(file), target, name: targetName(target) };
}

// File System Access API が使えないブラウザ向け：<input type="file"> で選んだファイルを読む
export async function readUploadedFile(file: File): Promise<OpenedProject> {
  return { document: parseProjectJson(await file.text()), target: null, name: file.name };
}

export async function ensureWritePermission(target: FileTarget): Promise<boolean> {
  const handle = target.file as PermissionHandle;
  if (!handle.queryPermission || !handle.requestPermission) return true;
  if ((await handle.queryPermission({ mode: "readwrite" })) === "granted") return true;
  return (await handle.requestPermission({ mode: "readwrite" })) === "granted";
}

export async function writeProject(target: FileTarget, document: ProjectDocument): Promise<void> {
  if (!(await ensureWritePermission(target))) {
    throw new Error("ファイルへの書き込みが許可されませんでした。");
  }
  const writable = await target.file.createWritable();
  await writable.write(serializeProject(document));
  await writable.close();
}

// 新しいプロジェクトフォルダとして保存する（デスクトップ版と同じく picture/ も作る）
export async function saveAsFolder(document: ProjectDocument): Promise<FileTarget | null> {
  const folder = await pickerWindow.showDirectoryPicker!({ mode: "readwrite", id: "crossmaker" });
  let exists = true;
  try {
    await folder.getFileHandle(DATA_FILE_NAME);
  } catch {
    exists = false;
  }
  if (exists && !window.confirm(`「${folder.name}」には既に ${DATA_FILE_NAME} があります。上書きしますか？`)) {
    return null;
  }
  const file = await folder.getFileHandle(DATA_FILE_NAME, { create: true });
  await folder.getDirectoryHandle(PICTURE_FOLDER_NAME, { create: true });
  const target: FileTarget = { kind: "folder", folder, file };
  await writeProject(target, document);
  return target;
}

export function downloadProject(document: ProjectDocument, fileName = DATA_FILE_NAME): void {
  const blob = new Blob([serializeProject(document)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const anchor = window.document.createElement("a");
  anchor.href = url;
  anchor.download = fileName;
  anchor.click();
  URL.revokeObjectURL(url);
}
