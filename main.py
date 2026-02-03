import argparse
import logging
import sys
from pathlib import Path

src_path = str(Path(__file__).parent.resolve())
if src_path not in sys.path:
    sys.path.append(src_path)


from run_minicactus import CactusRunner
from vg_stats_index import VgIndexStats

def setup_logging():
    "set up log file"
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )

def main():
    setup_logging()

    parser = argparse.ArgumentParser(description="Graph Pangenome Analysis Pipeline")

    parser.add_argument("--config", type=str, required=True, help="Path to the config file")

    parser.add_argument("--cactus-pangenome", action="store_true", help="Run minigraph-cactus module")
    parser.add_argument("--vg", action="store_true", help="Run vg stats and index module")
    parser.add_argument("--all", action="store_true", help="Run the full pipeline (Cactus -> VG)")

    args = parser.parse_args()
    config_path = args.config

    if not Path(config_path).exists():
        logging.error(f"Config file not found: {config_path}")
        sys.exit(1)

    run_cactus = args.cactus_pangenome or args.all
    run_vg = args.vg or args.all

    if not (run_cactus or run_vg):
        parser.print_help()
        sys.exit(0)

    # 1. 运行 Cactus 模块
    if run_cactus:
        logging.info(">>> Starting Step 1: Cactus Pangenome Construction")
        cactus_runner = CactusRunner(config_path)
        cactus_runner.run_cactus()

    # 2. 运行 VG 统计与索引模块
    if run_vg:
        logging.info(">>> Starting Step 2: VG Stats and Indexing")
        vg_runner = VgIndexStats(config_path)
        vg_runner.run_vg_index_stats()

    logging.info("Pipeline execution finished successfully.")


if __name__ == "__main__":
    main()