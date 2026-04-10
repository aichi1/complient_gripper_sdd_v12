# GripperForge — 入出力仕様

各フェーズの入出力を明確化し、フェーズ間の I/F を固定する。

---

## Phase 1: 技術検証 PoC

### 入力
- **コマンドライン引数 / 設定ファイル**
  - 設計領域サイズ（要素数 `nelx × nely`、既定 60×30）
  - 体積分率制約 `volfrac`（例：0.4）
  - ペナルティ指数 `penal`（既定 3.0）
  - フィルタ半径 `rmin`（既定 1.5）
  - 目的関数種別：`compliance` または `compliant_mechanism`
- **ワーク条件**
  - テストケースごとにハードコード（円筒／直方体／L 字型の荷重条件プリセット）

### 出力
- **標準出力**：イテレーションごとの目的関数値・変化量
- **ファイル**
  - `outputs/phase-01/results/{case_name}_density.png` — 密度分布可視化
  - `outputs/phase-01/results/{case_name}_history.csv` — 収束履歴
  - `outputs/phase-01/results/{case_name}_topology.npy` — 密度フィールドのバイナリ
- **3Dプリント検証レポート**：`outputs/phase-01/reports/physical-validation.md`（テスト結果、写真、評価）

### エラー時の振る舞い
- 不正引数 → エラーメッセージ + `--help` ヒント表示 → 終了コード 2
- 収束しない（最大反復に到達） → 警告メッセージ + 最終状態を保存 → 終了コード 0（ただしレポートに記録）
- 数値発散（NaN / Inf） → エラーメッセージ + スナップショット保存 → 終了コード 3

---

## Phase 2: コア最適化エンジン

### 入力
- **ワーク断面**
  - 閉多角形（頂点座標リスト、mm 単位） — JSON または簡易 DXF
  - 境界条件アノテーション（荷重点、固定点、把持方向）
- **最適化パラメータ**
  - メッシュ解像度（既定：100×100）
  - 材料物性：ヤング率 `E`、ポアソン比 `nu`
  - フィルタ種別：`sensitivity` / `density`
  - Heaviside projection 有効化フラグ + β スケジュール
- **押し出しパラメータ**
  - 厚み（mm）

### 出力
- **2D 密度分布**：PNG + NPY
- **3D メッシュ**：`outputs/phase-02/results/{case_name}.stl`（ASCII または binary STL）
- **収束ログ**：JSON
- **Python API**：`gripperforge_engine.optimize(config) -> OptimizationResult`

### エラー時の振る舞い
- 入力ワーク境界の不整合（自己交差、開多角形） → `InvalidGeometryError` を raise → CLI は終了コード 2
- ソルバー数値不安定 → `SolverDivergenceError` → 最終スナップショットを残して終了コード 3
- STL 出力時に退化三角形検出 → 警告ログ + 退化三角形を除外して続行

---

## Phase 3: 最小限 Web UI

### 入力（API リクエスト）
- `POST /api/jobs` — 最適化ジョブ開始
  - Body（JSON）：`{ workpiece: {...}, params: {...} }`
  - レスポンス：`{ job_id: "...", status: "queued" }`
- `GET /api/jobs/{job_id}` — ジョブ状態取得
  - レスポンス：`{ status: "running|done|error", progress: 0-1, preview_url?: "...", stl_url?: "..." }`
- `GET /api/jobs/{job_id}/stl` — STL ダウンロード
- `GET /api/history` — 履歴一覧

### フロントエンド UI
- ワーク断面描画ツール（Canvas）、DXF アップロード
- パラメータ設定パネル
- 最適化結果プレビュー（PNG）
- STL ダウンロードボタン
- 履歴一覧

### エラー時の振る舞い
- API：標準的な HTTP ステータス + `{"error": {...}}` JSON
- ジョブ失敗 → ステータス `error`、`error_message` を含める
- フロント：トーストでエラー表示、リトライ可能ならリトライボタン

---

## Phase 4: 実ワーク検証

### 入力
- 実ワークの CAD データ（STEP / STL） — 3〜5 種
- 把持条件仕様書（把持点、想定荷重、姿勢）
- 汎用ジョーでの既存把持結果（比較基準）

### 出力
- 最適化済みフィンガー STL
- 3Dプリント成果物（物理）— 写真で記録
- 把持テスト記録：`outputs/phase-04/cases/{case_id}/`
  - `setup.md` — 実験条件
  - `result.md` — 定量評価（成功率、把持力、位置決め精度）
  - `photos/` — 写真・動画リンク
  - `comparison.md` — 汎用ジョー vs GripperForge フィンガーの比較
- 総括レポート：`outputs/phase-04/summary-report.md`

### エラー時の振る舞い
- 把持失敗 → 原因分類（形状不適合、材料不足、境界条件ミス）して記録
- 5 ケース中 2 以上で失敗 → 要件達成失敗として `summary-report.md` に明記し、Validator が NEEDS_REVISION を出す

---

## Phase 5: 公開と初期顧客獲得

### 入力
- Phase 4 の事例データ・写真・動画素材
- プロジェクト全体の学びとリスク対応履歴

### 出力
- `outputs/phase-05/articles/zenn-draft.md` — Zenn 記事ドラフト
- `outputs/phase-05/demo_video/script.md` + カット割り表
- `outputs/phase-05/oss/README.md` — OSS 公開時の README 案
- `outputs/phase-05/outreach/target-list.md` — 初期アプローチ企業リスト（匿名化可）
- `outputs/phase-05/outreach/message-templates.md` — コールドメッセージ雛形

### エラー時の振る舞い
- 公開前に機密情報（顧客名・内部データ）混入チェックを実施し、見つかれば差し戻し
- OSS ライセンスの選定未了 → Validator がブロック
