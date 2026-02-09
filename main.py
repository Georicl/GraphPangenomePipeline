import logging
import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.logging import RichHandler

from src.run_minicactus import CactusRunner
from src.vg_stats_index import VgIndexStats
from src.annotation_pangenome import AnnotationRunner
from src.vg_wgs import VgWgsRunner
from src.vg_call import CallVariantRunner

# Initializing Typer and Rich Console
app = typer.Typer(
    help="Graph Pangenome Analysis Pipeline: Assembly, Annotation, Genotyping, and Beyond.",
    rich_markup_mode="rich",
    add_completion=False,
)
console = Console()

def setup_logging():
    """Set up logging with Rich for better visuals."""
    # We use force=True to override any previously configured logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(rich_tracebacks=True, console=console)],
        force=True
    )

def validate_config(config: str) -> Path:
    """Validate if the config file exists."""
    config_path = Path(config)
    if not config_path.exists():
        console.print(f"[bold red]Error:[/bold red] Config file not found: [yellow]{config}[/yellow]")
        raise typer.Exit(code=1)
    return config_path

@app.command()
def run(
    config: str = typer.Option(..., "--config", "-c", help="Path to the config.toml file"),
    cactus: bool = typer.Option(False, "--cactus", help="Run minigraph-cactus module"),
    vg: bool = typer.Option(False, "--vg", help="Run vg stats and index module"),
    annotation: bool = typer.Option(False, "--annotation", help="Run annotation module"),
    wgs: bool = typer.Option(False, "--wgs", help="Run vg wgs pipeline"),
    call: bool = typer.Option(False, "--call", help="Run vg call variant module"),
    all: bool = typer.Option(False, "--all", help="Run the full pipeline (Cactus -> VG -> Annotation -> WGS -> Call)"),
):
    """
    Run the pipeline steps based on the provided configuration.
    """
    setup_logging()
    config_path = validate_config(config)
    
    # Logic to determine which modules to run
    run_cactus = cactus or all
    run_vg = vg or all
    run_anno = annotation or all
    run_wgs = wgs or all
    run_call = call or all

    if not any([run_cactus, run_vg, run_anno, run_wgs, run_call]):
        console.print("[yellow]No modules selected. Use --help to see available options.[/yellow]")
        raise typer.Exit()

    # 1. Cactus Module
    if run_cactus:
        logging.info("[bold cyan]>>> Starting Step 1: Cactus Pangenome Construction[/bold cyan]")
        CactusRunner(str(config_path)).run_cactus()

    # 2. VG Stats & Indexing
    if run_vg:
        logging.info("[bold cyan]>>> Starting Step 2: VG Stats and Indexing[/bold cyan]")
        VgIndexStats(str(config_path)).run_vg_index_stats()

    # 3. Annotation
    if run_anno:
        logging.info("[bold cyan]>>> Starting Step 3: Annotation[/bold cyan]")
        AnnotationRunner(str(config_path)).run_annotation()

    # 4. WGS Mapping
    if run_wgs:
        logging.info("[bold cyan]>>> Starting Step 4: WGS Pipeline[/bold cyan]")
        VgWgsRunner(str(config_path)).run_wgs()

    # 5. Variant Calling
    if run_call:
        logging.info("[bold cyan]>>> Starting Step 5: Variant Calling[/bold cyan]")
        CallVariantRunner(str(config_path)).run_vg_call()

    console.print("\n[bold green]Pipeline execution finished successfully![/bold green] :rocket:")

@app.command()
def check(
    config: Optional[str] = typer.Option(None, "--config", "-c", help="Check config file and environment")
):
    """
    [Future Work] Check the environment and configuration validity.
    """
    console.print("[yellow]Environment check module is under development...[/yellow]")

if __name__ == "__main__":
    app()
