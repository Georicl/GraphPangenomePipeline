import logging
import sys
from pathlib import Path
from src.base_runner import BaseRunner

class VgIndexStats(BaseRunner):
    def __init__(self, config: dict):
        # 初始化 BaseRunner，对应 [VgIndex] 配置段
        super().__init__(config, 'VgIndex')
        self.VgStats = self.config.get('VgStats', {})

    def run_vg_index_stats(self):
        """仅执行统计 (stats) 和 路径 (paths) 模块"""
        
        # 定义 GBZ 文件位置 (通常来源于 Cactus Step 1)
        gbz_file = self.cactus_dir / f"{self.Global.get('filePrefix')}.full.gbz"
        
        # 确保文件存在并已解压
        if not gbz_file.exists():
            # 尝试寻找解压后的或待解压的
            gbz_file = self._ensure_decompressed(gbz_file)
            if not gbz_file.exists():
                logging.warning(f"GBZ file not found for stats: {gbz_file}. Skipping Step 2.")
                return

        # 1. VG Stats
        if self.VgStats.get('stats'):
            self.vg_stats_dir.mkdir(parents=True, exist_ok=True)
            stats_out = self.vg_stats_dir / "vg_stats.txt"
            logging.info("Starting vg stats...")
            self.run_command(
                ["vg", "stats", "-N", "-E", "-L", "-l", str(gbz_file.resolve())],
                cwd=self.vg_stats_dir,
                stdout_file=stats_out,
                label="vg-stats"
            )

        # 2. VG Paths
        if self.VgStats.get('paths'):
            self.vg_stats_dir.mkdir(parents=True, exist_ok=True)
            paths_out = self.vg_stats_dir / "vg_paths.txt"
            logging.info("Starting vg paths...")
            self.run_command(
                ["vg", "paths", "-L", "-x", str(gbz_file.resolve())],
                cwd=self.vg_stats_dir,
                stdout_file=paths_out,
                label="vg-paths"
            )

if __name__ == "__main__":
    from src.config_loader import ConfigManager
    import sys
    
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    config_path = sys.argv[1] if len(sys.argv) > 1 else "config/config.toml"
    cfg = ConfigManager(config_path).get_config()
    
    runner = VgIndexStats(cfg)
    runner.run_vg_index_stats()