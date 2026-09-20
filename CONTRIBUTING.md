# Contributing / コントリビュート

**English.** Corrections, new field lessons and stack notes for other frameworks are
welcome. Please:
1. Keep lessons **generic**: no client, company, domain, IP, person or credential names —
   even in examples. Run `skills/saas-tenant-audit/scripts/leak_scan.sh --terms <your private terms file>`
   before opening a pull request (keep the terms file outside the repository).
2. Tag each lesson **[field]** (you actually hit it) or **[std]** (standard practice).
3. Change both languages together (`saas-tenant-audit` and `saas-tenant-audit-ja`) and keep
   the same file names, headings and FL ids. If you cannot write Japanese, say so in the
   pull request and the maintainer will help.
4. New lessons get the next free `FL-nn` id and a row in the index table.
5. Do not add offensive tooling. This skill is for authorized testing of systems you own or
   are permitted to test.

Questions and suggestions: X (Twitter) https://x.com/iwasaki_dev40

**日本語.** 誤りの指摘、実戦の教訓の追加、他フレームワーク向けのメモを歓迎します。
1. 教訓は**一般化**してください。顧客名・会社名・ドメイン・IP・個人名・認証情報は、例であっても含めないでください。
   PR前に `skills/saas-tenant-audit/scripts/leak_scan.sh --terms <非公開語ファイル>` を実行してください（語ファイルはリポジトリ外に置く）。
2. 各教訓に **[field]**（実際に踏んだ）か **[std]**（標準的な作法）のタグを付けてください。
3. 英語版・日本語版（`saas-tenant-audit` と `saas-tenant-audit-ja`）を**同時に**更新し、ファイル名・見出し・FL番号を揃えてください。
4. 新しい教訓は次の空き番号 `FL-nn` を使い、索引表に行を追加してください。
5. 攻撃用ツールは追加しないでください。自分が所有する、または許可を得たシステムの検証のためのスキルです。

質問・提案: X（旧Twitter） https://x.com/iwasaki_dev40
