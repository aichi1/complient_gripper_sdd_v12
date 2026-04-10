# Algorithm Notes — SIMP + OC + Compliant Mechanism Objective

本文書は Phase 1 PoC で実装したトポロジー最適化アルゴリズムの数式ベースの整理。
Sigmund (2011) の 88-line code を骨組みとして、**mutual mean compliance 最大化**
の定式化で **コンプライアントメカニズム** 設計に対応させる。

---

## 1. 記号

| 記号 | 意味 |
|---|---|
| $\Omega$ | 設計領域 |
| $\mathbf{x} \in [0,1]^{n_e}$ | 設計変数（各要素の密度） |
| $\mathbf{\tilde x}$ | フィルタ適用後の物理密度 |
| $p$ | SIMP ペナルティ指数（既定 3.0） |
| $E_0$ | 固相材料のヤング率 |
| $E_{\min}$ | 空隙要素の数値安定化用ヤング率（$10^{-9}$） |
| $\mathbf{K}$ | 全体剛性行列 |
| $\mathbf{k}_e$ | 要素剛性行列（単位ヤング率） |
| $\mathbf{F}_\text{in}$ | 実荷重ベクトル（入力点に作用） |
| $\mathbf{L}_\text{out}$ | 出力点ダミー単位荷重（出力方向） |
| $\mathbf{u}_\text{in}$ | 実荷重に対する変位解 |
| $\mathbf{u}_\text{out}$ | 随伴変位解（ダミー荷重に対する解） |
| $V_f$ | 体積分率制約 |
| $r_\text{min}$ | フィルタ半径 |

## 2. SIMP 材料補間

$$
E_e(\tilde x_e) = E_{\min} + \tilde x_e^p \, (E_0 - E_{\min})
$$

要素剛性行列は

$$
\mathbf{K}_e(\tilde x_e) = E_e(\tilde x_e) \, \mathbf{k}_e
$$

### 要素剛性行列 $\mathbf{k}_e$（平面応力、4 節点 Q4、単位要素サイズ）

$$
\mathbf{k}_e = \frac{1}{1-\nu^2}
\begin{bmatrix}
A_{11} & \dots \\
\vdots & \ddots
\end{bmatrix}
$$

ここで解析解は Sigmund 88-line コードの `lk()` 関数と同一。実装では
`topopt.py::element_stiffness_matrix(E=1.0, nu=0.3)` が返す。

## 3. 目的関数

### 3.1 剛性最大化（Compliance Minimization, 比較用）

$$
\min_{\mathbf{x}} \; c(\mathbf{x}) = \mathbf{u}^T \mathbf{K} \mathbf{u} = \sum_e E_e \, \mathbf{u}_e^T \mathbf{k}_e \mathbf{u}_e
$$

感度：

$$
\frac{\partial c}{\partial x_e}
= -p\,(E_0 - E_{\min})\,\tilde x_e^{p-1}\,\mathbf{u}_e^T \mathbf{k}_e \mathbf{u}_e
$$

### 3.2 コンプライアントメカニズム（Mutual Mean Compliance 最大化）

コンプライアントメカニズムは、入力荷重 $F_\text{in}$ に対して **指定の出力点** が
**指定の方向** に大きく変位するような構造を設計する問題。

目的関数は **mutual mean compliance** = $\mathbf{L}_\text{out}^T \mathbf{u}_\text{in}$
を **最大化**。

$$
\max_{\mathbf{x}} \; g(\mathbf{x})
= \mathbf{L}_\text{out}^T \mathbf{u}_\text{in}
$$

最小化問題に直すため $-g$ を最小化する。

### 3.2.1 なぜ 2 荷重ケースが必要か

$g = \mathbf{L}_\text{out}^T \mathbf{u}_\text{in}$ の感度は随伴法で

$$
\frac{\partial g}{\partial x_e}
= -\,\boldsymbol{\lambda}^T \frac{\partial \mathbf{K}}{\partial x_e}\,\mathbf{u}_\text{in}
$$

ここで随伴変数 $\boldsymbol{\lambda}$ は

$$
\mathbf{K}\,\boldsymbol{\lambda} = \mathbf{L}_\text{out}
$$

を解けば得られる。つまり **実荷重 $F_\text{in}$ と出力点ダミー荷重 $L_\text{out}$ の
2 ケースを解く必要がある**。

$\boldsymbol{\lambda} \equiv \mathbf{u}_\text{out}$ と書けば感度は要素ごとに

$$
\frac{\partial g}{\partial x_e}
= -\,p\,(E_0 - E_{\min})\,\tilde x_e^{p-1}\,(\mathbf{u}_\text{out})_e^T \mathbf{k}_e (\mathbf{u}_\text{in})_e
$$

### 3.2.2 符号に注意

SIMP コンプライアンス最小化と同じ形だが **2 つの異なる変位ベクトルの積** が現れる点が要。
実装で `u_in`, `u_out` を混同すると勾配符号が逆になり最適化が発散する。
単体テスト（`test_objectives.py`）で有限差分勾配と比較することで防ぐ。

## 4. OC (Optimality Criteria) 更新

体積制約付き最小化問題

$$
\min_{\mathbf{x}}\; f(\mathbf{x}) \quad \text{s.t.}\quad \sum_e v_e x_e \le V_f \sum_e v_e,\; 0 \le x_e \le 1
$$

に対して Bendsøe の OC 更新則：

$$
x_e^{k+1} =
\begin{cases}
\max(0, x_e^k - m), & x_e^k B_e^\eta \le \max(0, x_e^k - m) \\
\min(1, x_e^k + m), & x_e^k B_e^\eta \ge \min(1, x_e^k + m) \\
x_e^k B_e^\eta, & \text{otherwise}
\end{cases}
$$

ここで $B_e = -\dfrac{\partial f/\partial x_e}{\lambda\,\partial V/\partial x_e}$、
$\eta = 1/2$（damping）、$m = 0.2$（move limit）。

$\lambda$ は体積制約を厳密に満たすよう **bisection** で求める。

## 5. フィルタ

### 5.1 感度フィルタ（Sigmund 1997）

$$
\widehat{\frac{\partial f}{\partial x_e}}
= \frac{1}{x_e\,\sum_{i \in N_e} H_{ei}}
\sum_{i \in N_e} H_{ei}\,x_i\,\frac{\partial f}{\partial x_i}
$$

### 5.2 密度フィルタ（Bruns & Tortorelli 2001）

$$
\tilde x_e = \frac{\sum_{i \in N_e} H_{ei}\,x_i}{\sum_{i \in N_e} H_{ei}},\quad
H_{ei} = \max(0, r_\text{min} - \Delta_{ei})
$$

チェッカーボード抑制と最小長さスケール制御の両方に効く。
Phase 1 では両方を実装、CLI オプション `--filter {sensitivity,density}` で選択。

## 6. 境界条件（コンプライアント把持ケース）

Phase 1 ではワークごとに boundary condition function を `cases.py` に定義。

| ケース | 入力点 | 入力荷重方向 | 出力点 | 出力方向 | 固定点 |
|---|---|---|---|---|---|
| mbb | 左上端 | -y | — | — | 左辺対称 + 右下点 |
| cylinder | 左辺中央 | +x | 右辺中央 | -x | 上下辺ピン |
| box | 左辺中央 | +x | 右辺中央 | -x | 上下辺ピン |
| lshape | L の内角 | +x | L の先端 | -y | L の上端固定 |

mbb は Sigmund 88-line コードとの **一致確認用**。残り 3 ケースが **把持動作** 用。

## 7. 収束判定とパラメータ

- `maxloop = 200`
- 収束：$\max_e |x_e^{k+1} - x_e^k| < 0.01$
- `penal = 3.0` 固定スタート（3.5 まで段階増加は Phase 2）
- `volfrac = 0.4` 標準
- `rmin = 1.5` 標準
- 初期密度 = `volfrac`（均一）

## 8. 実装上のポイント

1. **K 組立**：疎行列 COO で IKL/JKL を事前計算、反復ごとに値だけ更新
2. **境界条件**：`fixed_dofs` を除いた `free_dofs` 上でのみ線形系を解く
3. **感度 $\mathbf{u}_e^T \mathbf{k}_e \mathbf{u}_e$**：全要素を一括ベクトル化 (`ce = (U[edofMat] @ ke * U[edofMat]).sum(1)`)
4. **フィルタ**：距離依存のスパース行列 H と、$\sum_j H_{ij}$ を事前計算
5. **OC 更新**：bisection は対数スケールで 50 回以内に収束

## 9. 参考文献

- Sigmund, O. (2011). "Morphology-based black and white filters for topology optimization." Struct Multidisc Optim 33:401-424.
- Andreassen et al. (2011). "Efficient topology optimization in MATLAB using 88 lines of code." Struct Multidisc Optim 43:1-16.
- Sigmund, O. (1997). "On the design of compliant mechanisms using topology optimization." Mech Struct Mach 25(4):493-524.
- Bendsøe, M. P. & Sigmund, O. (2003). *Topology Optimization: Theory, Methods, and Applications*. Springer.
