import logging
import sys
import csv
import subprocess
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed

class BaseRunner:
    def __init__(self, config: dict, section_name: str = None):
        self.config = config
        self.Global: dict = self.config.get('Global', {})
        self.section = self.config.get(section_name, {}) if section_name else {}

        # 基础路径管理
        self.work_dir = Path(self.Global.get('work_dir', './work')).resolve()
        self.prefix = self.Global.get('filePrefix', 'vg_index')
        self.cactus_dir = self.work_dir / "1.cactus"
        self.vg_stats_dir = self.work_dir / "2.vg_stats"
        self.annotation_dir = self.work_dir / "3.annotation"
        self.wgs_dir = self.work_dir / "4.wgs_analysis"
        self.call_dir = self.work_dir / "5.call_variant"
        self.rna_dir = self.work_dir / "6.rna_seq"

        # 通用配置 (仅在传入 section_name 时有效)
        if section_name:
            self.threads = self.section.get('Threads', self.section.get('threads', 8))
            self.parallel_job = self.section.get('Parallel_job', 1)
            self.data_table = self.section.get('DataTable')

    def _ensure_decompressed(self, file_path: Path) -> Path:
        """确保文件已解压，如果存在 .gz 则解压它"""
        gz_path = file_path.with_name(file_path.name + ".gz")
        if gz_path.exists() and not file_path.exists():
            logging.info(f"Decompressing {gz_path.name}...")
            try:
                subprocess.run(["gzip", "-d", str(gz_path.resolve())], check=True)
            except subprocess.CalledProcessError as e:
                logging.error(f"Decompression failed: {e}")
                sys.exit(1)
        return file_path

    def run_command(self, cmd: list, cwd: Path, stdout_file: Path = None, label: str = "") -> bool:
        """通用的命令执行工具"""
        msg = f"[{label}] " if label else ""
        logging.info(f"{msg}Running: {' '.join(cmd)}")
        try:
            if stdout_file:
                with open(stdout_file, "w") as w:
                    subprocess.run(cmd, stdout=w, check=True, stderr=subprocess.PIPE, cwd=cwd, text=True)
            else:
                subprocess.run(cmd, check=True, stderr=subprocess.PIPE, cwd=cwd, text=True)
            return True
        except subprocess.CalledProcessError as e:
            err_msg = e.stderr.strip().splitlines()[-1] if e.stderr else "Unknown error"
            logging.error(f"{msg}Command failed (exit {e.returncode}): {err_msg}")
            return False

    def run_autoindex(self, workflow: str, gff: str = None) -> bool:
        """封装 vg autoindex，索引直接生成在对应的工作目录下"""
        # 1. 确定目标目录和核心后缀
        if workflow == "giraffe":
            target_dir = self.wgs_dir
            required_suffixes = [".gbz", ".dist", ".min"]
        elif workflow == "mpmap":
            target_dir = self.rna_dir
            required_suffixes = [".gcsa", ".lcp"]
        else:
            logging.error(f"Invalid workflow: {workflow}")
            return False

        target_dir.mkdir(parents=True, exist_ok=True)

        # 2. 检查目录下是否已经存在对应后缀的文件（忽略前缀名）
        files_in_dir = list(target_dir.iterdir())
        found_all = True
        for ext in required_suffixes:
            if not any(f.name.endswith(ext) for f in files_in_dir):
                found_all = False
                break
        
        if found_all:
            logging.info(f"Required {workflow} index files ({required_suffixes}) already exist in {target_dir}, skipping.")
            return True

        # 3. 如果没找到，则运行构建逻辑
        gfa_file = self.cactus_dir / f"{self.Global.get('filePrefix')}.full.gfa"
        self._ensure_decompressed(gfa_file)
        
        cmd = [
            "vg", "autoindex",
            "--workflow", workflow,
            "-g", str(gfa_file.resolve()),
            "-p", "index",
            "-t", str(self.threads if hasattr(self, 'threads') else 8)
        ]
        
        if workflow == "mpmap" and gff:
            cmd.extend(["--tx-gff", str(Path(gff).resolve())])

        return self.run_command(cmd, cwd=target_dir, label=f"autoindex-{workflow}")

    def parser_csv(self) -> list:
        """解析 DataTable CSV"""
        if not self.data_table:
            return []
        dt_path = Path(self.data_table).resolve()
        if not dt_path.exists():
            logging.error(f"DataTable not found: {dt_path}")
            return []

        samples = []
        try:
            with open(dt_path, 'r', newline='') as f:
                reader = csv.DictReader(f, skipinitialspace=True)
                for row in reader:
                    if 'SampleID' not in row or 'R1' not in row:
                        continue
                    samples.append(row)
        except Exception as e:
            logging.error(f"Error parsing CSV: {e}")
            return []
        return samples

    def run_parallel(self, samples: list, process_func, label: str = "Pipeline"):
        """通用并行执行器"""
        if not samples:
            logging.error("No samples found to process.")
            return

        logging.info(f"Starting parallel processing with {self.parallel_job} jobs")
        with ProcessPoolExecutor(max_workers=self.parallel_job) as executor:
            future_to_sample = {
                executor.submit(process_func, s): s for s in samples
            }
            for future in as_completed(future_to_sample):
                s = future_to_sample[future]
                try:
                    success = future.result()
                    status = "SUCCESS" if success else "FAILED"
                    logging.info(f">>> Sample {s['SampleID']}: {label} {status}")
                except Exception as e:
                    logging.error(f">>> Sample {s['SampleID']} crashed: {e}")
