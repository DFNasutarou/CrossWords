import {
  countBlackouts,
  countInlineImages,
  getPlainText,
  type KeyDirection,
  type ProjectData,
} from "../model/project";

type Props = {
  data: ProjectData;
  onKeyText: (direction: KeyDirection, index: number, text: string) => void;
  onHeading: (which: "row_title" | "col_title", text: string) => void;
};

function Extras({ content }: { content: unknown }) {
  const blackouts = countBlackouts(content);
  const images = countInlineImages(content);
  if (!blackouts && !images) return null;
  return (
    <span className="extras" title="Web版ではまだ編集できません。保存しても残ります。">
      {blackouts > 0 && <span>黒塗り{blackouts}</span>}
      {images > 0 && <span>画像{images}</span>}
    </span>
  );
}

function ClueList({
  data,
  direction,
  heading,
  onKeyText,
  onHeading,
}: Props & { direction: KeyDirection; heading: "row_title" | "col_title" }) {
  const keys = data.key[direction].filter((key) => getPlainText(key.key_name) !== "");
  return (
    <div className="clue-list">
      <input
        className="clue-heading"
        value={getPlainText(data.key[heading])}
        onChange={(event) => onHeading(heading, event.target.value)}
        aria-label="カギの見出し"
      />
      {keys.length === 0 && <p className="hint">盤面にカギがありません。</p>}
      {keys.map((key, index) => {
        const text = getPlainText(key.text);
        return (
          <div className="clue" key={index}>
            <span className="clue-number">{getPlainText(key.key_name)}</span>
            <div className="clue-body">
              <textarea
                value={text}
                rows={Math.max(1, text.split("\n").length)}
                placeholder="カギ文"
                onChange={(event) => onKeyText(direction, index, event.target.value)}
                aria-label={`${getPlainText(data.key[heading])} ${getPlainText(key.key_name)}`}
              />
              <Extras content={key.text} />
            </div>
            <span className="clue-answer" title="盤面から自動で入ります">
              {key.answer.replace(/ /g, "□")}
            </span>
          </div>
        );
      })}
    </div>
  );
}

export function CluePanel(props: Props) {
  const { data } = props;
  // デスクトップ版の「タテヨコカギ入れ替え」(key_sort) と「盤の転置」(key_trans) の表示順に合わせる
  type Section = { direction: KeyDirection; heading: "row_title" | "col_title" };
  let first: Section = { direction: "row_key", heading: "row_title" };
  let second: Section = { direction: "col_key", heading: "col_title" };
  if (data.key.key_sort) [first, second] = [second, first];
  const headings = data.key.key_trans
    ? [second.heading, first.heading]
    : [first.heading, second.heading];
  return (
    <section className="panel clues">
      <ClueList {...props} direction={first.direction} heading={headings[0]} />
      <ClueList {...props} direction={second.direction} heading={headings[1]} />
    </section>
  );
}
