import logging
from operator import truediv
from pathlib import Path
from src.base_runner import BaseRunner

class VgWgsRunner(BaseRunner):
    def __init__(self, config: dict):
        # 继承 BaseRunner，自动设置 wgs_dir 等路径
        super().__init__(config, section_name="wgs")
        self.wgs = self.section

    def _find_index(self, suffix: str) -> Path:
        """根据后缀在 wgs_dir 中动态查找文件"""
        matches = [f for f in self.wgs_dir.iterdir() if f.name.endswith(suffix)]
        if not matches:
            raise FileNotFoundError(f"Missing index file ending with '{suffix}' in {self.wgs_dir}")
        return matches[0]

    def single_sample_process(self, sample_info: dict) -> bool:
        """单个样本的比对和 Pack 流程"""
        sample_id = sample_info['SampleID']
        r1 = sample_info['R1']
        r2 = sample_info.get('R2')

        if r2 and not r2.strip():
            r2 = None

        # 创建样本专用目录（在 5.wgs_analysis 下）
        sample_dir = self.wgs_dir / sample_id
        sample_dir.mkdir(parents=True, exist_ok=True)

        # 文件定义
        gam_file = sample_dir / f"{sample_id}.gam"
        pack_file = sample_dir / f"{sample_id}.pack"

        # 1. vg giraffe 比对 (标准输出重定向到 .gam)
        giraffe_cmd = [
            "vg", "giraffe",
            "--gbz-name", str(self.gbz_file.resolve()),
            "--minimizer-name", str(self.min_file.resolve()),
            "--dist-name", str(self.dist_file.resolve()),
            "--threads", str(self.threads),
            "--output-format", "gam",
            "--fastq-in", r1,
        ]
        if r2:
            giraffe_cmd.extend(["--fastq-in", r2])

        logging.info(f"Sample [{sample_id}]: Starting Mapping...")
        if not self.run_command(giraffe_cmd, cwd=sample_dir, stdout_file=gam_file, label=f"giraffe-{sample_id}"):
            return False

        # 2. vg pack 压缩
        pack_cmd = [
            "vg", "pack",
            "--gam", str(gam_file.resolve()),
            "--xg", str(self.gbz_file.resolve()),
            "--packs-out", str(pack_file.resolve()),
            "--threads", str(self.threads),
            "--min-mapq", str(self.wgs.get('MinMapQ', 0))
        ]

        logging.info(f"Sample [{sample_id}]: Starting Packing...")
        if not self.run_command(pack_cmd, cwd=sample_dir, label=f"pack-{sample_id}"):
            return False

        return True

    def run_wgs(self):
        """执行完整的 WGS 分析流程"""
        # A. 确保索引存在
        logging.info("Step 1: Checking/Building VG Giraffe Index...")
        if not self.run_autoindex("giraffe"):
            logging.error("VG Autoindex failed. Aborting.")
            sys.exit(1)

        # B. 动态加载索引文件路径
        try:
            self.gbz_file = self._find_index(".gbz")
            self.dist_file = self._find_index(".dist")
            self.min_file = self._find_index(".min")
            logging.info(f"Using GBZ: {self.gbz_file.name}")
        except FileNotFoundError as e:
            logging.error(e)
            sys.exit(1)

        # C. 解析样本
        samples = self.parser_csv()
        if not samples:
            logging.error("No valid samples found in DataTable.")
            sys.exit(1)

        # D. 并行执行 (调用父类通用并行器)
        self.run_parallel(samples, self.single_sample_process, label="WGS Pipeline")

if __name__ == "__main__":
    from src.config_loader import ConfigManager
    import sys
    
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    config_path = sys.argv[1] if len(sys.argv) > 1 else "config/config.toml"
    cfg = ConfigManager(config_path).get_config()
    
    runner = VgWgsRunner(cfg)
    runner.run_wgs()