import logging
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.logging import RichHandler

from src.run_minicactus import CactusRunner
from src.vg_stats import VgIndexStats
from src.annotation_pangenome import AnnotationRunner
from src.vg_wgs import VgWgsRunner
from src.vg_call import CallVariantRunner
from src.config_loader import ConfigManager

# Initializing Typer and Rich Console
app = typer.Typer(
    help="""Graph Pangenome Analysis Pipeline:
    
    [bold cyan]Assembly, Annotation, Genotyping, and Beyond.[/bold cyan]
    
    [bold black]Author: Yang Xiang[/bold black]
    """,
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

@app.command()
def run(
    config_file: Optional[str] = typer.Option(
        None, "--config", "-c", 
        help="Path to a custom config.toml file. If not provided, 'config/config.toml' will be used by default.",
        rich_help_panel="Base Configuration",
        show_default=False
    ),
    # Execution Modules
    cactus: bool = typer.Option(False, "--cactus", help="Run minigraph-cactus module", rich_help_panel="Execution Modules"),
    vg: bool = typer.Option(False, "--vg", help="Run vg stats and index module", rich_help_panel="Execution Modules"),
    annotation: bool = typer.Option(False, "--annotation", help="Run annotation module", rich_help_panel="Execution Modules"),
    wgs: bool = typer.Option(False, "--wgs", help="Run vg wgs pipeline", rich_help_panel="Execution Modules"),
    call: bool = typer.Option(False, "--call", help="Run vg call variant module", rich_help_panel="Execution Modules"),
    all: bool = typer.Option(False, "--all", help="Run the full pipeline", rich_help_panel="Execution Modules"),
    
    # [Global] Overrides
    work_dir: Optional[str] = typer.Option(None, "--work-dir", help="Work directory", rich_help_panel="Global Settings"),
    prefix: Optional[str] = typer.Option(None, "--prefix", help="File prefix for outputs", rich_help_panel="Global Settings"),

    # [Cactus] Overrides
    cactus_seq: Optional[str] = typer.Option(None, "--cactus-seq", help="Cactus seqFile path", rich_help_panel="Cactus Pangenome Settings"),
    cactus_ref: Optional[str] = typer.Option(None, "--cactus-ref", help="Cactus reference genome name", rich_help_panel="Cactus Pangenome Settings"),
    cactus_cores: Optional[int] = typer.Option(None, "--cactus-cores", help="Max cores for Cactus", rich_help_panel="Cactus Pangenome Settings"),
    cactus_image: Optional[str] = typer.Option(None, "--cactus-image", help="Singularity image for Cactus", rich_help_panel="Cactus Pangenome Settings"),

    # [VgIndex] Overrides
    vg_threads: Optional[int] = typer.Option(None, "--vg-threads", help="Threads for VG indexing", rich_help_panel="VG Indexing Settings"),
    
    # [Annotation] Overrides
    anno_gff: Optional[str] = typer.Option(None, "--anno-gff", help="GFF3 file for annotation", rich_help_panel="Annotation Settings"),
    anno_source: Optional[str] = typer.Option(None, "--anno-source", help="Source genome for annotation", rich_help_panel="Annotation Settings"),
    anno_image: Optional[str] = typer.Option(None, "--anno-image", help="Singularity image for Grannot", rich_help_panel="Annotation Settings"),

    # [wgs] Overrides
    wgs_data: Optional[str] = typer.Option(None, "--wgs-data", help="DataTable CSV for WGS", rich_help_panel="WGS Mapping Settings"),
    wgs_threads: Optional[int] = typer.Option(None, "--wgs-threads", help="Threads per sample in WGS", rich_help_panel="WGS Mapping Settings"),
    wgs_parallel: Optional[int] = typer.Option(None, "--wgs-parallel", help="Parallel samples in WGS", rich_help_panel="WGS Mapping Settings"),

    # [call] Overrides
    call_threads: Optional[int] = typer.Option(None, "--call-threads", help="Threads per sample in variant calling", rich_help_panel="Variant Calling Settings"),
    call_parallel: Optional[int] = typer.Option(None, "--call-parallel", help="Parallel samples in variant calling", rich_help_panel="Variant Calling Settings"),
):
    """
    Run the pipeline. Parameters provided via CLI will override those in the config file.
    """
    setup_logging()
    
    # Determine config path: provided or default (relative to script location)
    if config_file:
        actual_config_path = Path(config_file)
    else:
        # Default to 'config/config.toml' relative to this script's directory
        actual_config_path = Path(__file__).parent / "config" / "config.toml"
    
    # Initialize ConfigManager with config file (if exists)
    config_mgr = ConfigManager(str(actual_config_path) if actual_config_path.exists() else None)
    
    # Construct override dictionary based on flattened CLI arguments
    overrides = {
        "Global": {},
        "Cactus": {},
        "VgIndex": {},
        "Annotation": {},
        "wgs": {},
        "call": {},
    }
    
    # Mapping CLI to Dict
    if work_dir: overrides["Global"]["work_dir"] = work_dir
    if prefix: overrides["Global"]["filePrefix"] = prefix
    
    if cactus_seq: overrides["Cactus"]["seqFile"] = cactus_seq
    if cactus_ref: overrides["Cactus"]["reference"] = cactus_ref
    if cactus_cores: overrides["Cactus"]["maxCores"] = cactus_cores
    if cactus_image: overrides["Cactus"]["singularityImage"] = cactus_image
    
    if vg_threads: overrides["VgIndex"]["threads"] = vg_threads
    
    if anno_gff: overrides["Annotation"]["gff3"] = anno_gff
    if anno_source: overrides["Annotation"]["SourceGenome"] = anno_source
    if anno_image: overrides["Annotation"]["singularityImage"] = anno_image
    
    if wgs_data: overrides["wgs"]["DataTable"] = wgs_data
    if wgs_threads: overrides["wgs"]["Threads"] = wgs_threads
    if wgs_parallel: overrides["wgs"]["Parallel_job"] = wgs_parallel

    if call_threads: overrides["call"]["Threads"] = call_threads
    if call_parallel: overrides["call"]["Parallel_job"] = call_parallel

    # Clean empty sections in overrides
    overrides = {k: v for k, v in overrides.items() if v}
    
    if overrides:
        config_mgr.update_config(overrides)
    
    config = config_mgr.get_config()
    
    # Logic to determine which modules to run
    run_modules = {
        "cactus": cactus or all,
        "vg": vg or all,
        "annotation": annotation or all,
        "wgs": wgs or all,
        "call": call or all,
    }

    if not any(run_modules.values()):
        console.print("[yellow]No modules selected. Use --help to see available options.[/yellow]")
        raise typer.Exit()

    # Basic validation before running
    try:
        config_mgr.validate(run_modules)
    except ValueError as e:
        console.print(f"[bold red]Config Error:[/bold red] {e}")
        raise typer.Exit(1)
    
    # 1. Cactus Module
    if run_modules["cactus"]:
        logging.info("[bold cyan]>>> Starting Step 1: Cactus Pangenome Construction[/bold cyan]")
        CactusRunner(config).run_cactus()

    # 2. VG Stats & Indexing
    if run_modules["vg"]:
        logging.info("[bold cyan]>>> Starting Step 2: VG Stats and Indexing[/bold cyan]")
        VgIndexStats(config).run_vg_index_stats()

    # 3. Annotation
    if run_modules["annotation"]:
        logging.info("[bold cyan]>>> Starting Step 3: Annotation[/bold cyan]")
        AnnotationRunner(config).run_annotation()

    # 4. WGS Mapping
    if run_modules["wgs"]:
        logging.info("[bold cyan]>>> Starting Step 4: WGS Pipeline[/bold cyan]")
        VgWgsRunner(config).run_wgs()

    # 5. Variant Calling
    if run_modules["call"]:
        logging.info("[bold cyan]>>> Starting Step 5: Variant Calling[/bold cyan]")
        CallVariantRunner(config).run_vg_call()

    console.print("\n[bold green]Pipeline execution finished successfully![/bold green] :rocket:")

@app.command()
def check(
    config_file: Optional[str] = typer.Option(
        None, "--config", "-c", 
        help="Path to a custom config.toml file to check.",
        rich_help_panel="Base Configuration",
        show_default=False
    )
):
    """
    Check the environment and configuration validity.
    """
    setup_logging()
    
    # Determine config path
    if config_file:
        actual_config_path = Path(config_file)
    else:
        actual_config_path = Path(__file__).parent / "config" / "config.toml"
    
    console.print(f"[bold cyan]Checking configuration file:[/bold cyan] {actual_config_path}")
    
    if not actual_config_path.exists():
        console.print(f"[bold red]Error:[/bold red] Config file not found at {actual_config_path}")
        raise typer.Exit(1)
        
    try:
        config_mgr = ConfigManager(str(actual_config_path))
        config = config_mgr.get_config()
        console.print("[green]✓ Configuration loaded and merged successfully.[/green]")
        
        # Check for required tools
        tools = ["cactus-pangenome", "vg", "grannot", "singularity"]
        console.print("\n[bold cyan]Checking for required tools in PATH:[/bold cyan]")
        for tool in tools:
            import shutil
            path = shutil.which(tool)
            if path:
                console.print(f"[green]✓ {tool:20}[/green] found at {path}")
            else:
                console.print(f"[yellow]! {tool:20}[/yellow] [bold yellow]not found[/bold yellow] (ensure it is in your PATH or provided via singularity)")
        
        console.print("\n[bold green]Configuration check completed.[/bold green]")
        
    except Exception as e:
        console.print(f"[bold red]Error during check:[/bold red] {e}")
        raise typer.Exit(1)

if __name__ == "__main__":
    app()
