# Publishing checklist / 公開チェックリスト

## English

1. **Decide the identity.** Repository name (suggested: `saas-tenant-audit-skill`),
   owner account, and the copyright line in `LICENSE` (currently `kai-tecweb`).
2. **Private-terms scan.** Create a file *outside* the repo (e.g. `~/private-terms.txt`),
   one term per line: every client, company, product, person, domain, host name, internal
   code name and project prefix you worked with. Then run:
   ```bash
   skills/saas-tenant-audit/scripts/leak_scan.sh --terms ~/private-terms.txt .
   ```
   Expect `RESULT: clean`. The scan matches exact text only and skips `.git`: list spelling
   variants (romaji, katakana, abbreviations) as separate terms, and read the first commit by
   eye once — it cannot know about things nobody listed.
   **Git identity:** the commit author name and e-mail come from your git config and are
   published with the first commit. Before `git init`, set a repository-local identity
   (for example your GitHub noreply address) and check afterwards with
   `git log --format='%an <%ae>'`.
3. **Contact line.** README, both `SKILL.md` files, `scripts/README.md`, `CONTRIBUTING.md`
   and `docs/comparison*.md` carry the X handle. Confirm it is the one you want public.
4. **Validate the skills load.** Copy both skill folders to a scratch `~/.claude/skills/`
   (or a test project's `.claude/skills/`), start Claude Code, and confirm both appear and
   trigger on a sample request. Check frontmatter: `name` ≤ 64 chars (lowercase, digits,
   hyphens), `description` ≤ 1024 chars.
5. **Initialise and review.**
   ```bash
   git init && git config user.name "<public name>" && git config user.email "<noreply address>"
   git add -A && git status   # review the list
   git commit -m "Initial release 0.1.0"
   ```
6. **Create the GitHub repository** (public), add topics such as `claude-code`,
   `claude-skills`, `security-audit`, `multi-tenant`, `laravel`, `nextjs`, `owasp`,
   `idor`, `bola`, `japanese`; set the description to one sentence; push; tag `v0.1.0`.
7. **After publishing.** Enable private vulnerability reporting/discussions if desired;
   pin the README contact; re-run step 2 whenever you add a lesson.

## 日本語

1. **公開名義を決める。** リポジトリ名（例: `saas-tenant-audit-skill`）、所有アカウント、`LICENSE` の著作権表記
   （現在は `kai-tecweb`）。
2. **非公開語スキャン。** リポジトリ**外**にファイル（例: `~/private-terms.txt`）を作り、1行1語で、関わった顧客名・会社名・製品名・人名・
   ドメイン・ホスト名・社内コード名・テストデータの接頭辞をすべて書く。次を実行し `RESULT: clean` を確認:
   ```bash
   skills/saas-tenant-audit/scripts/leak_scan.sh --terms ~/private-terms.txt .
   ```
   スキャンは完全一致のテキストだけを対象とし、`.git` は対象外です。表記ゆれ（ローマ字、カタカナ、略称）は別の語として列挙してください。
   最初のコミットも一度は目視で確認してください（誰も列挙していない語はスキャンでは検出できません）。
   **gitの識別情報:** コミットの作者名とメールアドレスはgit設定から取られ、最初のコミットとともに公開されます。
   `git init` の前にリポジトリ限定の識別情報（例: GitHubのnoreplyアドレス）を設定し、後で
   `git log --format='%an <%ae>'` で確認してください。
3. **問い合わせ先。** README、両方の `SKILL.md`、`scripts/README.md`、`CONTRIBUTING.md`、`docs/comparison*.md` にXのハンドルを記載済み。
   公開してよいものか確認してください。
4. **スキルが読み込まれるか確認。** 2つのスキルフォルダを検証用の `~/.claude/skills/`（またはテスト用プロジェクトの `.claude/skills/`）にコピーし、
   Claude Codeを起動して両方が表示され、サンプルの依頼で起動することを確認。フロントマター: `name` は64文字以内（小文字・数字・ハイフン）、
   `description` は1024文字以内。
5. **初期化とレビュー。** `git init` の後、`git config user.name` と `git config user.email` をリポジトリ限定で設定し、`git add -A && git status` で一覧を確認して最初のコミットを作成。
6. **GitHubに公開リポジトリを作成。** トピック例: `claude-code` `claude-skills` `security-audit` `multi-tenant` `laravel` `nextjs`
   `owasp` `idor` `bola` `japanese`。説明は1文。push して `v0.1.0` をタグ付け。
7. **公開後。** 必要なら脆弱性の非公開報告/Discussionsを有効化。教訓を追加するたびに手順2を再実行。
