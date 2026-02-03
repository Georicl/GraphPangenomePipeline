import tomllib
import subprocess
from pathlib import Path
import logging

class VgIndexStats:
    def __init__(self, config_path: str):
        with open(config_path, 'rb') as f:
            self.config = tomllib.load(f)
        self.Global = self.config['Global']
        self.work_dir = Path(self.Global['work_dir']).resolve()
        self.VgStats = self.config['VgStats']
        self.VgIndex = self.config['VgIndex']
        
        # Initialize paths
        self.vg_stats_dir: Path = self.work_dir / "2. vg_stats"
        self.vg_index_dir: Path = self.work_dir / "3. vg_index"
        self.cactus_dir: Path = self.work_dir / "1. cactus" / "pangenome"

    def _run_command(self, cmd: list, cwd: Path, output_file: Path = None):
        """
        Helper method to run commands in a specific directory.
        """
        cwd.mkdir(parents=True, exist_ok=True)
        logging.info(f"Running command in {cwd}: {' '.join(cmd)}")
        
        try:
            if output_file:
                with open(output_file, "w") as f:
                    subprocess.run(cmd, stdout=f, check=True, text=True, cwd=cwd)
                logging.info(f"Finished. Output saved to {output_file.name}")
            else:
                subprocess.run(cmd, check=True, text=True, cwd=cwd)
                logging.info(f"Finished.")
            return True
        except subprocess.CalledProcessError as e:
            logging.error(f"Command failed with return code {e.returncode}: {e}")
            return False
        except Exception as e:
            logging.error(f"An unexpected error occurred: {e}")
            return False

    def _stats_vg_command(self) -> list:
        # Use absolute path for input file so it works regardless of cwd
        cactus_gbz_file = self.cactus_dir / f"{self.Global['filePrefix']}.gbz"
        return [
            "vg", "stats",
            "-N", "-E", "-L", "-l",
            str(cactus_gbz_file.resolve())
        ]

    def _paths_vg_command(self) -> list:
        cactus_gbz_file = self.cactus_dir / f"{self.Global['filePrefix']}.gbz"
        return [
            "vg", "paths",
            "-x", "-L",
            str(cactus_gbz_file.resolve())
        ]

    def _autoindex_vg_command(self) -> list:
        cactus_gfa_file = self.cactus_dir / f"{self.Global['filePrefix']}.gfa"
        return [
            "vg", "autoindex",
            "--workflow", "giraffe",
            "-g", str(cactus_gfa_file.resolve()),
            "-p", "vg_index",  # Output prefix relative to cwd (3. vg_index)
            "-t", str(self.VgIndex['threads'])
        ]

    def run_vg_index_stats(self):
        # 1. Run VG Stats if enabled
        if self.VgStats.get('stats'):
            logging.info("Start running vg stats")
            self._run_command(
                self._stats_vg_command(), 
                cwd=self.vg_stats_dir, 
                output_file=self.vg_stats_dir / "vg_stats.txt"
            )

        # 2. Run VG Paths if enabled
        if self.VgStats.get('paths'):
            logging.info("Start running vg paths")
            self._run_command(
                self._paths_vg_command(), 
                cwd=self.vg_stats_dir, 
                output_file=self.vg_stats_dir / "vg_paths.txt"
            )

        # 3. Run VG Autoindex if enabled
        if self.VgIndex.get('autoindex'):
            logging.info("Start running vg autoindex")
            # Runs in vg_index_dir, so -p vg_index creates files there
            self._run_command(
                self._autoindex_vg_command(), 
                cwd=self.vg_index_dir
            )