# CrossMaker Web

CrossMaker のブラウザ版。デスクトップ版（`app/`）と同じ `data.json`（プロジェクト形式バージョン2）を読み書きする。

公開版: https://dfnasutarou.github.io/CrossWords/ （`main` の `web/` が更新されると GitHub Actions で自動公開）
サーバーは使わず、ブラウザだけで動く静的サイト（Vite + React + TypeScript）。

## 開発

```bash
cd web
npm install
npm run dev      # http://localhost:5173
npm test         # モデル層の自動テスト（vitest）
npm run build    # dist/ に静的ファイルを出力
```

`dist/` は相対パスでビルドされるため、GitHub Pages や Cloudflare Pages などにそのまま置ける。

## 対応ブラウザ

- Chrome / Edge：プロジェクトフォルダ（`data.json` と `picture/`）を開いて、同じ場所へ上書き保存できる（File System Access API）。
- Firefox / Safari：ファイルを選んで読み込み、保存はダウンロードになる。

編集中の内容はブラウザ内（IndexedDB）に自動保存され、再読み込みしても復元される。

## 現在の機能（段階1）

- 新規作成（4×4～9×9）、フォルダ／`data.json` を開く、上書き保存、フォルダへ保存、ダウンロード
- 盤面の編集
  - 文字入力モード：マスを選んで打つと入力方向（→／↓）へ1文字ずつ進む。日本語入力の確定文字列もまとめて流し込める。
    `＊` で黒マス、`・` で文字なし。矢印キーで移動、Tab または選択中のマスの再クリックで方向切り替え。
  - 黒マスモード／二重マスモード：クリックで切り替え
  - 盤サイズ変更、カギ番号の振り方（上優先／左優先）
- 盤面の一括入力：テキストで盤全体を入力して反映。今の盤面をテキストとして表示する（逆変換）。
  二重マスは一括入力とは別に設定し、一括入力で反映しても白マスのままなら残る。
- 指示文・カギ文・カギ見出しの編集、答えの自動表示
- 元に戻す／やり直し（Ctrl+Z / Ctrl+Y）、Ctrl+S で保存
- 盤面とカギを全部消す

Web版でまだ編集できない項目（文字の黒塗り、文中画像、書式設定、表示ON/OFF など）は、
読み込んだデータをそのまま保持して保存するので、デスクトップ版で付けた設定は失われない。

## 今後（段階2以降）

- 盤面の黒塗り、文字の黒塗り、表示ON/OFF、フォーマット設定、PNG出力
- 文中画像、盤面列挙、PDF出力
- 盤の転置・タテヨコカギ入れ替えの操作（現在は表示のみ対応）

## 構成

- `src/model/project.ts`：データ形式の読み書き・編集操作（未対応項目は保持）
- `src/model/numbering.ts`：カギ番号と答えの計算（デスクトップ版 `CellBoard.reset` と同じ規則）
- `src/model/quick-input.ts`：一括入力・直接入力の文字解釈
- `src/model/default-project.json`：新規作成時の既定値（デスクトップ版が保存する初期データ）
- `src/storage/`：ローカルファイルの読み書き、自動保存
- `src/components/`：盤面・一括入力・カギ欄の画面
