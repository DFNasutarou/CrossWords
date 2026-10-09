// 元に戻す・やり直しの履歴
import type { ProjectDocument } from "./project";

const LIMIT = 200;
const COALESCE_MS = 1000;

export type History = {
  past: ProjectDocument[];
  present: ProjectDocument;
  future: ProjectDocument[];
  lastKey: string | null;
  lastAt: number;
};

export type HistoryAction =
  | { type: "reset"; document: ProjectDocument }
  | { type: "change"; document: ProjectDocument; coalesceKey?: string }
  | { type: "undo" }
  | { type: "redo" };

export function initHistory(document: ProjectDocument): History {
  return { past: [], present: document, future: [], lastKey: null, lastAt: 0 };
}

export function historyReducer(state: History, action: HistoryAction): History {
  switch (action.type) {
    case "reset":
      return initHistory(action.document);
    case "change": {
      if (action.document === state.present) return state;
      const now = Date.now();
      // 同じ欄への連続した文字入力は1回分の履歴にまとめる
      const coalesce =
        action.coalesceKey !== undefined &&
        action.coalesceKey === state.lastKey &&
        now - state.lastAt < COALESCE_MS;
      return {
        past: coalesce ? state.past : [...state.past, state.present].slice(-LIMIT),
        present: action.document,
        future: [],
        lastKey: action.coalesceKey ?? null,
        lastAt: now,
      };
    }
    case "undo": {
      const previous = state.past[state.past.length - 1];
      if (!previous) return state;
      return {
        past: state.past.slice(0, -1),
        present: previous,
        future: [state.present, ...state.future],
        lastKey: null,
        lastAt: 0,
      };
    }
    case "redo": {
      const [next, ...rest] = state.future;
      if (!next) return state;
      return {
        past: [...state.past, state.present],
        present: next,
        future: rest,
        lastKey: null,
        lastAt: 0,
      };
    }
  }
}
