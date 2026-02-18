import logging
import shlex
from pathlib import Path
from src.base_runner import BaseRunner

class CactusRunner(BaseRunner):
    """
    Minigraph-Cactus runner
    Use Cactus to assemble pangenome graph
    """
    def __init__(self, config: dict):
        # 继承 BaseRunner，自动设置 cactus_dir
        super().__init__(config, section_name="Cactus")
        self.Cactus = self.section
        self.CactusOutFormat = self.config.get('CactusOutFormat', {})

    def _cactus_command(self) -> list:
        """
        生成 cactus-pangenome 运行命令
        """
        self.cactus_dir.mkdir(parents=True, exist_ok=True)
        cactus_job_store = self.cactus_dir / "jobStore"

        cmd = [
            "cactus-pangenome",
            str(cactus_job_store.resolve()),
            str(Path(self.Cactus.get('seqFile')).resolve()),
            "--outDir", str(self.cactus_dir.resolve()),
            "--outName", str(self.Global.get('filePrefix')),
            "--maxCores", str(self.Cactus.get('maxCores', 8)),
            "--reference", str(self.Cactus.get('reference')),
        ]

        # 设置输出格式
        if self.CactusOutFormat.get('vcf'): cmd.extend(shlex.split('--vcf full'))
        if self.CactusOutFormat.get('gfa'): cmd.extend(shlex.split('--gfa full'))
        if self.CactusOutFormat.get('gbz'): cmd.extend(shlex.split('--gbz full'))

        # Singularity 容器化
        singularity_image = self.Cactus.get('singularityImage')
        if singularity_image and singularity_image != "":
            logging.info(f"Using Singularity image: {singularity_image}")
            cmd = ["singularity", "exec", str(singularity_image)] + cmd
            
        return cmd

    def run_cactus(self) -> None:
        """运行 Cactus"""
        seq_file = Path(self.Cactus.get('seqFile'))
        if not seq_file.exists():
            logging.error(f"seqFile not found: {seq_file}! Cactus needs a seqFile to build graph pangenome.")
            sys.exit(1)

        cactus_cmd = self._cactus_command()
        logging.info("Starting Cactus pangenome assembly...")
        
        # 使用父类统一的运行工具
        if not self.run_command(cactus_cmd, cwd=self.cactus_dir, label="cactus"):
            sys.exit(1)
        
        logging.info("Cactus-pangenome pipeline finished successfully.")

if __name__ == '__main__':
    from src.config_loader import ConfigManager
    import sys
    
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    config_path = sys.argv[1] if len(sys.argv) > 1 else "config/config.toml"
    cfg = ConfigManager(config_path).get_config()
    
    runner = CactusRunner(cfg)
    runner.run_cactus()