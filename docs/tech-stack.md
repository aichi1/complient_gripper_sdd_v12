# GripperForge — 技術スタック

## 核となる言語・ライブラリ

### 最適化エンジン（Phase 1, 2）
| 項目 | 選定 | 代替・補足 |
|---|---|---|
| 言語 | Python 3.11+ | 3.10 以上で動作する想定 |
| 数値計算 | NumPy ≥ 1.26 | |
| スパース線形代数 | SciPy ≥ 1.11 （`scipy.sparse`, `scipy.sparse.linalg`） | 将来 `pyamg` で高速化検討 |
| 可視化（開発時） | matplotlib ≥ 3.8 | Phase 2 以降、`trimesh` を STL ビューア代替として利用可 |
| メッシュ・STL | `numpy-stl` または `trimesh` | Phase 2 で採用決定 |
| テストフレームワーク | `pytest` ≥ 8.0 | |
| 型チェック（任意） | `mypy` または `pyright` | 必須ではないが推奨 |

### バックエンド（Phase 3）
| 項目 | 選定 |
|---|---|
| Web フレームワーク | FastAPI ≥ 0.110 |
| ASGI サーバ | `uvicorn[standard]` |
| ジョブキュー | Phase 3 初版は `asyncio` + in-process キュー（将来 Redis + RQ を検討） |
| スキーマ | Pydantic v2 |
| ストレージ | ローカルファイルシステム（MVP）+ SQLite 履歴（任意） |

### フロントエンド（Phase 3）
| 項目 | 選定 |
|---|---|
| フレームワーク | React 18 + TypeScript |
| ビルド | Vite |
| スタイリング | Tailwind CSS（任意） |
| 描画 | HTML Canvas or `svg.js` / `konva` — ワーク断面の描画 UI 用 |
| HTTP | `fetch` または `axios` |
| 状態管理 | React Hook ベース（Redux 等は導入しない） |

## リポジトリ構成指針
```
.
├── docs/                      # 仕様（本ディレクトリ）
├── skills/                    # SDD 手順書
├── outputs/
│   ├── phase-01/              # PoC 実装
│   │   ├── src/
│   │   │   └── gripperforge_poc/
│   │   ├── tests/
│   │   └── reports/
│   ├── phase-02/              # コアエンジン
│   │   └── src/gripperforge_engine/
│   ├── phase-03/              # Web アプリ
│   │   ├── backend/
│   │   └── frontend/
│   ├── phase-04/              # 実ワーク検証
│   │   └── cases/
│   └── phase-05/              # 発信物・顧客計画
│       ├── articles/
│       ├── demo_video/
│       └── outreach/
└── templates/                 # SDD 内部テンプレート
```

## 依存管理
- Python: `requirements.txt` を各 Phase ディレクトリに配置（Phase 1 → Phase 2 で累積・更新）
- バージョン固定方針：MVP 段階では上限を設けない（`>=` のみ）。Phase 5 で `==` または `~=` に切替える
- フロント：`package.json` + `package-lock.json`。ロックファイルは commit 対象

## CI / 開発環境
- MVP では CI は必須としない（手動テスト実行で可）
- 単体テストは `pytest -v` を各 Phase の Quality Criteria に組み込む
- Lint：`ruff`（任意）

## 対応 OS
- 一次ターゲット：Linux（Ubuntu 22.04+）, macOS 14+
- 二次：Windows 10/11（WSL2 推奨）
- 3Dプリンタ制御ソフトはホスト OS 依存だが、GripperForge 本体は OS 非依存とする

## 前提とする外部環境
- 3Dプリンタ：FDM 方式で TPU フィラメント対応（Shore 硬度 95A 付近）
- グリッパーボディ：SMC MHZ2-16D クラスの平行 2 爪（取付 I/F を Phase 2 で具体化）
- CAD 入力経路：STEP / DXF / ユーザー描画（Phase 3 で確定）
