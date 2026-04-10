# Phase 4: 実ワーク検証と事例構築

> カテゴリ：`small_implementation`（ただし主要成果物は検証レポートと事例集）
> 元 Roadmap：Phase 3 実ワーク検証
> 前提：Phase 3 完了（Web UI から一気通貫で最適化 → STL 取得が動く）

## Objective
実際の工業部品 3〜5 種類を対象に、CAD アップロード → 最適化 → 3Dプリント → 把持テスト → 定量評価までの一連のワークフローを回し、「GripperForge が実用に値すること」を **定量データと事例** で証明する。既製品汎用ジョーとの比較を行い、優位性を数値で示す。

## Input Requirements
- `docs/requirements.md`（Phase 4 成功条件：5 実ワーク中 4 以上で既製品ジョー以上の把持安定性）
- `docs/plan.md`, `docs/io-spec.md`（Phase 4）, `docs/constraints.md`
- `outputs/phase-03/` の Web UI（最適化実行の経路）
- 実ワーク 3〜5 種類の CAD データ（外部調達） — 自動車部品 Tier2〜3 を優先
- 比較用の既製品汎用ジョー（物理）

## Output Specification
成果物ディレクトリ：`outputs/phase-04/`

### 必須ファイル構成
```
outputs/phase-04/
├── README.md                          # 検証全体のナビゲーション
├── case-selection.md                  # ケース選定の根拠
├── protocol.md                        # 実験プロトコル（再現可能な手順書）
├── cases/
│   ├── case-01-{workpiece_name}/
│   │   ├── input/
│   │   │   ├── workpiece.json         # GripperForge 入力
│   │   │   └── original_cad.*         # 元 CAD（公開不可なら placeholder）
│   │   ├── optimization/
│   │   │   ├── config.json
│   │   │   ├── density.png
│   │   │   └── finger.stl
│   │   ├── physical/
│   │   │   ├── print_log.md           # 印刷条件・時間・材料
│   │   │   └── photos/ or photos.md   # 写真一覧（実ファイル or 参照）
│   │   ├── test-result.md             # 把持成功率、保持力、位置精度
│   │   └── comparison.md              # 汎用ジョー vs GripperForge
│   ├── case-02-.../
│   ├── case-03-.../
│   ├── case-04-.../
│   └── case-05-.../
├── summary-report.md                  # 全ケース総括 + 判定
├── sim-vs-real.md                     # シミュレーション結果と実測の比較
└── appendix/
    ├── measurement-protocol.md        # 計測方法の詳細
    └── data-tables.csv                # 集計データ（定量）
```

### 各ケースの `test-result.md` 必須項目
- **ワーク仕様**：寸法、重量、材質、把持の難易度
- **印刷条件**：機種、フィラメント、充填率、印刷時間、コスト
- **把持テスト**：試行回数 (最低 10 回)、成功率、失敗モード
- **保持力**：装着後に追加可能な荷重（g）
- **位置決め精度**：目標位置からのずれ（mm）
- **写真・動画**：最低 2 枚の写真と 1 本の動画（リンク）
- **所見**：想定外の現象、改善候補

### `summary-report.md` 必須セクション
1. **目的と評価軸**
2. **ケース一覧**（表形式）
3. **定量結果サマリ** — 成功率、既製品比較、コスト、リードタイム
4. **5 中 4 以上成功したか** — Pass / Fail 判定
5. **シミュレーション vs 実測の相関分析**
6. **改善提案** — Phase 5 に持ち越す課題
7. **結論**

## Quality Criteria
- [ ] `protocol.md` に再現可能な実験手順が書かれている
- [ ] ケース数が 3〜5 で、全て `case-XX/test-result.md` が埋まっている
- [ ] 各ケースの把持テスト試行回数が 10 回以上
- [ ] 比較対象（既製品汎用ジョー）の定量データが取られている
- [ ] `summary-report.md` に 5 中 4 以上の成功判定またはその達成度が明記されている
- [ ] 写真／動画参照が各ケースに最低 2 枚 + 1 本ある（物理不可なら placeholder で記載）
- [ ] `sim-vs-real.md` でシミュレーション結果（変形予測、応力集中）と実測の比較がある
- [ ] `appendix/data-tables.csv` に機械可読な定量データがある
- [ ] 顧客機密（CAD データ、社名）が公開可能なものだけに限定されている

## Procedure

### Step 1: ケース選定
1. `case-selection.md` を作成
2. 選定基準：
   - 把持難易度（曲面あり、薄肉、非対称、傷不可）
   - CAD データ入手可能性
   - 自動車部品 Tier2〜3 を優先
   - 既製品ジョーで困難なワークを意図的に含める
3. 3〜5 ケースを選び、それぞれにワーク仕様サマリを書く

**→ `sdd-domain-sme` にケース選定の妥当性レビューを依頼（難易度分布、代表性、測定可能性）**

### Step 2: 実験プロトコル策定
1. `protocol.md` に手順を記述：
   - ワーク → `workpiece.json` への変換手順
   - 最適化パラメータの初期値
   - 印刷設定
   - 把持テストの試行方法、成功判定、荷重印加方法、位置計測
2. 安全上の注意（落下防止、TPU 劣化対策）

**→ `sdd-qa-test-engineer` にプロトコルの再現性・測定の客観性をレビューしてもらう**

### Step 3: 各ケースの実行
各ケースについて以下を繰り返す：
1. `workpiece.json` を作成し、Phase 3 の Web UI から実行
2. `optimization/` に結果を保存
3. STL を 3Dプリント（外部作業）、`physical/print_log.md` に記録
4. 把持テスト実施、`test-result.md` を埋める
5. 同じワークを既製品汎用ジョーで試し、`comparison.md` を作成

**→ Step 3 の実験記録整理後、`sdd-domain-sme` に実測と理論の突合せをレビュー依頼**

### Step 4: シミュレーション vs 実測分析
1. 各ケースの密度分布・予測変形と実機の挙動を比較
2. 差異の原因分類：
   - 境界条件の簡略化
   - 材料モデルの線形仮定
   - 印刷品質
   - 接触面の摩擦未考慮
3. `sim-vs-real.md` に表形式でまとめる

### Step 5: 総括レポート
1. `summary-report.md` を書く（Output Specification の構成）
2. 定量データを `appendix/data-tables.csv` に集約
3. 5 中 4 成功判定を明確に出す
4. 失敗ケースは原因と今後の改善方針を書く

**→ `sdd-doc-editor` に summary-report のストーリーラインと情報設計をレビュー依頼**

### Step 6: 事例の機密チェック
1. 顧客社名・CAD データの公開可否をチェック
2. 公開不可は placeholder / 匿名化

**→ `sdd-security-reviewer` に機密情報の混入チェックを依頼**

### Step 7: .metadata.json 作成

## Common Pitfalls
- **試行回数が少なすぎる** → 1〜2 回の成功は偶然。10 回以上で成功率を出す
- **定量データが主観的** — 「安定していた」ではなく「追加荷重 200 g まで保持」のような数値にする
- **失敗ケースを書かない／隠す** → 失敗からの学びこそ価値。原因分析とセットで公開
- **既製品ジョーとの比較を定性的に済ませる** → 同一条件で同一試行数を実施
- **顧客社名を `case-XX-{company}/` のディレクトリ名に入れてしまう** → 匿名化は最初から
- **シミュレーション vs 実測を書かない** → Phase 5 の発信素材として最重要
- **Web UI を Phase 3 で作ったのに手動実行に戻る** → 必ず UI 経由で実行し、ログも残す

## Troubleshooting
| 症状 | 原因 | 対処法 |
|---|---|---|
| 実ワークが用意できない | 顧客連携が間に合わない | 3Dプリントでワークモックを自作 |
| 3Dプリント品が割れる | TPU 硬度選定ミス | Shore 95A → 90A に変更 |
| シミュレーションと実測が大きく乖離 | 材料物性の線形仮定 | 実測値から E を逆算して再実行 |
| 把持成功判定が曖昧 | 判定基準の不統一 | `protocol.md` の判定ルールを改訂、既測定分を再評価 |

## Examples

### `test-result.md` のテンプレ
```markdown
# Case 01: Nylon Connector Housing (自動車部品)

## ワーク仕様
- 寸法：45 × 20 × 12 mm
- 重量：8 g
- 材質：PA66 + GF30
- 把持難易度：★★★（曲面 + 傷不可）

## 最適化設定
- nelx=120, nely=80, volfrac=0.35, penal=3.0, rmin=1.8
- 計算時間：2 分 14 秒

## 印刷条件
- 機種：Bambu Lab X1 Carbon
- フィラメント：TPU 95A
- 充填率：30%
- 印刷時間：1 時間 22 分
- コスト：約 450 円

## 把持テスト結果
- 試行回数：10
- 成功：9（90%）
- 失敗モード：薄肉部のスリップ 1 件
- 追加保持荷重：最大 250 g
- 位置決め精度：±0.4 mm

## 既製品比較
- 汎用平行ジョー（SMC MHL2-20D 標準爪）：10 回中 3 成功（30%）

## 所見
- 出力点方向の設定を調整すれば成功率 100% 見込み
```
