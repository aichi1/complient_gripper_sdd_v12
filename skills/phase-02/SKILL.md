# Phase 2: コア最適化エンジン（実用 2D SIMP エンジン + STL 出力）

> カテゴリ：`small_implementation`
> 元 Roadmap：Phase 1 コア最適化エンジン
> 前提：Phase 1 完了（PoC が 3 ケースで収束している）

## Objective
Phase 1 の PoC を実用レベルに引き上げる。任意のワーク 2D 断面形状に対して境界条件を自動生成し、密度フィルタ + Heaviside projection で良好な二値化結果を得て、3D 化（押し出し）して STL をエクスポートできるエンジン `gripperforge_engine` を完成させる。複数のワーク形状（5 種類以上）で再現性ある結果を得る。

## Input Requirements
- `docs/requirements.md`, `docs/plan.md`, `docs/io-spec.md`（Phase 2）, `docs/tech-stack.md`, `docs/constraints.md`
- `outputs/phase-01/` のソースコード（リファクタ元として参照）
- `outputs/phase-01/reports/algorithm-notes.md`（数式整理）

## Output Specification
成果物ディレクトリ：`outputs/phase-02/`

### 必須ファイル構成
```
outputs/phase-02/
├── README.md                          # 実行手順 + API 使用例
├── requirements.txt
├── src/
│   └── gripperforge_engine/
│       ├── __init__.py
│       ├── api.py                      # 高レベル API（optimize 関数）
│       ├── geometry.py                 # ワーク断面の読込・検証・境界条件生成
│       ├── mesh.py                     # 構造格子生成、DOF マッピング
│       ├── solver.py                   # FEM 解析（疎行列 CG / 直接解）
│       ├── optimizer.py                # SIMP + OC or MMA
│       ├── filters.py                  # 密度フィルタ + Heaviside projection
│       ├── export.py                   # PNG / NPY / STL 出力
│       ├── cli.py                      # コマンドライン入口
│       └── schemas.py                  # Pydantic による設定スキーマ
├── tests/
│   ├── test_geometry.py
│   ├── test_mesh.py
│   ├── test_solver.py
│   ├── test_optimizer.py
│   ├── test_filters.py
│   ├── test_export.py
│   └── test_api_integration.py        # E2E 統合テスト
├── benchmarks/
│   └── run-benchmarks.py               # 5 ケースの一括ベンチマーク
├── results/
│   └── case-{01..05}/                  # 各ケースの実行結果
└── reports/
    ├── engine-architecture.md          # モジュール構成とデータフロー
    ├── validation-report.md            # 5 ケースの定量評価
    └── performance-report.md           # 計算時間・メモリ・収束性
```

### README.md の必須セクション
1. **概要** — Phase 1 との差分（実用機能の追加）
2. **前提条件**
3. **インストール**
4. **CLI 使用例** — JSON 設定ファイルからの一括実行
5. **Python API 使用例** — `from gripperforge_engine import optimize`
6. **入力形式** — ワーク断面 JSON スキーマの説明
7. **出力** — PNG / NPY / STL の意味
8. **テスト / ベンチマーク実行**
9. **トラブルシューティング**

### データフロー
```
Workpiece JSON/DXF → geometry.load_workpiece()
    → mesh.generate_grid() → mesh.apply_boundary_conditions()
    → optimizer.run(config)
        ↳ solver.solve(K, F) ← 2 荷重ケース
        ↳ filters.apply(density, rmin, beta)
        ↳ OC 更新
    → export.to_png() / export.to_npy() / export.to_stl()
```

## Quality Criteria
- [ ] README.md にインストール・実行・API 使用例があり、コピペで動く
- [ ] Pydantic スキーマにより不正入力は実行前に弾かれる
- [ ] 5 種類以上のワーク形状（Phase 1 の 3 ケース + 新規 2 ケース）で収束する
- [ ] Heaviside projection により密度分布が 0/1 に二値化される（中間密度要素が全体の 5% 未満）
- [ ] STL 出力が 3Dプリント可能（non-manifold エラーなし、退化三角形なし）
- [ ] 5 ケース中 4 以上で計算時間が 3 分以内
- [ ] `pytest -v` で全 PASS（統合テスト含む）
- [ ] `benchmarks/run-benchmarks.py` が 5 ケースを一括実行し `reports/validation-report.md` を生成する
- [ ] `reports/engine-architecture.md` にモジュール構成図とデータフローが示されている
- [ ] Phase 3（Web UI）から呼び出すための API が `api.py` で定義され、ドキュメント化されている

## Procedure

### Step 1: アーキテクチャ設計
1. `reports/engine-architecture.md` を先に書く。モジュール分割、データフロー、責務境界を明示
2. Phase 1 のコードを参照し、流用/リファクタ/新規作成の区分を整理

**→ `sdd-software-architect` に設計レビューを依頼（責務分離、拡張性、依存方向）**

### Step 2: スキーマと入力層
1. `schemas.py` に Pydantic モデルを定義：
   - `WorkpieceGeometry`（頂点リスト、荷重点、固定点、出力点）
   - `OptimizerConfig`（nelx/nely, volfrac, penal, rmin, filter_type, beta_schedule, maxloop）
   - `MaterialProps`（E, nu）
2. `geometry.py` にワーク JSON の読込・検証・境界条件自動生成を実装
3. DXF ローダは最低限（2D ポリライン → 頂点リスト変換）

### Step 3: メッシュとソルバー
1. `mesh.py` — 構造格子（nelx × nely）と DOF マッピング
2. `solver.py` — スパース剛性行列組立 + 疎行列線形ソルバー（`scipy.sparse.linalg.spsolve`）
3. 大規模ケース向けに `pyamg` による AMG も選択肢として用意（必須ではない）

### Step 4: 最適化ループとフィルタ
1. `filters.py`：密度フィルタ + Heaviside projection（β スケジュール：初期 β=1、50 反復ごとに 2 倍）
2. `optimizer.py`：OC 更新を SIMP + Heaviside projection に対応させる
3. 2 荷重ケース解析を汎用化

**→ `sdd-domain-sme` に数理レビューを依頼（Heaviside projection の導入、連続性の扱い、反復安定性）**

### Step 5: 出力層（特に STL）
1. `export.to_png` — 密度分布可視化
2. `export.to_npy` — 密度フィールドのバイナリ保存
3. `export.to_stl` — 2D 密度 → 3D 押し出し → メッシュ生成 → STL 書き出し
   - `skimage.measure.find_contours` で等値線抽出（密度閾値 0.5）
   - 等値線を三角形分割し、押し出して立体化
   - `trimesh` で non-manifold / 退化三角形チェック
4. STL は ASCII/binary 両対応

### Step 6: CLI と API
1. `cli.py` — JSON 設定ファイル受け取り、結果を `results/{case}/` に保存
2. `api.py` — Phase 3 から import される高レベル関数 `optimize(config: OptimizerConfig) -> OptimizationResult`
3. `OptimizationResult` は density field、STL bytes、収束履歴、評価指標を含む

### Step 7: テスト
1. 各モジュール単体テスト
2. `test_api_integration.py` — 1 ケースの E2E：JSON 入力 → STL 出力まで
3. STL の妥当性検証：`trimesh` で `is_watertight`, `is_winding_consistent`

**→ `sdd-qa-test-engineer` にテスト観点レビューを依頼**

### Step 8: ベンチマークと検証レポート
1. `benchmarks/run-benchmarks.py` で 5 ケース一括実行
2. 計算時間・メモリ・収束イテレーション数・中間密度率を記録
3. `reports/validation-report.md` を自動生成
4. `reports/performance-report.md` にプロファイリング結果を記載

### Step 9: README とドキュメント整備
**→ `sdd-doc-editor` に README とレポートの情報設計レビューを依頼**

### Step 10: .metadata.json 作成

## Common Pitfalls
- **Heaviside projection の導入タイミングが早すぎる** → 初期反復で進まなくなる。β=1 で 20〜50 反復回してから徐々に増やす
- **STL 生成時に non-manifold エッジが残る** → find_contours の結果を厳密に閉曲線化していない。`skimage.measure.approximate_polygon` で後処理する or `trimesh.repair` を使う
- **API を CLI と一体化したまま** → Phase 3 で import できない。必ず CLI とロジックを分離する
- **Pydantic v1 系のコードを書く** → v2 を使用。`model_config`, `Field` の API が違う
- **密度フィルタを畳み込みで素朴に実装** → nelx × nely が 100 を超えると遅い。スパース行列で事前計算する

## Troubleshooting
| 症状 | 原因 | 対処法 | 再開ポイント |
|---|---|---|---|
| STL に穴が空いている | find_contours の閉じ残し | 輪郭を閉じるポスト処理、trimesh.repair.fill_holes を使用 | Step 5 |
| 計算が 3 分以内に収まらない | 直接解が重い | `scipy.sparse.linalg.cg` + 前処理 or `pyamg` 導入 | Step 3 |
| 中間密度が消えない | Heaviside β が小さい | 最終 β を 8〜16 まで増やす、ペナルティ 4.0 へ | Step 4 |
| ベンチマーク結果が不安定 | 初期密度が均一で多解問題 | 初期密度を volfrac + 小さい摂動でスタート | Step 4 |

## Examples

### ワーク JSON スキーマ例
```json
{
  "workpiece_id": "cylinder_30mm",
  "boundary": [[0,0],[30,0],[30,30],[0,30]],
  "grip_points": [[5,15],[25,15]],
  "contact_direction": [1,0],
  "output_point": [15,15],
  "output_direction": [-1,0],
  "design_domain": {"nelx":100,"nely":100,"size_mm":[50,50]}
}
```

### Python API 使用例
```python
from gripperforge_engine import optimize, OptimizerConfig, load_workpiece

workpiece = load_workpiece("cases/cylinder_30mm.json")
config = OptimizerConfig(
    volfrac=0.4,
    penal=3.0,
    rmin=1.5,
    filter_type="density",
    beta_schedule="exponential",
    maxloop=200,
)
result = optimize(workpiece, config)
result.save_stl("out.stl")
result.save_png("out.png")
```
