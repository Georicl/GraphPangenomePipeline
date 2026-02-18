# Pipeline Refactoring Plan: Config-first with CLI Overrides

## 1. Objective
Enable the pipeline to be driven primarily by a `config.toml` file while allowing specific parameters to be overridden via CLI arguments for quick experimentation and flexibility.

## 2. Architecture Design

### 2.1 Configuration Manager (`src/config_loader.py`)
- Responsible for loading the base TOML configuration.
- Merges CLI-provided options into the configuration dictionary.
- Provides a unified object to all Runner classes.

### 2.2 Runner Refactoring
- All classes in `src/` (e.g., `CactusRunner`, `VgWgsRunner`) should be updated:
    - **Current**: `__init__(self, config_path: str)` (reads file internally).
    - **Target**: `__init__(self, config: dict)` (receives pre-loaded configuration).

### 2.3 CLI Enhancement (`main.py`)
- Expand `typer` options to include common overrides:
    - `--work-dir` (Overrides `[Global] work_dir`)
    - `--threads` (Overrides threads in `[VgIndex]`, `[wgs]`, `[call]`)
    - `--reference` (Overrides `[Cactus] reference`)
    - `--seq-file` (Overrides `[Cactus] seqFile`)

## 3. Implementation Steps

1.  **[x] Step 1: Create `ConfigManager`**
    - Implement a deep-merge utility for the nested TOML structure.
    - Define a mapping between CLI flags and TOML keys.

2.  **[x] Step 2: Refactor `src/` Runners**
    - Update `run_minicactus.py`, `vg_stats_index.py`, `annotation_pangenome.py`, `vg_wgs.py`, and `vg_call.py`.
    - Ensure they no longer open the config file themselves.

3.  **[x] Step 3: Update `main.py`**
    - Add the new CLI options.
    - Integrate the `ConfigManager` to prepare the `final_config` before calling runners.

4.  **[ ] Step 5: On-demand Indexing (Lazy Loading)**
    - Implement "check-before-build" logic in `BaseRunner.run_autoindex`.
    - If `{workflow}_index.{workflow}.gbz` exists, skip the build and return `True`.
    - Integrated this into `VgWgsRunner` and `RnaSeqRunner` so users don't have to manually run the indexing step if it's already done.

## 5. Example Usage Pattern
```bash
# Use defaults from config.toml
python main.py run --config config/config.toml --all

# Override work directory and threads on the fly
python main.py run -c config/config.toml --all --work-dir ./tmp_run --threads 32
```
