import { useMemo, useState } from "react";
import type { ProjectData } from "../model/project";
import { BLACK_MARKS, EMPTY_MARKS, formatQuickInput, parseQuickInput, type QuickCell } from "../model/quick-input";

type Props = {
  data: ProjectData;
  onApply: (size: number, cells: QuickCell[][]) => void;
};

export function QuickInputPanel({ data, onApply }: Props) {
  // 編集していない間は盤面の内容に追随する
  const [draft, setDraft] = useState<string | null>(null);
  const boardText = formatQuickInput(data);
  const text = draft ?? boardText;
  const result = useMemo(() => parseQuickInput(text), [text]);
  const unchanged = text === boardText;

  const apply = () => {
    if (!result.ok) return;
    if (
      result.size !== data.cell.board_size &&
      !window.confirm(`盤のサイズが ${data.cell.board_size}×${data.cell.board_size} から ${result.size}×${result.size} に変わります。反映しますか？`)
    ) {
      return;
    }
    onApply(result.size, result.cells);
    setDraft(null);
  };

  return (
    <section className="panel quick-input">
      <h2>盤面の一括入力</h2>
      <p className="hint">
        1行が盤の1行です。黒マスは <kbd>{BLACK_MARKS.slice(0, 3).join(" ")}</kbd>、
        文字なしの白マスは <kbd>{EMPTY_MARKS.slice(0, 2).join(" ")}</kbd>。空白は無視します。
        二重マスは「二重マス」モードで別に設定します（ここで反映しても消えません）。
      </p>
      <textarea
        className="quick-textarea"
        value={text}
        onChange={(event) => setDraft(event.target.value)}
        rows={Math.max(5, text.split("\n").length + 1)}
        spellCheck={false}
        aria-label="盤面の一括入力"
      />
      {result.ok ? (
        <p className="status-ok">{result.size}×{result.size} の盤として反映できます。</p>
      ) : (
        <ul className="errors">
          {result.errors.map((error, index) => (
            <li key={index}>{error.message}</li>
          ))}
        </ul>
      )}
      <div className="row-buttons">
        <button type="button" className="primary" onClick={apply} disabled={!result.ok || unchanged}>
          盤面に反映
        </button>
        <button type="button" onClick={() => setDraft(null)} disabled={unchanged}>
          今の盤面を読み込む
        </button>
      </div>
    </section>
  );
}
