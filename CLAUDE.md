# GripperForge — コンプライアントメカニズムによるグリッパーフィンガー自動設計サービス

## Metadata
- **Category**: small_implementation
- **Start Date**: 2026-04-10
- **Estimated Duration**: 約 5 ヶ月（MVP 公開まで）
- **Phase Count**: 5
- **Source Document**: `project_init.md`
- **task_type**: small_implementation（+ domain_sme 追加）

## Objective
ワークの CAD／断面形状データをアップロードするだけで、トポロジー最適化（SIMP 法 + コンプライアントメカニズム定式化）によって最適なグリッパーフィンガーを自動設計し、3Dプリント試作からゴム型量産までを貫く MVP を構築する。多品種少量生産の工業部品（初期フォーカス：自動車部品 Tier2〜3）向けに、リードタイムを数週間→数時間、コストを数十万円→数千円に短縮することを目指す。

## Deliverables
| Phase | Deliverable | Format | 想定期間 |
|:---:|---|---|:---:|
| 1 | **技術検証 PoC** — Sigmund 88 行コード Python 再実装 + コンプライアントメカニズム目的関数 + 3Dプリント物理検証レポート | Python パッケージ + 実験レポート | 2〜3 週間 |
| 2 | **コア最適化エンジン** — 実用 2D SIMP エンジン（フィルタ・境界条件・STL 出力）+ 5 ケース検証 | Python パッケージ + ベンチマーク | 4〜6 週間 |
| 3 | **最小限 Web UI** — React フロント + FastAPI バックエンド + 非同期ジョブキュー | Web アプリ | 3〜4 週間 |
| 4 | **実ワーク検証と事例構築** — 3〜5 実ワーク検証 + 汎用ジョー比較 + 事例集 | 実験レポート集 | 4〜6 週間 |
| 5 | **公開と初期顧客獲得** — Zenn 記事 + デモ動画 + OSS リポジトリ + 顧客アプローチ計画 | 発信コンテンツ + 営業計画 | 2〜3 週間 |

## Specification Files
- `docs/requirements.md` — 目的、スコープ、非目的、制約、成功条件
- `docs/plan.md` — Phase 構成、依存関係、進め方、マイルストーンとリスク
- `docs/team.md` — チーム編成と専門家エージェントの呼び出しポリシー
- `docs/tech-stack.md` — 言語・フレームワーク・依存ライブラリ
- `docs/io-spec.md` — 各フェーズの入出力仕様
- `docs/constraints.md` — 技術的・ビジネス的・物理的制約
- `docs/_manifest.json` — 必須ファイル一覧（hooks 用）

## Skills Structure
- `skills/phase-01/SKILL.md` — 技術検証 PoC（Sigmund 88 行の Python 再実装 + コンプライアント対応）
- `skills/phase-02/SKILL.md` — コア最適化エンジン（実用 2D SIMP + STL 出力）
- `skills/phase-03/SKILL.md` — 最小限 Web UI（React + FastAPI）
- `skills/phase-04/SKILL.md` — 実ワーク検証と事例構築
- `skills/phase-05/SKILL.md` — 公開と初期顧客獲得

## Team
### 汎用エージェント
`sdd-planner` / `sdd-builder` / `sdd-validator` / `sdd-researcher`

### 専門家エージェント（`.claude/agents/generated/` に生成済み）
| エージェント | 主な役割 | 主な呼び出し Phase |
|---|---|---|
| `sdd-software-architect` | モジュール分割・依存整理・レイヤリング | 1, 2, 3, 5 |
| `sdd-qa-test-engineer` | テスト観点・異常系・再現性 | 1, 2, 3, 4 |
| `sdd-security-reviewer` | 入力検証・機密・OSS 公開前スキャン | 1, 3, 4, 5 |
| `sdd-doc-editor` | README・記事・レポートの情報設計 | 1, 2, 3, 4, 5 |
| `sdd-domain-sme` | トポロジー最適化・コンプライアントメカニズムの数理的妥当性 | 1, 2, 4 |

詳細は `docs/team.md` 参照。

## Next Steps
1. **`docs/` をレビュー**：特に `requirements.md`（成功条件）と `team.md`（専門家の呼び出しタイミング）を確認
2. **必要なら `/update-docs` で修正**：既存 `project_init.md` との差分確認、前提に齟齬があれば補正
3. **Phase 1 を開始**：`/run-phase 1` を実行
4. **複数 Phase を連続実行**：`/run-phase 1-2` または `/run-phase all`
5. **MVP 完成後の製品化フェーズを追加**：`/re-init-task` を実行し、Iteration 2 として拡張（例：実接触解析、ユーザー認証、課金、フル 3D 最適化など）
6. **完了時**：`/finalize` で `~/.sdd-knowledge/` に知見を蓄積、`/retrospective` で振り返り

## Assumptions Pending Confirmation
以下は `project_init.md` から推定した前提。Phase 1 着手前にユーザー確認推奨：
- 主要開発 OS は Linux / macOS（Windows は WSL 前提）
- 3Dプリンタは FDM/TPU 方式（SLA/MJF は外注バックアップ）
- 対象グリッパーボディは SMC MHZ2 系列相当の平行 2 爪
- OSS 公開時のライセンスは MIT または Apache 2.0（Phase 5 で確定）
- CI は MVP 段階では必須としない（Phase 5 以降で導入検討）

## Next Session Starter
```
Phase 1 の実装を開始。
/run-phase 1
```
- まず `docs/requirements.md` と `skills/phase-01/SKILL.md` を読み直す
- Builder → Validator サイクルで PoC を構築
- 3Dプリント物理検証は外部作業のため、手順書 + 結果記録テンプレート形式で成果物化する
