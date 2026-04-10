# GripperForge — チーム編成と専門家エージェント

## task_type
`small_implementation`

## 分類理由
本プロジェクトの中核成果物は次の実装・検証物で構成される：
- Python によるトポロジー最適化エンジン（Phase 1, 2）
- React + FastAPI による Web UI パイプライン（Phase 3）
- 物理実験レポート（Phase 4）
- 発信コンテンツと顧客アプローチ計画（Phase 5）

調査・提案ではなく「動くものを作って検証し、公開する」流れが支配的なため、`small_implementation` に分類する。ただし、トポロジー最適化・弾性力学・3Dプリンティングの **ドメイン知見** が設計品質を大きく左右するため、標準セットに加えて `domain_sme` を常駐レビュワーとして召喚する。

## 汎用エージェント（常駐）
| エージェント | 役割 | 使用タイミング |
|---|---|---|
| `sdd-planner` | 計画立案・WBS・フェーズ調整 | `/init-task`, `/re-init-task` |
| `sdd-builder` | 成果物生成 | 各 Phase の Builder 工程 |
| `sdd-validator` | 仕様・品質検証 | 各 Phase の Validator 工程 |
| `sdd-researcher` | 過去知見の探索・再利用提案 | `/init-task` 冒頭、`/re-init-task` 前 |

## 専門家エージェント（召喚対象）

### 標準 `small_implementation` セット
| エージェント | 主たる責務 | 呼び出しタイミング |
|---|---|---|
| `sdd-software-architect` | モジュール分割・依存整理・拡張性レビュー | Phase 1 Step 2–4、Phase 2 Step 3–5、Phase 3 Step 2–4 |
| `sdd-qa-test-engineer` | テスト観点、正常系／異常系設計、再現性担保 | 全 Phase の Step 6（テスト作成時） |
| `sdd-security-reviewer` | 入力バリデーション、秘密情報の取り扱い、Web API のセキュリティ | Phase 1 Step 5（エラーハンドリング後）、Phase 3 Step 5（バックエンド API レビュー） |
| `sdd-doc-editor` | README・手順書の情報設計と読みやすさ | 全 Phase の Step 8（README 作成時）、Phase 5 の技術記事レビュー |

### GripperForge 追加セット
| エージェント | 主たる責務 | 呼び出しタイミング |
|---|---|---|
| `sdd-domain-sme` | トポロジー最適化の数理的妥当性、コンプライアントメカニズムの物理的前提、有限要素定式化の検証 | Phase 1 Step 4（コアロジック実装後）、Phase 2 Step 4（フィルタ・境界条件レビュー）、Phase 4 Step 3（実測と理論の突合せ） |

## 呼び出しポリシー
- 各 Phase の Builder は、SKILL.md に記載された呼び出しタイミングで該当エージェントにレビューを依頼する
- 専門家のレビューは「指摘事項のうち High/Med を Builder が取り込む。Low は次フェーズ以降で対応可」とする
- Validator は Builder 成果物 + 専門家レビュー結果の両方を参照して検証する

## 新規エージェント召喚手順
本プロジェクト開始時、`/init-task` が以下を `.claude/agents/generated/` に配置する：
- `sdd-software-architect.md`
- `sdd-qa-test-engineer.md`
- `sdd-security-reviewer.md`
- `sdd-doc-editor.md`
- `sdd-domain-sme.md`

既に同名エージェントが `.claude/agents/` に存在する場合は上書きせず、生成物は `.claude/agents/generated/` に置く（読み込み優先度は generated が高い）。
