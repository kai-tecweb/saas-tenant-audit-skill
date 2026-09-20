# 既存の公開スキル・規格の調査

> [English](comparison.md) · **日本語**

2026-09-20 時点で、公開されているリポジトリの説明とドキュメントから調べました。**網羅的ではなく**、
多くは構成を確認した程度で全文は読んでいません。ライセンス・規模・機能は変わっている可能性があるため、
各リンク先で確認してください。ここに載せることは批判ではなく、このスキルの立ち位置を示すためのものです。

## 確認した公開スキル・エージェントプロンプト

| プロジェクト | 概要 | 方式 | このスキルとの関係 |
|---|---|---|---|
| [anthropics/claude-code-security-review](https://github.com/anthropics/claude-code-security-review)（MIT） | `/security-review` コマンドとGitHub Action | 差分ベースのコードレビュー | 確信度による絞り込みと誤検知除外リスト。アプリを実行しない |
| [trailofbits/skills](https://github.com/trailofbits/skills)（CC-BY-SA-4.0） | 静的解析・バリアント分析・安全でない既定値など多数のプラグイン | コードレビュー＋ツール | マルチテナントWebアプリの認可スキルは確認できず |
| [agamm/claude-code-owasp](https://github.com/agamm/claude-code-owasp)（MIT） | 言語別リファレンス付きのOWASP知識ベース | コードレビュー | 段階的開示が良い。テスト手順ではなく知識ベース |
| [afiqiqmal/claude-security-audit](https://github.com/afiqiqmal/claude-security-audit) | 大規模チェックリスト。Laravel/Next.js検出、SaaSマルチテナント用パック、グレーボックスモード | 主にチェックリスト/コード | 範囲は最も近い。ライセンス未確認。説明には2テナントのブラックボックス手順や教訓集は見当たらず |
| [AgriciDaniel/claude-cybersecurity](https://github.com/AgriciDaniel/claude-cybersecurity)（MIT） | 採点ルーブリック付きの大規模マルチエージェント・コードレビュー | コードレビュー | Laravel/Next.jsは明示されず |
| [netresearch/security-audit-skill](https://github.com/netresearch/security-audit-skill) | スクリプト中心のPHP向け監査（CWE・CVSS） | コード＋スクリプト | PHP/TYPO3中心 |
| [sickn33 laravel-security-audit](https://github.com/sickn33/agentic-awesome-skills/blob/main/skills/laravel-security-audit/SKILL.md) | 1ファイルのLaravelチェックリスト（IDOR・マスアサインメント・ポリシー） | ホワイトボックス | 実行時の検証なし、Next.jsなし |
| [VicKayro/claude-security-audit](https://github.com/VicKayro/claude-security-audit)（MIT） | 1コマンドファイル（フランス語） | コードレビュー | 最初に環境を確認する |
| [McGo/claude-code-security-audit](https://github.com/McGo/claude-code-security-audit)（MIT） | 数値スコアと出力言語切替（`lang=de`）付き | コードレビュー | 説明にはIDOR/マルチテナントの扱いは見当たらず |
| [toshipon/claude-code-security-audit-skill](https://zenn.dev/toshipon/articles/claude-code-security-audit-skill) | 日本語。24の参照文書・8フェーズ。Next.js/Supabase向け | 静的＋ブラウザ | 「証拠優先」の規則と「誤った合理化を退ける」節。対象はSupabaseでLaravelではない |
| [mukul975/Anthropic-Cybersecurity-Skills](https://github.com/mukul975/Anthropic-Cybersecurity-Skills)（Apache-2.0） | API BOLA/IDORテストを含む多数のセキュリティスキル | 各種 | 複数アカウントでのテスト。クリーンアップや2テナントの衛生面の指針は見当たらず |
| [Orizon-eu/claude-code-pentest](https://github.com/Orizon-eu/claude-code-pentest)（MIT） | ブラックボックスのペンテスト用スキル/スクリプト、CVSS再計算 | ブラックボックス | 汎用でテナント特化ではない |

## このスキルが参考にした規格・チェックリスト

- OWASP Top 10（2021。2025年版があり一部カテゴリの番号が変わるため、スキルは番号でなく**カテゴリ名**で対応付け）、
  OWASP API Security Top 10（2023）、CWE、任意でCVSS。
- OWASP Authorization Regression Testing Cheat Sheet（アクター・リソース・操作のマトリクス、403/404の一貫性）、
  OWASP Multi-Tenant Security Cheat Sheet（テナントは認証情報から決める、キャッシュ・レート制限のキーにテナントを含める、
  キューのコンシューマでテナント文脈を再確立）。
- OWASP Laravel Cheat Sheet、Next.jsのセキュリティ指針（データアクセス層、Server Actionsは公開エンドポイント）、
  広く公表されたNext.jsのミドルウェア迂回の脆弱性情報。
- Claude Codeのスキル作成指針: 最小限のフロントマター、短い `SKILL.md`、1階層の `references/`、
  長い文書の目次、決定的な処理はスクリプト化。

## このスキルの違い

1. **第二テナントのブラックボックス手順**: 被害側データの前後スナップショット、拒否の規約、存在オラクルの比較、
   データに隠れたID。コードのチェックリストではなく、実際に試す手順です。
2. **実戦の教訓（FL-01 … FL-35）**: 監査の**進め方と検証スクリプト**に関する教訓。他では見つけられませんでした。
3. **Laravel + Next.js のマルチテナントSaaS**固有の注意点を1か所に集約。
4. **日英2言語**を同一の手順で作成し、同期を保つ。

古い情報や誤りがあれば教えてください: X（旧Twitter） https://x.com/iwasaki_dev40
