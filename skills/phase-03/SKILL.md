# Phase 3: 最小限 Web UI（React + FastAPI + 非同期ジョブ実行）

> カテゴリ：`small_implementation`
> 元 Roadmap：Phase 2 最小限の WebUI
> 前提：Phase 2 完了（`gripperforge_engine` が Python API として安定）

## Objective
自分以外の人が触れる最小限の Web インターフェースを構築する。ワーク断面の描画・パラメータ設定・最適化実行・結果表示・STL ダウンロードまでを一気通貫で提供する。バックエンドは Phase 2 の `gripperforge_engine` を呼び出す。

**意図的に省くもの**：3D ビューア、接触解析、材料 DB、ユーザー認証、課金。

## Input Requirements
- `docs/requirements.md`, `docs/plan.md`, `docs/io-spec.md`（Phase 3）, `docs/tech-stack.md`, `docs/constraints.md`
- `outputs/phase-02/src/gripperforge_engine/` — バックエンドが依存
- `outputs/phase-02/README.md` — API 使用方法

## Output Specification
成果物ディレクトリ：`outputs/phase-03/`

### 必須ファイル構成
```
outputs/phase-03/
├── README.md                           # システム概要 + 起動手順
├── docker-compose.yml                  # 任意：開発環境の一発起動
├── backend/
│   ├── requirements.txt
│   ├── pyproject.toml or setup.py
│   ├── src/
│   │   └── gripperforge_api/
│   │       ├── __init__.py
│   │       ├── main.py                 # FastAPI app
│   │       ├── routes/
│   │       │   ├── jobs.py
│   │       │   └── history.py
│   │       ├── services/
│   │       │   ├── job_queue.py        # asyncio ベースのキュー
│   │       │   └── optimizer_service.py # gripperforge_engine 呼び出しラッパ
│   │       ├── models/
│   │       │   └── job.py              # Pydantic v2 モデル
│   │       └── storage/
│   │           ├── file_store.py       # STL / PNG の保存
│   │           └── history_db.py       # SQLite（任意）
│   └── tests/
│       ├── test_routes.py
│       ├── test_job_queue.py
│       └── test_optimizer_service.py
└── frontend/
    ├── package.json
    ├── package-lock.json
    ├── tsconfig.json
    ├── vite.config.ts
    ├── index.html
    ├── src/
    │   ├── main.tsx
    │   ├── App.tsx
    │   ├── components/
    │   │   ├── WorkpieceCanvas.tsx     # 断面描画 UI
    │   │   ├── ParamPanel.tsx          # パラメータ設定
    │   │   ├── ResultViewer.tsx        # 密度分布 PNG 表示
    │   │   ├── JobList.tsx             # 履歴一覧
    │   │   └── StlDownload.tsx
    │   ├── api/
    │   │   └── client.ts               # fetch ラッパ
    │   └── styles/
    │       └── main.css
    └── tests/
        └── App.test.tsx                # 最低限の smoke test
```

### README.md の必須セクション
1. **概要** — システム全体像（フロント + API + エンジン）
2. **前提条件** — Python, Node.js, npm
3. **起動手順（手動）**
   - バックエンド：`cd backend && pip install -e . && uvicorn gripperforge_api.main:app --reload`
   - フロント：`cd frontend && npm install && npm run dev`
4. **起動手順（Docker Compose、任意）**
5. **使い方** — 画面フロー、スクリーンショット
6. **API 一覧** — エンドポイント・リクエスト例・レスポンス例
7. **テスト実行**
8. **トラブルシューティング**

### API エンドポイント一覧
| メソッド | パス | 目的 |
|---|---|---|
| POST | `/api/jobs` | 最適化ジョブ投入 |
| GET | `/api/jobs/{job_id}` | ジョブ状態取得 |
| GET | `/api/jobs/{job_id}/stl` | STL ダウンロード |
| GET | `/api/jobs/{job_id}/preview.png` | プレビュー画像 |
| GET | `/api/history` | 過去ジョブ一覧 |
| GET | `/healthz` | ヘルスチェック |

## Quality Criteria
- [ ] README.md 通りに手動起動でフロント + バックエンドが立ち上がる
- [ ] フロントでワーク断面を描画 → パラメータ設定 → 「最適化実行」ボタン → 結果表示 → STL ダウンロードの一連のフローが動く
- [ ] ジョブは非同期で実行され、UI からポーリングで進捗取得できる
- [ ] バックエンドは Phase 2 の `gripperforge_engine` を介して最適化を行う（再実装しない）
- [ ] API 入力は Pydantic で厳格に検証され、不正入力は 422 を返す
- [ ] バックエンドに最低 3 つの pytest（ルート、キュー、サービス）、フロントに 1 つの smoke test が存在し PASS する
- [ ] CORS 設定は `localhost` 開発用途に限定されている
- [ ] ファイルアップロード・ダウンロードでディレクトリトラバーサルが防止されている
- [ ] `reports/integration-demo.md` に起動からダウンロードまでのスクリーンショット付き手順がある

## Procedure

### Step 1: アーキテクチャ・データフロー設計
1. バックエンドのレイヤー構成（routes → services → engine）を決定
2. ジョブキューの方式：MVP は単一プロセス `asyncio.Queue` + バックグラウンドタスク。将来 Redis + RQ 移行を README に明記
3. フロントの状態管理：React Hook + ポーリング（WebSocket は不採用）

**→ `sdd-software-architect` に設計レビューを依頼**

### Step 2: バックエンド実装（ルートとモデル）
1. `main.py` に FastAPI app、CORS ミドルウェア、ライフスパン（起動時にジョブキュー起動）
2. `models/job.py` — `JobCreateRequest`, `JobStatusResponse`, `JobResult`
3. `routes/jobs.py`, `routes/history.py`
4. `storage/file_store.py` — UUID ベースのファイル保存、パス検証

### Step 3: ジョブキューと Optimizer サービス
1. `services/job_queue.py` — バックグラウンドワーカーがキューを消費し、`optimizer_service.run_optimization` を呼ぶ
2. `services/optimizer_service.py` — Phase 2 の `gripperforge_engine.optimize` を呼び、結果を `file_store` に保存
3. ジョブ状態は in-memory dict（MVP）で保持、再起動後は消える旨を README に明記

### Step 4: フロントエンド実装
1. Vite + React + TypeScript プロジェクトを初期化
2. `WorkpieceCanvas.tsx` — マウスで多角形描画、境界条件マーカー配置
3. `ParamPanel.tsx` — volfrac, penal, rmin, maxloop 等のスライダー/入力
4. `ResultViewer.tsx` — PNG 表示、STL ダウンロードリンク
5. `JobList.tsx` — 履歴一覧（API からフェッチ）
6. `api/client.ts` — fetch ラッパ、エラーハンドリング

### Step 5: エラーハンドリングとセキュリティ
1. バックエンド：HTTP 例外ハンドラ、不正入力は 422、内部エラーは 500 + ログ
2. ファイルパスは常に `file_store` 経由で正規化し、`..` を排除
3. CORS 許可を `http://localhost:5173` に限定
4. 入力サイズ上限（JSON 1 MB）
5. フロント：API エラーをトースト表示、リトライ可能な操作はリトライボタン

**→ `sdd-security-reviewer` にセキュリティレビューを依頼（入力検証、CORS、パス検証、情報漏洩）**

### Step 6: テスト
1. バックエンド：`test_routes.py`（httpx AsyncClient）, `test_job_queue.py`, `test_optimizer_service.py`
2. フロント：Vitest で `App.test.tsx` の smoke test
3. E2E 簡易テスト：`reports/integration-demo.md` に手動実施手順を記載

**→ `sdd-qa-test-engineer` にテスト観点レビューを依頼**

### Step 7: 統合デモとドキュメント
1. 1 ケース（例：Phase 2 の cylinder_30mm）を UI から実行し、スクリーンショットを撮る
2. README にフロー図 + スクリーンショットを埋める

**→ `sdd-doc-editor` に README と integration-demo のレビューを依頼**

### Step 8: .metadata.json 作成

## Common Pitfalls
- **バックエンドが `gripperforge_engine` を再実装** → 絶対に Phase 2 を import する。重複実装は検証コストを倍増させる
- **CORS を `*` のまま放置** → MVP でも localhost に限定
- **ジョブの結果を DB に入れない** → MVP は in-memory 可だが、**再起動で履歴が消える旨を README に明記**
- **フロントがバックエンド実装を待ってから作り始める** → API スタブ（モック）で並行開発できる
- **`WorkpieceCanvas` の座標系と Engine の座標系が食い違う** → フロントで表示 px、バックで mm なので変換層を明確にする
- **ポーリング間隔が短すぎてサーバ負荷** → 1 〜 2 秒間隔で十分

## Troubleshooting
| 症状 | 原因 | 対処法 | 再開ポイント |
|---|---|---|---|
| `ImportError: gripperforge_engine` | バックエンドの仮想環境に Phase 2 パッケージが入っていない | `pip install -e outputs/phase-02/` | Step 2 |
| CORS エラーで API 呼び出せない | Origin 不一致 | `main.py` の CORS 設定を確認 | Step 2 |
| ジョブが終わらない | ワーカーが起動していない | `main.py` のライフスパンでワーカー起動確認 | Step 3 |
| フロントで STL が壊れて見える | 3D ビューアは MVP 対象外 | STL はダウンロードのみ、ビューア導入は後回し | — |

## Examples

### `POST /api/jobs` リクエスト例
```json
{
  "workpiece": {
    "workpiece_id": "cyl_30",
    "boundary": [[0,0],[30,0],[30,30],[0,30]],
    "grip_points": [[5,15],[25,15]],
    "contact_direction": [1,0],
    "output_point": [15,15],
    "output_direction": [-1,0],
    "design_domain": {"nelx":100,"nely":100,"size_mm":[50,50]}
  },
  "params": {"volfrac":0.4, "penal":3.0, "rmin":1.5, "maxloop":200}
}
```

### レスポンス
```json
{ "job_id": "8b1e...", "status": "queued", "created_at": "..." }
```
