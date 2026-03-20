# Contributing to FitCrave AI Backend

## Branch Structure

```
main          ← production-ready, never push directly
  └── develop ← shared integration branch, all features merge here
        ├── feature/raghu-[task]
        ├── feature/sharath-[task]
        └── feature/rachit-[task]
```

## Module Ownership

To minimize merge conflicts, each person primarily owns a module:

| Module | Path | Owner |
|---|---|---|
| Workout Engine | `app/engines/workout/` | Raghu |
| Nutrition Engine | `app/engines/nutrition/` | Sharath |
| LangGraph / Orchestration | `graph/` | Rachit |
| Models, Config, DB | `app/models/`, `app/config.py`, `utils/` | Raghu (coordinate via PR) |
| Tests | `tests/` | Everyone |

> If you need to touch a file outside your module, flag it in your PR description.

## Daily Workflow

### 1. Start a new task
```bash
git checkout develop
git pull origin develop
git checkout -b feature/yourname-short-description
```

### 2. Commit often with clear messages
Follow this format:
```
feat: add calorie override to meal logger
fix: correct macro rounding in calculator
refactor: extract LLM retry logic to utils
docs: update workout engine readme
```

### 3. Before opening a PR — sync with develop
```bash
git fetch origin
git rebase origin/develop
# resolve any conflicts, then:
git push origin feature/yourname-task
```

### 4. Open a Pull Request to `develop`
- Title: same format as commit messages
- Description: what changed, why, and any modules touched outside your ownership area
- At least one other person must review before merging

## Environment Setup

1. Copy `.env.example` to `.env`
   ```bash
   cp .env.example .env
   ```
2. Fill in your own API keys — **never share or commit your `.env`**
3. Each developer should have their own:
   - MongoDB database (use your name as `MONGODB_DB_NAME`, e.g. `fitcrave_sharath`)
   - Gemini API key (free tier is fine for dev)
   - Firebase credentials JSON (ask Raghu for a dev service account)

## Rules

- **Never push directly to `main` or `develop`** — always use a PR
- **Never commit `.env`** or any file with secrets
- If your branch is more than 2 days old without a PR, rebase against `develop`
- Keep PRs small and focused — one feature/fix per PR
