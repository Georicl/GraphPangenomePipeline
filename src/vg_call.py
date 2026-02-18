import logging
from pathlib import Path
from src.base_runner import BaseRunner

class CallVariantRunner(BaseRunner):
    def __init__(self, config: dict):
        # 继承 BaseRunner，自动设置 wgs_dir, call_dir 等路径
        super().__init__(config, section_name="call")
        self.call = self.section

    def _find_gbz_index(self) -> Path:
        """从 wgs_dir 中查找比对时使用的 .gbz 索引文件"""
        matches = [f for f in self.wgs_dir.iterdir() if f.name.endswith(".gbz")]
        if not matches:
            raise FileNotFoundError(f"Missing .gbz index file in {self.wgs_dir}. Did you run WGS mapping?")
        return matches[0]

    def _get_pack_files(self) -> list[Path]:
        """从 wgs_dir 中递归查找所有样本产生的 .pack 文件"""
        return sorted(list(self.wgs_dir.rglob("*.pack")))

    def single_sample_process(self, pack_file: Path) -> bool:
        """对单个 pack 文件执行 vg call"""
        sample_id = pack_file.stem
        # 创建样本专用目录（在 6.call_variant 下）
        sample_dir = self.call_dir / sample_id
        sample_dir.mkdir(parents=True, exist_ok=True)
        
        vcf_file = sample_dir / f"{sample_id}.vcf"

        call_cmd = [
            "vg", "call",
            "--pack", str(pack_file.resolve()),
            "--threads", str(self.threads),
            str(self.gbz_file.resolve()),
        ]

        logging.info(f"Sample [{sample_id}]: Starting Variant Calling...")
        # 使用 BaseRunner 的 run_command 处理标准输出重定向到 .vcf
        return self.run_command(call_cmd, cwd=sample_dir, stdout_file=vcf_file, label=f"call-{sample_id}")

    def run_vg_call(self):
        """执行完整的变异检测流程"""
        # A. 动态定位依赖的 GBZ 索引
        try:
            self.gbz_file = self._find_gbz_index()
            logging.info(f"Using GBZ index for calling: {self.gbz_file.name}")
        except FileNotFoundError as e:
            logging.error(e)
            sys.exit(1)

        # B. 搜寻输入 pack 文件
        pack_files = self._get_pack_files()
        if not pack_files:
            logging.error(f"No .pack files found in {self.wgs_dir}. Aborting.")
            sys.exit(1)

        # C. 并行执行 (调用父类通用并行器)
        # 注意：这里我们传递的是 pack_files 列表，
        # 为了兼容 run_parallel 的 s['SampleID'] 访问，我们需要包装一下
        samples_payload = [{"SampleID": p.stem, "pack": p} for p in pack_files]
        
        # 内部函数，适配参数
        def _wrapper(s): return self.single_sample_process(s['pack'])
        
        self.run_parallel(samples_payload, _wrapper, label="Call Variant")

if __name__ == "__main__":
    from src.config_loader import ConfigManager
    import sys
    
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    config_path = sys.argv[1] if len(sys.argv) > 1 else "config/config.toml"
    cfg = ConfigManager(config_path).get_config()
    
    runner = CallVariantRunner(cfg)
    runner.run_vg_call()