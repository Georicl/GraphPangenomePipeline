import logging
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
import csv
import subprocess

class VgWgsRunner:
    def __init__(self, config: dict):
        self.config = config

        self.Global:dict = self.config['Global']
        self.wgs: dict = self.config['wgs']

        self.work_dir = Path(self.Global['work_dir']).resolve()
        self.threads = self.wgs['Threads']
        # import vg index file
        self.vg_index = self.work_dir / "3.vg_index"
        self.vg_wgs_output = self.work_dir / "5.wgs_analysis"
        # vg autoindex output file
        self.gbz_file = self.vg_index / "vg_index.giraffe.gbz"
        self.dist_file = self.vg_index / "vg_index.dist"
        self.min_file = self.vg_index / "vg_index.shortread.withzip.min"

    def parser_csv(self) -> list:
        """Parse the csv file and output each line as a list"""
        samples = []
        try:
            with open(self.wgs['DataTable'], 'r', newline='') as f:
                reader = csv.DictReader(f, skipinitialspace=True)
                for row in reader:
                    if 'SampleID' not in row or 'R1' not in row:
                        logging.warning(f"Skipping row (missing SampleID or R1)")
                        continue
                    samples.append(row)
        except Exception as e:
            logging.error(f"Error parsing CSV: {e}")
            sys.exit(1)
        return samples

    def single_sample_process(self, sample_info: dict) -> bool:
        """single sample map process"""

        sample_id = sample_info['SampleID']
        r1 = sample_info['R1']
        r2 = sample_info.get('R2')

        if r2 and not r2.strip():
            r2 = None

        # create sample directory
        sample_dir = self.vg_wgs_output / sample_id
        sample_dir.mkdir(parents=True, exist_ok=True)

        # file name
        gam_file = sample_dir / f"{sample_id}.gam"
        pack_file = sample_dir / f"{sample_id}.pack"

        # step1. vg giraffe map wgs data
        giraffe_cmd = [
            "vg", "giraffe",
            "--gbz-name", str(self.gbz_file),
            "--minimizer-name", str(self.min_file),
            "--dist-name", str(self.dist_file),
            "--threads", str(self.threads),
            "--output-format", "gam",
            "--fastq-in", r1,
        ]
        if r2:
            giraffe_cmd.extend(["--fastq-in", r2])

        logging.info(f"starting Mapping [{sample_id}, directory: {sample_dir}, command: {giraffe_cmd}]")
        try:
            with open(gam_file, "w") as w:
                subprocess.run(giraffe_cmd, stdout=w, check=True, stderr=subprocess.PIPE, cwd=sample_dir)
        except subprocess.CalledProcessError as e:
            logging.error(f"Sample: [{sample_id}] giraffe error: {e.returncode}")
            return False

        # step2. vg pack gam file
        pack_cmd = [
            "vg", "pack",
            "--gam", str(gam_file),
            "--xg", str(self.gbz_file),
            "--packs-out", str(pack_file),
            "--threads", str(self.threads),
            "--min-mapq", str(self.wgs['MinMapQ'])
        ]

        logging.info(f"starting Packing [{gam_file}, directory: {sample_dir}, command: {pack_cmd}]")
        try:
            subprocess.run(pack_cmd, check=True, stderr=subprocess.PIPE, cwd=sample_dir)
        except subprocess.CalledProcessError as e:
            logging.error(f"Pack file: [{gam_file}] pack error: {e.returncode}")
            return False

        # clean gam file
        if pack_file.exists() and pack_file.stat().st_size > 0:
            logging.info(f"[{sample_id}] Mapping & Packing done. Removing intermediate GAM file.")
            gam_file.unlink(missing_ok=True)
        else:
            logging.warning(f"[{sample_id}] Pack file missing or empty. Keeping GAM file for debugging.")
            return False

        return True

    def run_wgs(self):
        """run vg wgs analysis pipeline"""
        if not self.gbz_file.exists():
            logging.error(f"[{self.gbz_file}] does not exist. Please run vg autoindex first.")
            sys.exit(1)

        samples = self.parser_csv()
        if not samples:
            logging.error("No samples found in the CSV file.")
            sys.exit(1)

        parallel_job = self.wgs.get('Parallel_job', 1)
        logging.info(f"Starting WGS analysis with {parallel_job} parallel jobs.")

        with ProcessPoolExecutor(max_workers=parallel_job) as executor:
            future_to_sample = {
                executor.submit(self.single_sample_process, sample_info)
                : sample_info
                for sample_info in samples
            }

            for future in as_completed(future_to_sample):
                sample_id = future_to_sample[future]
                try:
                    success = future.result()
                    status = "SUCCESS" if success else "FAILED"
                    logging.info(f">>> Sample {sample_id}: Pipeline {status}")
                except Exception as e:
                    logging.error(f">>> Sample {sample_id} crashed with exception: {e}")

if __name__ == "__main__":
    from src.config_loader import ConfigManager
    import sys
    
    logging.basicConfig(level=logging.INFO)
    # This is mainly for local testing
    config_path = sys.argv[1] if len(sys.argv) > 1 else "config/config.toml"
    cfg = ConfigManager(config_path).get_config()
    runner = VgWgsRunner(cfg)
    runner.run_wgs()