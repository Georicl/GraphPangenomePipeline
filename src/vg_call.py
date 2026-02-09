from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
import logging
import tomllib
import subprocess
import sys

class CallVariantRunner:
    def __init__(self, config_path: str):
        with open(config_path, "rb") as f:
            self.config = tomllib.load(f)

        # [Global]
        self.work_dir: Path = Path(self.config['Global']['work_dir']).resolve()
        self.wgs_dir: Path = self.work_dir / "5.wgs_analysis"
        self.call_dir: Path = self.work_dir / "6.call_variant"
        self.gbz_file: Path = self.work_dir / "3.vg_index" / "vg_index.giraffe.gbz"
        # [call]
        self.call: dict = self.config['call']

    def _parsing_path(self) -> list[Path]:
        """解析pack文件的地址, 以方便使用"""
        return sorted(list(self.wgs_dir.rglob("*.pack")))

    def _single_call_variant(self, pack_file: Path) -> bool:
        """对单个pack文件进行输出"""
        # 样本id前缀
        sample_id = pack_file.stem
        call_cmd = [
            "vg", "call",
            "--pack", str(pack_file.resolve()),
            "--threads", str(self.call['Threads']),
            str(self.gbz_file.resolve()),
        ]
        # 创建样本目录
        sample_dir = self.call_dir / sample_id
        try:
            logging.info(f"starting vg call variant, now running in {sample_dir}, command: {call_cmd}")
            sample_dir.mkdir(parents=True, exist_ok=True)
            vcf_file = sample_dir / f"{sample_id}.vcf"
            # 写入文件, 因为vg需要的是重定向结果出vcf
            with open(vcf_file, "w") as w:
                subprocess.run(call_cmd, stdout=w, check=True, stderr=subprocess.PIPE, cwd=sample_dir, text=True)
        except subprocess.CalledProcessError as e:
            logging.error(f"Sample: [{sample_id}] call variant error: {e.returncode}, strderr: {e.stderr}")
            return False
        return True

    def run_vg_call(self):
        """运行vg call variant"""
        if not self.gbz_file.exists():
            logging.error(f"[{self.gbz_file}] does not exist. Please run vg autoindex first.")
            sys.exit(1)

        pack_files = self._parsing_path()
        if not pack_files:
            logging.error("No pack files found.")
            sys.exit(1)

        parallel_job = self.call.get('Parallel_job', 1)

        logging.info(f"开始vg call variant 流程, 并行{parallel_job}个")

        with ProcessPoolExecutor(max_workers=parallel_job) as executor:
            future_to_pack = {
                executor.submit(self._single_call_variant, pack_file): pack_file
                for pack_file in pack_files
            }

            for future in as_completed(future_to_pack):
                pack_file = future_to_pack[future]
                try:
                    success = future.result()
                    status = "SUCCESS" if success else "FAILED"
                    logging.info(f">>> Sample {pack_file.name}: Pipeline {status}")
                except Exception as e:
                    logging.error(f">>> Sample {pack_file.name} crashed with exception: {e}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    runner = CallVariantRunner("../config/config.toml")
    runner.run_vg_call()