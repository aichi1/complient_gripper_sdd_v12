# GripperForge — 実施計画（Phase 構成）

プロジェクト Kickoff 文書（`project_init.md`）の Phase 0〜4 を、SDD ワークフローの Phase 1〜5 に 1:1 対応させる。

## Phase 構成一覧

| SDD Phase | 元 Roadmap | フェーズ名 | 主要成果物 | 想定期間 |
|:---:|:---:|---|---|:---:|
| 1 | Phase 0 | 技術検証 PoC | `outputs/phase-01/` 配下に Python 実装（SIMP 88 行版の再実装 + コンプライアント対応）、テストケース、3Dプリント検証レポート | 2〜3 週間 |
| 2 | Phase 1 | コア最適化エンジン | `outputs/phase-02/` に実用 2D SIMP エンジン（フィルタ・境界条件・STL 出力）、複数ワーク検証 | 4〜6 週間 |
| 3 | Phase 2 | 最小限 Web UI | `outputs/phase-03/` に React フロント + FastAPI バックエンド、非同期ジョブキュー、履歴閲覧 | 3〜4 週間 |
| 4 | Phase 3 | 実ワーク検証と事例構築 | `outputs/phase-04/` に 3〜5 実ワーク検証レポート、汎用ジョー比較データ、事例集 | 4〜6 週間 |
| 5 | Phase 4 | 公開と初期顧客獲得 | `outputs/phase-05/` に Zenn 記事ドラフト、デモ動画スクリプト、OSS リポジトリ README、顧客アプローチ計画 | 2〜3 週間 |

## 進め方

### 実行ルール
- 各フェーズは SDD Builder / Validator プロトコル（`.claude/rules/builder-validator.md`）に従う
- フェーズ間は前後関係があり、Phase N は Phase N-1 の成果物に依存する
- 物理検証（3Dプリント・把持テスト）は外部作業となるため、フェーズ内では「実行手順書 + 結果記録テンプレート + 実測データレポート」の 3 点セットで成果物化する
- Go/No-Go 判定点：Phase 1 完了時に技術フィージビリティを確認し、継続判断する

### フェーズ間依存関係
```
Phase 1 (PoC)
   │ 最適化アルゴリズムの妥当性検証 → エンジン仕様の確定
   ▼
Phase 2 (Core Engine)
   │ エンジン API → UI からの呼び出し I/F 確定
   ▼
Phase 3 (Web UI)
   │ 実運用可能パイプライン → 実ワーク投入
   ▼
Phase 4 (Real-world Validation)
   │ 事例集・定量データ → 発信コンテンツ
   ▼
Phase 5 (Publication & Outreach)
```

### コマンド例
```bash
# Phase 1 のみ実行
/run-phase 1

# Phase 1〜2 を連続実行（スマートモード）
/run-phase 1-2

# 全フェーズを一括実行
/run-phase all

# 仕様を追記・修正したいとき
/update-docs
```

## 成果物フォーマット規約

各フェーズの `outputs/phase-{N}/` には以下を含める：
- `README.md` — フェーズ成果物のサマリと実行手順
- `src/` または `docs/`（該当する場合） — 実コード / 設計文書 / 検証レポート
- `tests/`（該当する場合） — 自動テスト
- `.metadata.json` — Builder/Validator メタデータ
- `.validation/report.md` — Validator による検証レポート（自動生成）

詳細は各フェーズの `skills/phase-{N}/SKILL.md` を参照。

## マイルストーンとリスク対応

| フェーズ | 主なリスク | 早期警戒サイン | 対応 |
|---|---|---|---|
| 1 | SIMP 収束しない／チェッカーボード発生 | イテレーションで目的関数が振動、密度が 0/1 に二値化しない | フィルタ半径・ペナルティ指数を調整、ラウンド2 で Heaviside projection を前倒し導入 |
| 2 | 複雑形状で局所最適に陥る | 入力形状で出力が毎回異なる | 初期密度分布の改善、多スタート最適化の導入 |
| 3 | 計算時間が UX を損なう | 1 ジョブ 10 分以上 | 非同期ジョブキュー、低解像度プレビュー → 高解像度最終実行の段階化 |
| 4 | 実ワークで把持できない | 把持テストで失敗多発 | 接触面の摩擦係数・弾性率を再調整、メッシュ解像度を上げる |
| 5 | 顧客の反応が薄い | 接触 5 社で全て様子見 | 無償試作オファーを強化、展示会デモに切替 |
