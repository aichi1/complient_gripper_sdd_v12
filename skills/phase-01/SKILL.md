# Phase 1: 技術検証 PoC（SIMP 88 行コードの Python 再実装 + コンプライアント対応）

> カテゴリ：`small_implementation`
> 元 Roadmap：Phase 0 技術検証

## Objective
Sigmund の 88 行トポロジー最適化コード（剛性最大化）を Python で再実装し、目的関数をコンプライアントメカニズム向け（mutual mean compliance 最大化）に書き換える。基本テストケース（円筒・直方体・L 字型）で最適化を実行し、3Dプリント品が設計通り変形してワークを把持できることを確認する。Go/No-Go 判定点。

## Input Requirements
- `docs/requirements.md` — 成功条件（3 種類以上のワーク形状で把持成功）
- `docs/plan.md` — Phase 1 の位置づけ
- `docs/tech-stack.md` — Python / NumPy / SciPy を使用
- `docs/io-spec.md` — Phase 1 の入出力仕様
- `docs/constraints.md` — 計算資源制約・数値制約
- `project_init.md` — 背景・動機

## Output Specification
成果物ディレクトリ：`outputs/phase-01/`

### 必須ファイル構成
```
outputs/phase-01/
├── README.md                       # 実行手順、依存、使い方
├── requirements.txt                # pip 依存関係
├── src/
│   └── gripperforge_poc/
│       ├── __init__.py
│       ├── topopt.py               # SIMP + OC 法のコア実装
│       ├── objectives.py           # compliance / compliant_mechanism 目的関数
│       ├── filters.py              # 密度フィルタ
│       ├── cases.py                # テストケース定義（円筒・直方体・L 字）
│       └── cli.py                  # コマンドライン入口
├── tests/
│   ├── test_topopt.py              # SIMP 基本動作のテスト
│   ├── test_objectives.py          # 目的関数の勾配整合性テスト
│   └── test_cases.py               # 各ケースの境界条件生成テスト
├── results/                        # 実行結果（初期は空）
│   └── .gitkeep
└── reports/
    ├── algorithm-notes.md          # アルゴリズム解説・数式
    └── physical-validation.md      # 3Dプリント後の把持テスト結果
```

### README.md の必須セクション
1. **概要** — GripperForge PoC が何をするか（1〜2 行）
2. **前提条件** — Python 3.11+、NumPy、SciPy、matplotlib
3. **インストール手順** — `pip install -r requirements.txt`
4. **使い方**
   - `python -m gripperforge_poc.cli --case cylinder --objective compliant_mechanism`
   - 主要オプション一覧
5. **テスト実行** — `pytest -v`
6. **出力の見方** — 密度分布 PNG、収束履歴 CSV の読み方
7. **3Dプリント手順** — STL はまだ出力しないが、密度画像から設計意図を読み取る方法を記載
8. **よくあるエラー** — NaN / 発散時の対処

### ソースコード指針
- **`topopt.py`**：SIMP（ペナルティ付き密度）+ OC（Optimality Criteria）法の 1 反復ループ。200 行以内に収める
- **`objectives.py`**：
  - `compliance_objective(K, U, F) -> (value, sensitivity)`
  - `compliant_mechanism_objective(K, U_in, U_out, F_in, L_out) -> (value, sensitivity)`
  - **mutual mean compliance** を最大化するため、実荷重（F_in）とダミー荷重（L_out: 出力点の求める変位方向に単位荷重）の 2 荷重ケース解析を行う
- **`filters.py`**：感度フィルタと密度フィルタの両方を実装、切り替え可能に
- **`cases.py`**：各テストケースごとに `(design_domain, boundary_conditions, loads, fixed_dofs, output_dof) -> Case` を返す
- **`cli.py`**：`argparse`、`--case`, `--objective`, `--nelx`, `--nely`, `--volfrac`, `--penal`, `--rmin`, `--maxloop`, `--output-dir` をサポート

### 数値妥当性のセルフチェック
- 有限差分による勾配整合性テスト（`test_objectives.py`）
- 対称境界条件のケースで対称な密度分布が得られることの確認

## Quality Criteria
- [ ] README.md にインストール・実行手順があり、コピペで動く
- [ ] 依存関係は `requirements.txt` にピン留めまたは下限指定で明記されている
- [ ] CLI が `--help` を出し、主要オプションの説明がある
- [ ] 3 種類以上のテストケース（円筒・直方体・L 字）が実装され、それぞれ最適化が収束する
- [ ] 目的関数の勾配が有限差分と 1% 以内で一致する（`test_objectives.py`）
- [ ] コンプライアントメカニズム目的関数で mutual mean compliance が反復ごとに増加する（改善方向へ収束）
- [ ] `pytest -v` が全 PASS
- [ ] `reports/algorithm-notes.md` で SIMP 法の数式（ペナルティ関数、OC 更新式、フィルタ）を明記
- [ ] `reports/physical-validation.md` に 3Dプリント手順と把持テスト結果（または実施予定プロトコル）が記録されている
- [ ] `docs/requirements.md` の Phase 1 成功条件を全て満たしている

## Procedure

### Step 1: 仕様読み込みと設計
1. `docs/requirements.md`, `docs/io-spec.md`, `docs/tech-stack.md` を読む
2. Sigmund の 88 行コードのアルゴリズム構造（K 組立、U 解、感度計算、OC 更新）を `reports/algorithm-notes.md` にまず整理して書く
3. コンプライアントメカニズム目的関数の定式化を明記（なぜ 2 荷重ケースが必要か）

### Step 2: ディレクトリ構造作成
1. `outputs/phase-01/src/gripperforge_poc/`, `tests/`, `results/`, `reports/` を作成
2. `__init__.py`, `.gitkeep` を配置

### Step 3: 基本実装（剛性最大化版）
1. `topopt.py` の K 組立ルーチン（8 ノード要素の要素剛性行列、境界条件適用）を実装
2. 密度フィルタ `filters.py` を実装
3. OC 更新ルーチンを実装
4. `objectives.py` に `compliance_objective` を実装
5. `cases.py` に MBB 梁の教科書ケースを定義して動作確認（Sigmund 88 行と同等の結果になるか）

**→ `sdd-software-architect` にコード構造レビューを依頼（モジュール分割、責務分離、拡張性）**

### Step 4: コンプライアントメカニズム化
1. `objectives.py` に `compliant_mechanism_objective` を追加
2. 2 荷重ケース解析（実荷重 + ダミー荷重）の実装
3. 感度計算の差し替え
4. `cases.py` に把持動作を模した円筒・直方体・L 字ケースを追加（出力点・入力荷重の定義含む）

**→ `sdd-domain-sme` に数理的妥当性レビューを依頼（目的関数の定式化、境界条件の物理的意味、符号・感度の整合性）**

### Step 5: エラーハンドリング
1. 不正引数 → argparse がエラー表示して exit 2
2. 収束しない → 警告 + 最終状態保存
3. NaN / Inf → 例外をキャッチし、スナップショット保存して exit 3
4. 入力ケース名が未定義 → 利用可能ケース一覧を表示

**→ `sdd-security-reviewer` に入力検証・例外処理レビューを依頼**

### Step 6: テスト作成
1. `test_topopt.py` — 対称境界条件で対称解が得られる、境界条件のない DOF にアクセスしない
2. `test_objectives.py` — 勾配の有限差分検証（コンプライアンス、mutual mean compliance の両方）
3. `test_cases.py` — 各ケースの DOF 番号・荷重・固定点が正当

**→ `sdd-qa-test-engineer` にテスト観点レビューを依頼（穴はないか、異常系は網羅か）**

### Step 7: 実行と結果保存
1. 各ケースを実行し `results/` に `{case}_density.png`, `{case}_history.csv`, `{case}_topology.npy` を保存
2. 収束が怪しいケースはパラメータを調整

### Step 8: README 作成
1. `README.md` を Output Specification 通りに記述
2. スクリーンショット（密度分布）を README に埋め込む
3. 3Dプリント → 把持テストの実施手順を `reports/physical-validation.md` に記載

**→ `sdd-doc-editor` に README と physical-validation の情報設計レビューを依頼**

### Step 9: .metadata.json 作成
```json
{
  "phase": 1,
  "status": "builder_complete",
  "deliverables": ["README.md", "src/", "tests/", "results/", "reports/"],
  "docs_referenced": ["requirements.md", "plan.md", "tech-stack.md", "io-spec.md", "constraints.md"],
  "specialists_invoked": ["software_architect", "domain_sme", "security_reviewer", "qa_test_engineer", "doc_editor"],
  "builder_notes": "..."
}
```

## Common Pitfalls
- **Sigmund 88 行をそのままコピー** → 論文・教科書由来なので構造を理解してから実装すること。コピペは数式の追跡可能性を失う
- **コンプライアントメカニズムの目的関数を compliance と混同** → 最小化ではなく **最大化** (mutual mean compliance)。符号ミスで最適化が逆方向に走る頻発エラー
- **チェッカーボード対策を省略** → フィルタを必ず入れる。見た目は最適化されているようでも FEM では非物理的な解になる
- **密度が 0 になる領域で数値不安定** → 最小密度 `Emin = 1e-9` を使った SIMP の標準化を忘れない
- **テストで勾配整合性を確認しない** → Phase 2 で目的関数を拡張する際にバグが入り込みやすい。Phase 1 時点で固める
- **境界条件を hard-code しすぎる** → ケース単位で関数化しておく。Phase 2 で動的生成に移行しやすくなる
- **3Dプリント実施を後回し** → 物理検証こそが Phase 1 の Go/No-Go。設計通り変形するかは数値だけでは判断できない

## Troubleshooting
| 症状 | 原因 | 対処法 | 再開ポイント |
|---|---|---|---|
| `LinAlgError: Matrix is singular` | 固定 DOF の指定漏れで剛体モードが残っている | 固定 DOF を再確認、K に単位行列加算のダミー処理を一時導入しデバッグ | Step 3 |
| 目的関数が振動・発散 | フィルタ半径が小さすぎる or `penal` が急激 | `rmin = 1.5`、`penal = 3.0` からスタートし、段階的に増加 | Step 4 |
| 勾配テスト失敗（誤差 > 1%） | 感度計算の実装バグ | 有限差分と解析値の各要素を比較し、符号・スケーリングを確認 | Step 4, Step 6 |
| 3Dプリント品がちぎれる | 最小厚み不足 or TPU の引張強度不足 | 最小メンバ厚 1.5 mm を制約条件化、材料を硬めの TPU に変更 | 物理検証のみ再実施 |
| 設計通りの変形にならない | 境界条件ミス（荷重方向・固定点） | `cases.py` と実機治具を付き合わせて再定義 | Step 4 |

## Examples

### `compliant_mechanism_objective` の骨格（擬似コード）
```python
def compliant_mechanism_objective(K, F_in, L_out, free_dofs, xPhys, penal, Emin, E0):
    # 2 荷重ケースの解析
    U_in = solve(K, F_in, free_dofs)       # 実荷重による変位
    U_out = solve(K, L_out, free_dofs)     # 出力点ダミー荷重による随伴変位

    # 目的関数: mutual mean compliance = L_out^T @ U_in
    obj = L_out @ U_in

    # 感度: dC/dx_e = -penal * (E0 - Emin) * xPhys^(penal-1) * (u_in_e^T @ ke @ u_out_e)
    dc = -penal * (E0 - Emin) * xPhys**(penal - 1) * elementwise_product(U_in, U_out, ke)
    return obj, dc
```

### 推奨 CLI 実行例
```bash
# MBB 梁（SIMP 動作確認）
python -m gripperforge_poc.cli --case mbb --objective compliance --nelx 60 --nely 20 --volfrac 0.5

# コンプライアント円筒グリッパー
python -m gripperforge_poc.cli --case cylinder --objective compliant_mechanism --nelx 80 --nely 40 --volfrac 0.4
```

### `reports/physical-validation.md` のアウトライン
```markdown
# Phase 1 物理検証レポート

## 実施概要
- 実施日、使用機材（3Dプリンタ機種、フィラメント）、担当者
- 印刷済みフィンガー枚数

## テストケースごとの結果
### Case 1: 円筒（Φ30mm）
- 印刷条件：...
- 把持動作写真／動画
- 変形の観察：設計通りか？
- 把持力：把持可能な最大重量

## Go/No-Go 判定
- [ ] 3 ケース中 X ケースで把持成功
- 判定結果：Go / No-Go
```
