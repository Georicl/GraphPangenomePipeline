import logging
import sys
from pathlib import Path
from src.base_runner import BaseRunner

class AnnotationRunner(BaseRunner):
    def __init__(self, config: dict):
        # 继承 BaseRunner，自动设置 annotation_dir (对应父类的 self.annotation_dir)
        super().__init__(config, section_name="Annotation")
        self.annotation = self.section
        self.gff3 = self.annotation.get('gff3')
        # gfa file (使用父类统一管理的路径)
        self.gfa_file = self.cactus_dir / f"{self.Global.get('filePrefix')}.full.gfa"

    def _grannot_gaf_command(self) -> list:
        return [
            "grannot",
            str(self.gfa_file.resolve()),
            str(Path(self.gff3).resolve()),
            str(self.annotation.get('SourceGenome', 'reference')),
            "-gaf",
            "-o",
            str(self.annotation_dir.resolve())
        ]

    def _grannot_ann_command(self) -> list:
        cmd = [
            "grannot",
            str(self.gfa_file.resolve()),
            str(Path(self.gff3).resolve()),
            str(self.annotation.get('SourceGenome', 'reference')),
            "--outdir",
            str(self.annotation_dir.resolve())
        ]
        # 合并自定义参数
        anno_options = self.config.get('ann', {})
        for key, value in anno_options.items():
            if value == "" or value is None:
                continue
            flag_name = f"--{key}"
            if isinstance(value, bool):
                if value:
                    cmd.append(flag_name)
            else:
                cmd.extend([flag_name, str(value)])
        return cmd

    def run_annotation(self) -> None:
        """运行 Grannot 注释流程"""
        # 确保 GFA 文件已解压
        self._ensure_decompressed(self.gfa_file)
        self.annotation_dir.mkdir(parents=True, exist_ok=True)

        gaf_cmd = self._grannot_gaf_command()
        ann_cmd = self._grannot_ann_command()

        # Singularity 容器化封装
        singularity_image = self.annotation.get('singularityImage')
        if singularity_image:
            sin_prefix = ["singularity", "exec", str(singularity_image)]
            gaf_cmd = sin_prefix + gaf_cmd
            ann_cmd = sin_prefix + ann_cmd

        # 1. 生成 GAF
        if self.config.get('Gaf', {}).get('Gaf'):
            logging.info("Starting Grannot: Generating GAF annotation file...")
            if not self.run_command(gaf_cmd, cwd=self.annotation_dir, label="grannot-gaf"):
                sys.exit(1)

        # 2. 生成 Target Annotation (PAV 矩阵等)
        if self.config.get('ann', {}).get('annotation'):
            logging.info("Starting Grannot: Generating target annotation file...")
            if not self.run_command(ann_cmd, cwd=self.annotation_dir, label="grannot-ann"):
                sys.exit(1)

if __name__ == "__main__":
    from src.config_loader import ConfigManager
    import sys
    
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    config_path = sys.argv[1] if len(sys.argv) > 1 else "config/config.toml"
    cfg = ConfigManager(config_path).get_config()
    
    runner = AnnotationRunner(cfg)
    runner.run_annotation()