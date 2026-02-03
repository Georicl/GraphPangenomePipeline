import logging
import sys
import tomllib
import subprocess
from pathlib import Path


class CactusRunner:
    """
    Minigraph-Cactus runner
    Use Cactus to assembly pangenome graph
    """
    def __init__(self, config_path: str):
        with open(config_path, "rb") as f:
            self.config = tomllib.load(f)
        # config include seqFile path and jobStore path
        self.Cactus: dict = self.config['Cactus']
        # work directory path
        self.Global: dict = self.config['Global']
        # set cactus output file format
        self.CactusOutFormat:  dict = self.config['CactusOutFormat']

    def generate_cactus_dir(self) -> Path:
        """
        create cactus work dir path
        :return: cactus_path
        """
        work_dir = Path(self.Global['work_dir']).resolve()
        cactus_dir = work_dir / "1.cactus"

        return cactus_dir

    def _cactus_command(self) -> list:
        """
        generate run command
        cactus jobStore will use the new directory which created by generate_cactus_dir
        :return: cmd
        """
        # use generate_cactus_dir object to create cactus directory
        cactus_dir = self.generate_cactus_dir()

        cactus_dir.mkdir(parents=True, exist_ok=True)
        cactus_job_store = cactus_dir / "jobStore"

        cmd = [
            "cactus-pangenome",
            str(cactus_job_store),
            str(self.Cactus['seqFile']),
            "--outDir", str(cactus_dir),
            "--outName", str(self.Global['filePrefix']),
            "--maxCores", str(self.Cactus['maxCores']),
            '--reference', str(self.Cactus['reference']),
        ]

        if self.CactusOutFormat.get('vcf'): cmd.append('--vcf')
        if self.CactusOutFormat.get('gfa'): cmd.append('--gfa')
        if self.CactusOutFormat.get('gbz'): cmd.append('--gbz')
        singularity_image = self.Cactus['singularityImage']
        if singularity_image:
            logging.info(f"Using Singularity image: {singularity_image}")
            prefix_cmd = ["singularity", "exec", str(singularity_image)]
            cmd = prefix_cmd + cmd
        return cmd

    def run_cactus(self) -> None:
        """
        run cactus
        :return:
        """
        if not Path(self.Cactus['seqFile']).exists():
            logging.error(f"seqFile can not found: {self.Cactus['seqFile']}! Cactus need a seqFile to build graph "
                          f"pangenome.")
            sys.exit(1)

        cactus_cmd = self._cactus_command()
        logging.info(f"Start running cactus-pangenome: {' '.join(cactus_cmd)}")

        try:
            subprocess.run(cactus_cmd, capture_output=False, check=True, text=True)
            logging.info(f"cactus-pangenome finished")
        except subprocess.CalledProcessError as e:
            logging.error(f"cactus-pangenome error: {e.returncode}")
            sys.exit(1)

if __name__ == '__main__':
    cactus_run_code = CactusRunner('../config/config.toml')
    cactus_run_code.run_cactus()