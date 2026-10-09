import { useEffect, useMemo, useRef, useState, type KeyboardEvent } from "react";
import {
  CELL_BLACK,
  CELL_DOUBLE,
  CELL_WHITE,
  getBoardNumbers,
  getDisplayCell,
  toDataPosition,
  type CellUpdate,
  type ProjectData,
} from "../model/project";

export type BoardMode = "input" | "black" | "double";
export type Direction = "right" | "down";
export type Position = { row: number; col: number };

type Props = {
  data: ProjectData;
  mode: BoardMode;
  direction: Direction;
  onDirectionChange: (direction: Direction) => void;
  onUpdateCells: (updates: { row: number; col: number; update: CellUpdate }[]) => void;
  onType: (start: Position, text: string) => Position;
};

export function BoardEditor({ data, mode, direction, onDirectionChange, onUpdateCells, onType }: Props) {
  const size = data.cell.board_size;
  const [selected, setSelected] = useState<Position>({ row: 0, col: 0 });
  const inputRef = useRef<HTMLInputElement>(null);
  const composing = useRef(false);

  // 盤サイズが小さくなったら選択位置を盤内に戻す
  useEffect(() => {
    setSelected((current) => ({
      row: Math.min(current.row, size - 1),
      col: Math.min(current.col, size - 1),
    }));
  }, [size]);

  // 画面上の位置ごとのカギ番号（転置表示を考慮）
  const numbers = useMemo(() => {
    const dataNumbers = getBoardNumbers(data);
    return Array.from({ length: size }, (_, r) =>
      Array.from({ length: size }, (_, c) => {
        const [dr, dc] = toDataPosition(data, r, c);
        return dataNumbers[dr][dc];
      }),
    );
  }, [data, size]);

  const isBlack = (row: number, col: number) => getDisplayCell(data, row, col).state === CELL_BLACK;

  // 選択マスを含む、入力方向の一続きの白マス（強調表示用）
  const word = useMemo(() => {
    const cells = new Set<string>();
    if (mode !== "input" || isBlack(selected.row, selected.col)) return cells;
    const [dr, dc] = direction === "down" ? [1, 0] : [0, 1];
    let { row, col } = selected;
    while (row - dr >= 0 && col - dc >= 0 && !isBlack(row - dr, col - dc)) {
      row -= dr;
      col -= dc;
    }
    while (row < size && col < size && !isBlack(row, col)) {
      cells.add(`${row},${col}`);
      row += dr;
      col += dc;
    }
    return cells;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [data, selected, direction, mode, size]);

  const focusInput = () => inputRef.current?.focus({ preventScroll: true });

  const handleCellClick = (row: number, col: number) => {
    const cell = getDisplayCell(data, row, col);
    if (mode === "black") {
      onUpdateCells([{ row, col, update: { state: cell.state === CELL_BLACK ? CELL_WHITE : CELL_BLACK } }]);
      return;
    }
    if (mode === "double") {
      if (cell.state === CELL_BLACK) return;
      onUpdateCells([{ row, col, update: { state: cell.state === CELL_DOUBLE ? CELL_WHITE : CELL_DOUBLE } }]);
      return;
    }
    // 選択中のマスをもう一度クリックすると入力方向を切り替える
    // （盤面の外から戻ってきた最初のクリックでは切り替えない）
    const focused = window.document.activeElement === inputRef.current;
    if (focused && row === selected.row && col === selected.col) {
      onDirectionChange(direction === "right" ? "down" : "right");
    }
    setSelected({ row, col });
    focusInput();
  };

  const commitText = (text: string) => {
    if (!text) return;
    const cursor = onType(selected, text);
    setSelected(cursor);
  };

  const clearCell = (position: Position) => {
    const cell = getDisplayCell(data, position.row, position.col);
    onUpdateCells([
      {
        ...position,
        update: { charactor: "", state: cell.state === CELL_BLACK ? CELL_WHITE : cell.state },
      },
    ]);
  };

  const move = (dRow: number, dCol: number) => {
    setSelected((current) => ({
      row: Math.max(0, Math.min(size - 1, current.row + dRow)),
      col: Math.max(0, Math.min(size - 1, current.col + dCol)),
    }));
  };

  const handleKeyDown = (event: KeyboardEvent<HTMLInputElement>) => {
    if (event.nativeEvent.isComposing || composing.current || event.keyCode === 229) return;
    if (event.ctrlKey || event.metaKey || event.altKey) return;
    const back = direction === "down" ? { row: -1, col: 0 } : { row: 0, col: -1 };
    switch (event.key) {
      case "ArrowUp":
        move(-1, 0);
        break;
      case "ArrowDown":
        move(1, 0);
        break;
      case "ArrowLeft":
        move(0, -1);
        break;
      case "ArrowRight":
        move(0, 1);
        break;
      case "Tab":
        onDirectionChange(direction === "right" ? "down" : "right");
        break;
      case "Delete":
        clearCell(selected);
        break;
      case "Backspace": {
        const cell = getDisplayCell(data, selected.row, selected.col);
        if (cell.charactor || cell.state === CELL_BLACK) {
          clearCell(selected);
        } else {
          const previous = { row: selected.row + back.row, col: selected.col + back.col };
          if (previous.row < 0 || previous.col < 0) break;
          clearCell(previous);
          setSelected(previous);
        }
        break;
      }
      default:
        return;
    }
    event.preventDefault();
  };

  const cellSize = `min(${Math.floor(560 / size)}px, calc((100vw - 84px) / ${size}))`;

  return (
    <div className="board-wrap">
      <div
        className={`board mode-${mode}`}
        style={{ gridTemplateColumns: `repeat(${size}, ${cellSize})`, gridAutoRows: cellSize }}
        role="grid"
        aria-label="盤面"
      >
        {Array.from({ length: size }, (_, row) =>
          Array.from({ length: size }, (_, col) => {
            const cell = getDisplayCell(data, row, col);
            const black = cell.state === CELL_BLACK;
            const isSelected = mode === "input" && row === selected.row && col === selected.col;
            const classes = [
              "cell",
              black ? "black" : "white",
              cell.state === CELL_DOUBLE ? "double" : "",
              word.has(`${row},${col}`) ? "in-word" : "",
              isSelected ? "selected" : "",
            ].join(" ");
            return (
              <div
                key={`${row}-${col}`}
                className={classes}
                role="gridcell"
                onMouseDown={(event) => {
                  event.preventDefault();
                  handleCellClick(row, col);
                }}
              >
                {!black && numbers[row][col] !== null && <span className="number">{numbers[row][col]}</span>}
                {!black && <span className="char">{cell.charactor}</span>}
              </div>
            );
          }),
        )}
        {mode === "input" && (
          <input
            ref={inputRef}
            className="board-input"
            style={{
              top: `${(selected.row / size) * 100}%`,
              left: `${(selected.col / size) * 100}%`,
              width: `${100 / size}%`,
              height: `${100 / size}%`,
            }}
            aria-label="選択中のマスへの入力"
            autoComplete="off"
            autoCapitalize="off"
            spellCheck={false}
            onKeyDown={handleKeyDown}
            onCompositionStart={() => {
              composing.current = true;
            }}
            onCompositionEnd={(event) => {
              composing.current = false;
              const text = event.currentTarget.value;
              event.currentTarget.value = "";
              commitText(text);
            }}
            onChange={(event) => {
              if (composing.current || (event.nativeEvent as InputEvent).isComposing) return;
              const text = event.currentTarget.value;
              event.currentTarget.value = "";
              commitText(text);
            }}
          />
        )}
      </div>
    </div>
  );
}
