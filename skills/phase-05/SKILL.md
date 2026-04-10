# Phase 5: 公開と初期顧客獲得

> カテゴリ：`small_implementation`（成果物は発信コンテンツ + 顧客計画）
> 元 Roadmap：Phase 4 公開と初期顧客獲得
> 前提：Phase 4 完了（実ワーク検証で 5 中 4 以上成功、または達成度が報告済み）

## Objective
Phase 4 までに構築した技術・事例を外部に発信し、初期顧客獲得の動線を作る。技術記事、デモ動画、OSS リポジトリ公開、顧客アプローチの 4 本柱で構成する。

**成功指標**：
- 有償トライアルに進む意思を示す企業 **2 社以上**
- 公開記事への反応（Zenn Trending、GitHub Star、問い合わせ数）

## Input Requirements
- `outputs/phase-04/summary-report.md`（定量データ）
- `outputs/phase-04/cases/` の事例集
- `outputs/phase-02/src/gripperforge_engine/`（OSS 公開対象）
- `docs/requirements.md`（MVP 全体の成功条件）

## Output Specification
成果物ディレクトリ：`outputs/phase-05/`

### 必須ファイル構成
```
outputs/phase-05/
├── README.md                           # 発信活動全体ナビ + 進捗ダッシュボード
├── articles/
│   ├── zenn-draft.md                   # Zenn 記事ドラフト
│   ├── zenn-cover-image.md             # カバー画像の仕様
│   └── english-draft.md                # 英語版ドラフト（任意）
├── demo_video/
│   ├── script.md                       # 台本
│   ├── storyboard.md                   # カット割り
│   ├── assets-checklist.md             # 必要素材リスト
│   └── final-video-link.md             # 公開 URL を後で追記
├── oss/
│   ├── README.md                       # OSS 公開用 README 案
│   ├── LICENSE-decision.md             # ライセンス選定根拠
│   ├── CONTRIBUTING.md                 # 貢献ガイド
│   ├── CODE_OF_CONDUCT.md              # 行動規範
│   └── publish-checklist.md            # 公開前チェック
├── outreach/
│   ├── target-list.md                  # アプローチ先企業一覧（匿名可）
│   ├── message-templates.md            # コールドメッセージ雛形（LinkedIn/メール）
│   ├── pitch-deck-outline.md           # ピッチ資料アウトライン
│   ├── followup-playbook.md            # 返信への対応手順
│   └── tracking.csv                    # アプローチ進捗管理
├── metrics/
│   ├── publication-metrics.md          # 公開後の指標計測方法
│   └── kpi-dashboard-spec.md           # KPI 定義
└── reports/
    └── launch-retrospective.md         # 公開後の振り返り（リリース後に記載）
```

### `articles/zenn-draft.md` の必須セクション
1. **タイトル案**（3 案以上）
2. **リード文**（共感フック → 課題 → 解決アプローチ）
3. **背景**：多品種少量生産でのグリッパー設計ボトルネック
4. **技術解説**：コンプライアントメカニズム + トポロジー最適化 SIMP 法
5. **実装の要点**：目的関数、フィルタ、Heaviside projection
6. **実ワーク事例**（Phase 4 から 2〜3 事例）
7. **定量データ**（成功率、コスト、リードタイム）
8. **限界と今後**
9. **OSS リポジトリへのリンク**
10. **問い合わせ導線**

### `demo_video/script.md` の必須セクション
1. **全体尺** — 3 分を目安
2. **シーン構成** — 0:00〜0:15 課題、0:15〜0:45 デモ（UI 操作）、0:45〜1:30 3Dプリント、1:30〜2:30 把持テスト、2:30〜3:00 締め
3. **ナレーション原稿**
4. **必要な撮影シーン一覧**

### `oss/README.md` の必須セクション
1. Badge（License, Python version, CI）
2. 概要
3. デモ GIF / 動画リンク
4. インストール
5. Quick Start
6. ドキュメント構成
7. 限界と注意事項
8. コントリビューション
9. ライセンス
10. Citation（論文引用する場合の書式）

### `outreach/target-list.md` 最低要件
- 最低 10 社（匿名可）、業種別に分類
- 各社について：業種、想定担当者役職、アプローチチャネル、関連性メモ

## Quality Criteria
- [ ] `zenn-draft.md` が全必須セクションを埋め、公開可能な品質（誤字・事実誤認なし）
- [ ] `demo_video/script.md` の台本が時間配分・ナレーション・必要素材まで具体化されている
- [ ] `oss/README.md` が OSS 公開慣習に従っている（badge, quick start, contribution）
- [ ] `oss/LICENSE-decision.md` で MIT/Apache 2.0 等のライセンスが選定済み、選定根拠が明記
- [ ] `outreach/target-list.md` に 10 社以上のアプローチ対象がある
- [ ] `outreach/message-templates.md` に LinkedIn/メール 2 種類以上の雛形がある
- [ ] `outreach/tracking.csv` に少なくとも 3 社のアプローチ実績が記録されている（実施後）
- [ ] `metrics/` で公開後の KPI と計測方法が定義されている
- [ ] 公開物に顧客機密情報が含まれていないことを確認済み（`launch-retrospective.md` に記載）
- [ ] `launch-retrospective.md` で MVP 全体の成功条件達成度が評価されている

## Procedure

### Step 1: 素材整理と発信ストーリーの設計
1. Phase 4 の事例・写真・動画素材を棚卸し
2. 発信ストーリーの骨子を書く（誰に、何を、なぜ伝えるか）
3. `articles/zenn-draft.md` の骨組みとタイトル案

### Step 2: 技術記事執筆
1. `zenn-draft.md` を必須セクションに沿って執筆
2. コードスニペット・図表を Phase 1–4 から引用
3. 実ワーク事例は 2〜3 に絞る（全部入れると長くなりすぎる）

**→ `sdd-doc-editor` に記事の構成・読みやすさ・フック力をレビュー依頼**
**→ `sdd-domain-sme` に技術記述の正確性レビューを依頼**

### Step 3: デモ動画設計
1. `script.md` と `storyboard.md` を書く
2. 既存素材で撮れるカットと新規撮影カットを区別
3. `assets-checklist.md` で必要素材を一覧化

### Step 4: OSS 公開準備
1. `oss/LICENSE-decision.md` — MIT / Apache 2.0 を比較、選定
2. `oss/README.md` を書く（OSS 用に新規）— Phase 2 の README を流用しつつ外部向けに再構成
3. `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md` を作成
4. `publish-checklist.md` — 公開前に実施すべき項目（秘密情報スキャン、Git 履歴レビュー、ライセンスヘッダ）

**→ `sdd-security-reviewer` に OSS 公開物の機密チェックを依頼（.env、顧客データ、個人情報）**
**→ `sdd-software-architect` に OSS README の技術説明の整合性レビューを依頼**

### Step 5: 顧客アプローチ計画
1. `target-list.md` — 製造業ネットワーク由来を含む 10 社以上
2. `message-templates.md` — LinkedIn DM、コールドメール、展示会での声かけテンプレ
3. `pitch-deck-outline.md` — 10 スライド構成
4. `followup-playbook.md` — 返信パターンへの対応
5. `tracking.csv` の初期フォーマットを作成

### Step 6: 公開実施（任意、スコープ外の場合は計画のみ）
1. Zenn 記事投稿
2. デモ動画撮影・編集・公開
3. GitHub で OSS リポジトリ公開
4. 顧客 3 社以上へアプローチ開始
5. `tracking.csv` に結果を記録

### Step 7: 振り返りと MVP 判定
1. `launch-retrospective.md` を書く：
   - Zenn 反応（Views, Likes, Trending 入り有無）
   - GitHub Star 数、Issue/PR
   - 顧客アプローチ結果（返信率、商談数）
   - MVP 成功条件の達成度
2. 次フェーズ（製品化 or ピボット）への提言

**→ `sdd-doc-editor` に最終レビューを依頼**

### Step 8: .metadata.json 作成

## Common Pitfalls
- **記事が長すぎる** → Zenn は 5000 字前後が読まれやすい。冗長な技術詳細は外部リンクへ
- **動画の尺が長い** → 初回は 3 分以内。長尺版は Phase 5 外でよい
- **OSS の LICENSE を後回し** → リポジトリ公開前に必ず確定
- **Git 履歴に顧客データが残っている** → `git filter-repo` で除去するか、新規リポジトリを切る
- **顧客アプローチが売り込み色すぎる** → 「無償試作提案」を前面に出す
- **公開後の計測をしない** → KPI を先に定義し、週次でトラッキング
- **展示会頼み** → 展示会依存度を下げ、オンライン流入の動線も整える
- **機密情報を記事に混入** → 公開前の機密レビューは必須

## Troubleshooting
| 症状 | 原因 | 対処法 |
|---|---|---|
| Zenn 記事の反応が薄い | フックが弱い | タイトル・リード文を A/B、SNS で再拡散 |
| GitHub Star が伸びない | Readability が低い | README にデモ GIF を追加、quick start を簡略化 |
| 返信率が低い | メッセージが一般的すぎる | 相手企業の具体ワークを調べ、カスタム一文を入れる |
| 問い合わせに対応できない | 窓口未整備 | 連絡先・FAQ をリポジトリに明示 |

## Examples

### LinkedIn DM テンプレ例
```
{相手名} 様

初めまして、GripperForge の {自分} と申します。
ロボットのグリッパー設計を、ワークの CAD データから数時間で自動化する技術を開発しています。
多品種少量の{業種}で毎回ジョー設計に時間がかかる課題がある場合、
無償で 1〜3 品種分の最適フィンガーを設計・3Dプリント試作します。

事例: {Zenn 記事 URL}
デモ動画: {動画 URL}

15 分ほどお時間いただけますと幸いです。
```

### `launch-retrospective.md` アウトライン
```markdown
# MVP 公開振り返り

## KPI 達成状況
- [ ] Zenn 記事公開 ✓ / Views: ___, Likes: ___
- [ ] デモ動画公開 ✓ / 再生: ___
- [ ] OSS リポジトリ公開 ✓ / Star: ___, Issue: ___
- [ ] 顧客アプローチ: ___ 社実施, 返信: ___ 社, 有償トライアル意欲: ___ 社

## MVP 全体成功条件達成度
- 実ワーク 5 中 4 以上成功: __
- CAD → STL の Web UI パイプライン: __
- 有償トライアル 2 社以上: __

## 学び
- Keep:
- Problem:
- Try:
```
