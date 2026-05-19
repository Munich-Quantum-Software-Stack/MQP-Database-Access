# 🤝 Contributing to MQP Database Access

Thank you for your interest in contributing to **MQP-Database-Access**, the database access component of the Munich Quantum Portal (MQP) Dashboard and part of the Munich Quantum Software Stack (MQSS).

## 📜 Code of Conduct

Please read and follow our [Code of Conduct](./CODE_OF_CONDUCT.md).

## ❓ How Can I Contribute?

You can help by:

- Reporting bugs
- Suggesting improvements or new features
- Contributing code, tests, or documentation

Use the GitHub issues page: <https://github.com/Munich-Quantum-Software-Stack/MQP-Database-Access/issues>

## 🐛 Reporting Bugs

Before opening a new issue, please check whether the problem has already been reported.

When filing a bug, include:

1. Your environment details (OS, Python version, database backend/version if relevant)
2. Minimal steps to reproduce
3. Expected behavior vs. actual behavior
4. Relevant logs or traceback output

## ✨ Suggesting Improvements / Features

Open an issue on the same GitHub issues page and clearly describe:

- The current limitation or pain point
- The proposed improvement
- Why it is useful for MQP/MQSS users

## 💻 Local Development Setup

1. Fork and clone the repository.
2. Install dependencies with PDM:

```bash
pdm install
```

3. Create a branch using the naming conventions below.

## 🧪 Running Tests

Run the test suite with:

```bash
pdm run pytest
```

> Note: test environment values are configured via `pyproject.toml` (`[tool.pytest.ini_options].env`).

## 🔍 Type Checking and Linting

Run static checks before opening a PR:

```bash
pdm run mypy bqp_database_access/
pdm run pylint bqp_database_access/
```

## 🌿 Branch Naming Conventions

Please use:

- `fix/<BUG>` for bug fixes
- `feat/<FEATURE>` for new features
- `docs/<CHANGE>` for documentation updates
- `test/<CHANGE>` for test-related changes

## ✅ Pull Request Guidelines

- Use a clear, descriptive title (for example: `FEAT: add <capability>` or `FIX: resolve <issue>`).
- Keep each PR focused on a single concern.
- Link related issues in the PR description (for example: `Closes #123`).
- Ensure tests and checks pass before requesting review.
- Add or update tests when behavior changes.

## 🗄️ Database and Environment Notes

- This repository is a **Python database access package** (not a frontend app and not a Flask backend).
- Ensure local database/environment settings are consistent with project expectations when running tests and development workflows.
- Review environment-dependent pytest defaults in `pyproject.toml` before troubleshooting test behavior.

## 🔐 Security and Secrets

Never commit secrets or sensitive material, including:

- `.env` files
- passwords
- peppers
- API tokens
- private keys
- any credential-like value

If sensitive data is committed accidentally, rotate/revoke it immediately and remove it from git history.