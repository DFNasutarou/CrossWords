// 編集中の内容をブラウザ内（IndexedDB）に自動保存し、再読み込み時に復元する。
// 開いていたファイルの場所（ハンドル）も保存し、再訪時に同じファイルへ上書き保存できるようにする。
import type { ProjectDocument } from "../model/project";
import type { FileTarget } from "./files";

const DATABASE_NAME = "crossmaker-web-v2";
const STORE = "session";
const SESSION_KEY = "current";

export type AutosaveSession = {
  document: ProjectDocument;
  name: string;
  target: FileTarget | null;
  dirty: boolean;
  savedAt: string;
};

function openDatabase(): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open(DATABASE_NAME, 1);
    request.onupgradeneeded = () => request.result.createObjectStore(STORE);
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
  });
}

async function run<T>(mode: IDBTransactionMode, action: (store: IDBObjectStore) => IDBRequest): Promise<T> {
  const database = await openDatabase();
  try {
    return await new Promise<T>((resolve, reject) => {
      const transaction = database.transaction(STORE, mode);
      const request = action(transaction.objectStore(STORE));
      transaction.oncomplete = () => resolve(request.result as T);
      transaction.onerror = () => reject(transaction.error);
    });
  } finally {
    database.close();
  }
}

export async function loadSession(): Promise<AutosaveSession | null> {
  try {
    return (await run<AutosaveSession | undefined>("readonly", (store) => store.get(SESSION_KEY))) ?? null;
  } catch {
    return null;
  }
}

export async function saveSession(session: AutosaveSession): Promise<void> {
  try {
    await run("readwrite", (store) => store.put(session, SESSION_KEY));
  } catch {
    // ハンドルを保存できない環境ではハンドル抜きで保存する
    try {
      await run("readwrite", (store) => store.put({ ...session, target: null }, SESSION_KEY));
    } catch {
      // プライベートモードなどで保存できない場合は自動保存をあきらめる
    }
  }
}
