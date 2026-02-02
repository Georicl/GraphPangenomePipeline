import tomllib


class CactusRunner:
    """
    Minigraph-Cactus runner
    Use Cactus to assembly pangenome graph
    """
    def __init__(self, config_path: str):
        with open(config_path, "rb") as f:
            self.config = tomllib.load(f)

        self.cactus_cfg = self.config['cactus']
