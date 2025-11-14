# Agent Instructions for TowPilot Lead Scraper

## Python Environment Management

**IMPORTANT: This project uses `uv` for Python package management, NOT venv/pip.**

### Why `uv`?
- **Faster**: 10-100x faster than pip
- **Better dependency resolution**: More reliable than pip
- **Modern**: Built with Rust, designed for modern Python workflows
- **Compatible**: Works with existing Python projects

### Setup Instructions

1. **Install `uv`** (if not already installed):
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   # Or on macOS:
   brew install uv
   ```

2. **Create virtual environment and install dependencies**:
   ```bash
   uv venv .venv
   source .venv/bin/activate
   uv pip install -r requirements.txt
   ```

3. **Activate the environment**:
   ```bash
   source .venv/bin/activate
   # Or use uv run directly:
   uv run python script.py
   ```

4. **Run commands**:
   ```bash
   # Run Python scripts
   uv run python scripts/download_apify_runs.py --list-only
   
   # Run with dependencies
   uv run uvicorn app.main:app --reload
   
   # Run tests
   uv run pytest tests/
   ```

### Common `uv` Commands

```bash
# Install/sync dependencies from pyproject.toml or requirements.txt
uv sync

# Add a new dependency
uv add package-name

# Add a dev dependency
uv add --dev package-name

# Remove a dependency
uv remove package-name

# Update dependencies
uv sync --upgrade

# Run a command in the environment
uv run <command>

# Show installed packages
uv pip list
```

### Makefile Integration

The Makefile has been updated to use `uv`:
- `make install` → `uv sync`
- `make run` → `uv run uvicorn ...`
- All Python commands use `uv run`

### Migration from venv/pip

If you have an existing `venv/` directory:
1. Remove it: `rm -rf venv/`
2. Run `uv sync` to create `.venv/`
3. Update your IDE to use `.venv/bin/python` instead of `venv/bin/python`

### Project Structure

```
.
├── .venv/              # uv-managed virtual environment (created by uv sync)
├── pyproject.toml      # Project metadata (if using uv project)
├── requirements.txt    # Dependencies (uv can use this)
├── uv.lock            # Lock file (if using uv project)
└── Makefile           # Commands using uv
```

## Development Workflow

1. **Initial Setup**:
   ```bash
   make init  # Creates .venv, installs deps, sets up DB
   ```

2. **Daily Development**:
   ```bash
   source .venv/bin/activate  # Or use uv run
   make run                   # Start API server
   ```

3. **Adding Dependencies**:
   ```bash
   uv add package-name
   # Or manually edit requirements.txt and run:
   uv sync
   ```

4. **Running Scripts**:
   ```bash
   uv run python scripts/download_apify_runs.py --list-only
   # Or activate first:
   source .venv/bin/activate
   python scripts/download_apify_runs.py --list-only
   ```

## Troubleshooting

### "uv: command not found"
Install uv: `curl -LsSf https://astral.sh/uv/install.sh | sh`

### "ModuleNotFoundError"
Run `uv sync` to ensure all dependencies are installed

### IDE not recognizing packages
Point your IDE to `.venv/bin/python` (not `venv/bin/python`)

### Alembic migrations failing
Ensure `DATABASE_URL` is set correctly in `.env` and uses `postgresql+asyncpg://` format

## Notes

- `uv` creates `.venv/` directory (not `venv/`)
- All Makefile commands use `uv` internally
- Scripts can be run with `uv run` or after activating `.venv`
- `uv sync` is equivalent to `pip install -r requirements.txt` but faster

