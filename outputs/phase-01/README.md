# GripperForge Phase 1 — Proof of Concept

> Python re-implementation of Sigmund's 88-line topology optimization code,
> extended with a **compliant-mechanism objective** (mutual mean compliance)
> for gripper finger design.

## 概要

本 PoC は GripperForge プロジェクトの **Phase 1 — 技術検証** 成果物。
Sigmund (Andreassen et al. 2011) の 88-line MATLAB 版トポロジー最適化コードを
Python で再実装し、目的関数を **剛性最大化** / **コンプライアントメカニズム
（mutual mean compliance 最大化）** の 2 種類に切替可能にした。
基本的な形状ケース 4 種（MBB 梁 + 3 種類のグリッパーフィンガー）について最適化
を実行して収束を確認し、3Dプリント検証プロトコルを整備する。

Go/No-Go 判定点の成果物であり、Phase 2 で実用エンジン `gripperforge_engine` に
リファクタする土台となる。

## 前提条件

- Python 3.11+（3.10 も動作するはず）
- NumPy ≥ 1.26
- SciPy ≥ 1.11
- matplotlib ≥ 3.8（結果可視化用）
- pytest ≥ 8.0（テスト実行用）

## インストール手順

```bash
cd outputs/phase-01
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

PoC は `setup.py` / `pyproject.toml` を持たないため、パスを通して実行する。

```bash
export PYTHONPATH=$PWD/src
```

## 使い方

### CLI

```bash
# MBB 梁（Sigmund 88-line と同等のベンチマーク、剛性最大化）
python -m gripperforge_poc.cli \
    --case mbb --objective compliance \
    --nelx 60 --nely 20 --volfrac 0.5 \
    --penal 3.0 --rmin 1.5 --maxloop 120 \
    --output-dir results

# コンプライアント円筒グリッパー
python -m gripperforge_poc.cli \
    --case cylinder --objective compliant_mechanism \
    --nelx 40 --nely 20 --volfrac 0.4 \
    --penal 3.0 --rmin 1.5 --maxloop 120 \
    --output-dir results

# 直方体ワーク向け
python -m gripperforge_poc.cli --case box --nelx 40 --nely 20 --maxloop 120

# L 字ワーク向け
python -m gripperforge_poc.cli --case lshape --nelx 40 --nely 20 --maxloop 120
```

### 主要オプション

| オプション | 既定値 | 説明 |
|---|---|---|
| `--case` | — | 必須。`mbb` / `cylinder` / `box` / `lshape` |
| `--objective` | case 依存 | `compliance` / `compliant_mechanism` |
| `--nelx`, `--nely` | case 既定 | メッシュ解像度 |
| `--volfrac` | case 既定 | 体積分率制約 |
| `--penal` | 3.0 | SIMP ペナルティ指数 |
| `--rmin` | 1.5 | フィルタ半径（要素長単位） |
| `--maxloop` | 200 | 最大反復回数 |
| `--filter` | `density` | `density` / `sensitivity` |
| `--output-dir` | `./results` | 結果の保存先 |
| `--no-save` | — | ファイル保存をスキップ |

### Python API

```python
from gripperforge_poc.cases import load_case
from gripperforge_poc.filters import build_filter
from gripperforge_poc.objectives import compliant_mechanism_objective
from gripperforge_poc.topopt import build_fem_context, optimize

case = load_case("cylinder", nelx=40, nely=20)
ctx  = build_fem_context(
    case.nelx, case.nely, case.fixed_dofs,
    spring_dofs=case.spring_dofs, spring_ks=case.spring_ks,
)
fm   = build_filter(case.nelx, case.nely, rmin=1.5)

def obj(x):
    return compliant_mechanism_objective(x, case.F_in, case.L_out, ctx)

result = optimize(obj, case.nelx, case.nely, fm, volfrac=0.4, maxloop=120)
print("converged:", result.converged, "iters:", result.iterations,
      "obj:", result.objective_value)
```

## テスト実行

```bash
cd outputs/phase-01
pytest -v
```

20 テスト。主なチェック：

- 要素剛性行列の対称性・剛体モード
- FEM コンテキストの DOF マッピング
- OC 更新の体積制約整合性
- **目的関数の勾配 vs 中央差分（有限差分）が 1% 以内**（compliance / compliant_mechanism 両方）
- MBB ベンチマークで compliance が反復ごとに減少する（非 NaN）
- 4 ケースの境界条件・出力点・固定 DOF の整合性

## 出力の見方

`results/` に保存される 3 種類のファイル：

- **`{case}_density.png`** — 物理密度 x-phys の可視化（0=空隙, 1=ソリッド）。
  横軸 `nelx`、縦軸 `nely`。黒い部分が「残すべき材料」。
- **`{case}_history.csv`** — 反復ごとの `(iteration, objective, change)`。
  compliance の場合は目的関数値そのもの、compliant_mechanism の場合は
  **`-(mutual mean compliance)` = -g** が表示される（最小化問題として扱うため）。
- **`{case}_topology.npy`** — 密度分布のバイナリ（`nelx × nely` NumPy 配列）。
  Phase 2 で 3D 化 / STL 出力するときの入力。

### 設計意図の読み取り方

まだ STL 出力はないため、設計意図は密度 PNG から読み取る：

1. **黒い領域の連結性**：入力荷重点から出力点まで連続的につながっているか
2. **薄い梁**：コンプライアントメカニズムでは細い梁が「ヒンジ」の役割
3. **対称性**：対称境界条件では密度も対称であること
4. **チェッカーボード有無**：細かく白黒が交互に出る場合はフィルタが効いていない

## 3Dプリント手順（Phase 1 時点）

PoC は STL 直接出力を持たない（Phase 2 で実装）。
Phase 1 では以下の手順で物理検証を行う：

1. `results/{case}_topology.npy` を読み込み、密度 > 0.5 の領域を 2D 輪郭として
   抽出する（`skimage.measure.find_contours` 等、別途手動で実施）
2. 得られた輪郭を CAD ソフト（Fusion 360, FreeCAD）で押し出し（厚み 10 mm）
3. FDM 3Dプリンタ + TPU 95A フィラメント（充填率 30%）で出力
4. 実機のグリッパーボディ（SMC MHZ2-16D 相当）に装着
5. テストワークで把持テスト、10 試行以上で成功率記録

詳細は `reports/physical-validation.md` を参照。

## よくあるエラー

| 症状 | 原因 | 対処 |
|---|---|---|
| `LinAlgError: Matrix is singular` | 固定 DOF 不足で剛体モードが残っている | `cases.py` の `fixed_dofs` を確認、最低 3 自由度を拘束 |
| 目的関数が振動 | フィルタ半径が小さすぎる、ペナルティが急 | `rmin` を 2.0 に、`penal` を 2.5 からスタート |
| 勾配テスト失敗 | 目的関数の感度式バグ | 有限差分との比較で要素ごとに符号をチェック |
| compliant の目的値が 0 近傍で停滞 | 入出力が構造的につながらない BC | `cases.py` の `spring_ks` を 0.05 に下げる、または入出力点を離す |
| NaN / Inf | 密度が完全に 0 で剛性が消える | `Emin` を 1e-9 のまま保持、初期密度を `volfrac` に |
| PNG が保存されない（警告） | matplotlib backend の問題 | `MPLBACKEND=Agg` を export |

## ディレクトリ構成

```
outputs/phase-01/
├── README.md
├── requirements.txt
├── src/
│   └── gripperforge_poc/
│       ├── __init__.py
│       ├── topopt.py        # SIMP + OC 最適化ループ（~180 行）
│       ├── objectives.py    # compliance / compliant_mechanism 目的関数
│       ├── filters.py       # 密度・感度フィルタ（疎行列実装）
│       ├── cases.py         # mbb / cylinder / box / lshape
│       └── cli.py
├── tests/
│   ├── conftest.py
│   ├── test_topopt.py
│   ├── test_objectives.py
│   └── test_cases.py
├── results/
│   ├── mbb_density.png / mbb_history.csv / mbb_topology.npy
│   ├── cylinder_*
│   ├── box_*
│   └── lshape_*
└── reports/
    ├── algorithm-notes.md       # 数式整理
    └── physical-validation.md   # 3Dプリント検証プロトコル
```

## 参考

- Andreassen et al. (2011), *Efficient topology optimization in MATLAB using 88 lines of code*
- Sigmund (1997), *On the design of compliant mechanisms using topology optimization*
- Bendsøe & Sigmund (2003), *Topology Optimization: Theory, Methods, and Applications*
