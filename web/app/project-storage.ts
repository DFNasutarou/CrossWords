import type { ProjectDocument } from "./project-model";

export type StoredProject = {
  id: string;
  fileName: string;
  document: ProjectDocument;
  savedAt: string;
};

export type StorageSummary = {
  usage: number | null;
  quota: number | null;
  persistent: boolean;
};

const DATABASE_NAME = "crossmaker-web";
const DATABASE_VERSION = 2;
const PROJECT_STORE = "projects";
const SETTINGS_STORE = "settings";
const LEGACY_STORE = "workspace";
const LAST_PROJECT_KEY = "last-project";
const LAST_PROJECT_ID_KEY = "last-project-id";

export async function loadLastProject(): Promise<StoredProject | null> {
  const database = await openDatabase();
  const lastProjectId = await getValue<string>(
    database,
    SETTINGS_STORE,
    LAST_PROJECT_ID_KEY,
  );
  if (lastProjectId) {
    const project = await getValue<StoredProject>(
      database,
      PROJECT_STORE,
      lastProjectId,
    );
    if (project) {
      database.close();
      return project;
    }
  }

  const legacy = database.objectStoreNames.contains(LEGACY_STORE)
    ? await getValue<Omit<StoredProject, "id">>(
        database,
        LEGACY_STORE,
        LAST_PROJECT_KEY,
      )
    : null;
  if (!legacy) {
    database.close();
    return null;
  }

  const migrated: StoredProject = {
    ...legacy,
    id: createProjectId(),
  };
  await putProject(database, migrated);
  await deleteValue(database, LEGACY_STORE, LAST_PROJECT_KEY);
  database.close();
  return migrated;
}

export async function saveProject(project: StoredProject): Promise<void> {
  const database = await openDatabase();
  await putProject(database, project);
  database.close();
}

export async function listProjects(): Promise<StoredProject[]> {
  const database = await openDatabase();
  const projects = await getAllValues<StoredProject>(database, PROJECT_STORE);
  database.close();
  return projects.sort((left, right) =>
    right.savedAt.localeCompare(left.savedAt),
  );
}

export async function deleteProject(id: string): Promise<void> {
  const database = await openDatabase();
  const lastProjectId = await getValue<string>(
    database,
    SETTINGS_STORE,
    LAST_PROJECT_ID_KEY,
  );
  await deleteValue(database, PROJECT_STORE, id);
  if (lastProjectId === id) {
    await deleteValue(database, SETTINGS_STORE, LAST_PROJECT_ID_KEY);
  }
  database.close();
}

export async function clearProjects(): Promise<void> {
  const database = await openDatabase();
  await clearStore(database, PROJECT_STORE);
  await deleteValue(database, SETTINGS_STORE, LAST_PROJECT_ID_KEY);
  if (database.objectStoreNames.contains(LEGACY_STORE)) {
    await clearStore(database, LEGACY_STORE);
  }
  database.close();
}

export async function getStorageSummary(): Promise<StorageSummary> {
  if (!navigator.storage) {
    return { usage: null, quota: null, persistent: false };
  }
  const [estimate, persistent] = await Promise.all([
    navigator.storage.estimate(),
    navigator.storage.persisted?.() ?? Promise.resolve(false),
  ]);
  return {
    usage: estimate.usage ?? null,
    quota: estimate.quota ?? null,
    persistent,
  };
}

export async function requestPersistentStorage(): Promise<boolean> {
  if (!navigator.storage?.persist) return false;
  return navigator.storage.persist();
}

export function createProjectId(): string {
  if (typeof crypto !== "undefined" && "randomUUID" in crypto) {
    return crypto.randomUUID();
  }
  return `project-${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

async function putProject(
  database: IDBDatabase,
  project: StoredProject,
): Promise<void> {
  return new Promise((resolve, reject) => {
    const transaction = database.transaction(
      [PROJECT_STORE, SETTINGS_STORE],
      "readwrite",
    );
    transaction.objectStore(PROJECT_STORE).put(project, project.id);
    transaction
      .objectStore(SETTINGS_STORE)
      .put(project.id, LAST_PROJECT_ID_KEY);
    transaction.oncomplete = () => resolve();
    transaction.onerror = () => reject(transaction.error);
  });
}

function getValue<T>(
  database: IDBDatabase,
  storeName: string,
  key: IDBValidKey,
): Promise<T | null> {
  return new Promise((resolve, reject) => {
    const transaction = database.transaction(storeName, "readonly");
    const request = transaction.objectStore(storeName).get(key);
    request.onsuccess = () => resolve((request.result as T) ?? null);
    request.onerror = () => reject(request.error);
  });
}

function getAllValues<T>(
  database: IDBDatabase,
  storeName: string,
): Promise<T[]> {
  return new Promise((resolve, reject) => {
    const transaction = database.transaction(storeName, "readonly");
    const request = transaction.objectStore(storeName).getAll();
    request.onsuccess = () => resolve((request.result as T[]) ?? []);
    request.onerror = () => reject(request.error);
  });
}

function deleteValue(
  database: IDBDatabase,
  storeName: string,
  key: IDBValidKey,
): Promise<void> {
  return new Promise((resolve, reject) => {
    const transaction = database.transaction(storeName, "readwrite");
    transaction.objectStore(storeName).delete(key);
    transaction.oncomplete = () => resolve();
    transaction.onerror = () => reject(transaction.error);
  });
}

function clearStore(
  database: IDBDatabase,
  storeName: string,
): Promise<void> {
  return new Promise((resolve, reject) => {
    const transaction = database.transaction(storeName, "readwrite");
    transaction.objectStore(storeName).clear();
    transaction.oncomplete = () => resolve();
    transaction.onerror = () => reject(transaction.error);
  });
}

function openDatabase(): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open(DATABASE_NAME, DATABASE_VERSION);
    request.onupgradeneeded = () => {
      if (!request.result.objectStoreNames.contains(PROJECT_STORE)) {
        request.result.createObjectStore(PROJECT_STORE);
      }
      if (!request.result.objectStoreNames.contains(SETTINGS_STORE)) {
        request.result.createObjectStore(SETTINGS_STORE);
      }
    };
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
  });
}
