import argparse
import csv
import logging
import re
from pathlib import Path

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

def generate_datatable(input_dir: str, outfile: str):
    input_path = Path(input_dir).resolve()
    if not input_path.exists():
        logging.error(f"Input directory does not exist: {input_dir}")
        return

    # Regular expressions for file matching
    # Paired-end R1: {SampleID}_1_clean.fq.gz
    # Paired-end R2: {SampleID}_2_clean.fq.gz
    r1_pattern = re.compile(r"(.+)_1_clean\.fq\.gz$")
    r2_pattern = re.compile(r"(.+)_2_clean\.fq\.gz$")
    
    # Common sequencing file suffixes (used for single-end identification)
    fq_suffixes = {".fq.gz", ".fastq.gz", ".fq", ".fastq"}

    samples = {}  # {SampleID: {'SampleID': str, 'R1': str, 'R2': str}}
    all_files = sorted(list(input_path.rglob("*")))
    
    used_files = set()

    # Phase 1: Identify paired-end files
    logging.info("Searching for paired-end files...")
    for file_path in all_files:
        if file_path.is_dir():
            continue
            
        name = file_path.name
        match_r1 = r1_pattern.match(name)
        
        if match_r1:
            sample_id = match_r1.group(1)
            # Construct expected R2 filename
            r2_name = name.replace("_1_clean.fq.gz", "_2_clean.fq.gz")
            r2_path = file_path.parent / r2_name
            
            if r2_path.exists():
                samples[sample_id] = {
                    'SampleID': sample_id,
                    'R1': str(file_path.resolve()),
                    'R2': str(r2_path.resolve())
                }
                used_files.add(file_path)
                used_files.add(r2_path)
                logging.info(f"Found PE sample: {sample_id}")
            else:
                # Found R1 without corresponding R2, treat as single-end
                samples[sample_id] = {
                    'SampleID': sample_id,
                    'R1': str(file_path.resolve()),
                    'R2': ''
                }
                used_files.add(file_path)
                logging.warning(f"Found orphan R1 (treating as SE): {sample_id}")

    # Phase 2: Identify single-end files (excluding already identified PE files)
    logging.info("Searching for single-end files...")
    for file_path in all_files:
        if file_path.is_dir() or file_path in used_files:
            continue
            
        # Check if the file has a sequencing suffix
        is_fq = any(file_path.name.endswith(suffix) for suffix in fq_suffixes)
        if is_fq:
            # Simple SE logic: remove all known suffixes to get SampleID
            sample_id = file_path.name
            for suffix in sorted(list(fq_suffixes) + [".clean"], key=len, reverse=True):
                if sample_id.endswith(suffix):
                    sample_id = sample_id[:-len(suffix)]
            
            if sample_id not in samples:
                samples[sample_id] = {
                    'SampleID': sample_id,
                    'R1': str(file_path.resolve()),
                    'R2': ''
                }
                used_files.add(file_path)
                logging.info(f"Found SE sample: {sample_id}")

    # Write to CSV
    if not samples:
        logging.warning("No sequencing files found.")
        return

    output_path = Path(outfile).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['SampleID', 'R1', 'R2'])
        writer.writeheader()
        for sid in sorted(samples.keys()):
            writer.writerow(samples[sid])
            
    logging.info(f"Successfully generated DataTable: {output_path}")
    logging.info(f"Total samples found: {len(samples)}")

def main():
    setup_logging()
    parser = argparse.ArgumentParser(description="Generate DataTable CSV for vg_wgs module.")
    parser.add_argument("directory", type=str, help="Directory to search for FASTQ files (recursive)")
    parser.add_argument("--outfile", type=str, default="wgs_datatable.csv", help="Path to output CSV file (default: wgs_datatable.csv)")
    
    args = parser.parse_args()
    generate_datatable(args.directory, args.outfile)

if __name__ == "__main__":
    main()