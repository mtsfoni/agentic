---
name: playwright
description: Use Playwright CLI for browser testing, UI inspection, screenshots, and web interaction. Use when validating pages or browser workflows.
---

# Playwright CLI

Use `playwright-cli` with Chromium defaults from the shell.

Rules:

- Run `playwright-cli open <url>` first.
- Then use follow-up commands without `-s`; the default session is reused.
- If the page animates, wait before capture: `sleep 2 && playwright-cli snapshot`.

Examples:

- `playwright-cli open https://example.com`
- `playwright-cli goto https://www.nytimes.com/games/wordle/index.html`
- `playwright-cli snapshot`
- `playwright-cli screenshot --filename=/.playwright/page.png`
