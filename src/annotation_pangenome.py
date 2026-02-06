import logging
import subprocess
import sys
import tomllib
from pathlib import Path

class AnnotationRunner:
    def __init__(self, config_path: str):
        with open(config_path, 'rb') as f:
            self.config: dict = tomllib.load(f)
        self.annotation: dict = self.config['Annotation']
        self.Global: dict = self.config['Global']
        self.gff3: str = self.annotation['gff3']
        self.work_dir: Path= Path(self.Global['work_dir']).resolve()
        # gfa file(full)
        self.gfa_file: Path= self.work_dir / "1.cactus" / f"{self.Global['filePrefix']}.full.gfa"
        # annot dir
        self.anno_dir: Path = self.work_dir / "4.annotation"


    # 使用grannot进行注释, 需要的是拼接基因组路径, 找到seqfile的基因组, 还有基因组注释文件, 然后输入

    # def _genome_path(self) -> str:
    #     seq_map = {}
    #     with open(self.config['Cactus']['seqFile'], 'r') as f:
    #         for line in f:
    #             line = line.strip()
    #             parts = line.split()
    #             seq_map[parts[0]] = parts[1]
    #     return seq_map[self.annotation['SourceGenome']]

    def _grannot_gaf_command(self) -> list:
        return [
            "grannot",
            str(self.gfa_file),
            str(self.gff3),
            str(self.annotation['SourceGenome']),
            "-gaf",
            "-o",
            str(self.anno_dir.resolve())
        ]

    def _grannot_ann_command(self):
        cmd = [
            "grannot",
            str(self.gfa_file),
            str(self.gff3),
            str(self.annotation['SourceGenome']),
            "--outdir",
            str(self.anno_dir.resolve())
        ]
        anno_options = self.config.get('ann', {})
        for key, value in anno_options.items():
            if value == "" or value is None:
                continue
            # add the flag name to the command
            flag_name = f"--{key}"

            if isinstance(value, bool):
                # if the option value is a boolean, add the flag name without a value
                if value:
                    cmd.append(flag_name)
            else:
                cmd.extend([flag_name, str(value)])

        return cmd

    def run_annotation(self) -> None:
        # create annotation dir
        self.anno_dir.mkdir(parents=True, exist_ok=True)
        gaf_cmd = self._grannot_gaf_command()
        ann_cmd = self._grannot_ann_command()

        # use singularity to run Grannot
        singularity_image = self.annotation.get('singularityImage')
        if singularity_image:
            sin_cmd = ["singularity", "exec", str(singularity_image)]
            gaf_cmd = sin_cmd + gaf_cmd
            ann_cmd = sin_cmd + ann_cmd

        # run grannot
        if self.config['Gaf'].get('gaf'):
            logging.info("Start running grannot generate gaf annotation file")
            try:
                subprocess.run(gaf_cmd, capture_output=False, check=True, text=True)
                logging.info("finish.")
            except subprocess.CalledProcessError as e:
                logging.error(f"grannot error: {e.returncode}")
                sys.exit(1)

        if self.config['ann'].get('annotation'):
            logging.info("Start running grannot generate target annotation file")
            try:
                subprocess.run(ann_cmd, capture_output=False, check=True, text=True)
                logging.info("finish.")
            except subprocess.CalledProcessError as e:
                logging.error(f"grannot error: {e.returncode}")
                sys.exit(1)