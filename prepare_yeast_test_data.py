import urllib.request
from pathlib import Path
import gzip

def download_and_save(url, destination):
    """download text dataset"""
    try:
        print(f"Downloading {url} to {destination}")
        urllib.request.urlretrieve(url, destination)
        print(f"Saved successfully: {destination}")
    except Exception as e:
        print(f"Failed to download {url}: {e}")

def filter_gff(input_gz, output_gz, chrom_id):
    """Filter GFF3 for a specific chromosome"""
    print(f"Filtering {input_gz} for {chrom_id} -> {output_gz}")
    with gzip.open(input_gz, 'rt') as f_in, gzip.open(output_gz, 'wt') as f_out:
        for line in f_in:
            if line.startswith('#'):
                # Keep headers, but might want to filter ##sequence-region if strict
                if line.startswith('##sequence-region'):
                    if chrom_id in line:
                        f_out.write(line)
                else:
                    f_out.write(line)
            else:
                cols = line.split('\t')
                if len(cols) > 0 and cols[0] == chrom_id:
                    f_out.write(line)
    print("Filtering complete.")

def prepare_real_yeast_test():
    base_dir = Path("test/data")
    genome_dir = base_dir / "genomes"
    read_dir = base_dir / "reads"

    for d in [genome_dir, read_dir]:
        d.mkdir(parents=True, exist_ok=True)

    sources = {
        "ref_fa": "https://ftp.ncbi.nlm.nih.gov/genomes/refseq/fungi/Saccharomyces_cerevisiae/latest_assembly_versions/GCF_000146045.2_R64/GCF_000146045.2_R64_assembly_structure/Primary_Assembly/assembled_chromosomes/FASTA/chrI.fna.gz",
        "ref_gff": "https://ftp.ncbi.nlm.nih.gov/genomes/refseq/fungi/Saccharomyces_cerevisiae/latest_assembly_versions/GCF_000146045.2_R64/GCF_000146045.2_R64_genomic.gff.gz",
        "I118_fa": "https://ftp.ncbi.nlm.nih.gov/genomes/all/GCA/054/130/705/GCA_054130705.1_ASM5413070v1/GCA_054130705.1_ASM5413070v1_assembly_structure/Primary_Assembly/assembled_chromosomes/FASTA/chrI.fna.gz",
        "imx2600_fa": "https://ftp.ncbi.nlm.nih.gov/genomes/all/GCA/030/292/175/GCA_030292175.1_ASM3029217v1/GCA_030292175.1_ASM3029217v1_assembly_structure/Primary_Assembly/assembled_chromosomes/FASTA/chrI.fna.gz",
        "wgs_r1": "https://ftp.sra.ebi.ac.uk/vol1/fastq/SRR365/095/SRR36559295/SRR36559295_subreads.fastq.gz"
    }

    print(">>> Downloading Genomes and Annotation...")
    download_and_save(sources["ref_fa"], genome_dir / "s288c_chrI.fa.gz")
    
    full_gff = genome_dir / "s288c.gff3.gz"
    download_and_save(sources["ref_gff"], full_gff)
    
    # Filter for chrI (NC_001133.9)
    filter_gff(full_gff, genome_dir / "s288c_chrI.gff3.gz", "NC_001133.9")

    download_and_save(sources["I118_fa"], genome_dir / "I118_chrI.fa.gz")
    download_and_save(sources["imx2600_fa"], genome_dir / "IMX2600_chrI.fa.gz")

    print(">>> Downloading full WGS data...")
    download_and_save(sources["wgs_r1"], read_dir / "test_sample_R1.fq.gz")

    # generate seqfile
    with open(base_dir / "seqfile", "w") as f:
        f.write(f"s288c\t{genome_dir.absolute()}/s288c_chrI.fa.gz\n")
        f.write(f"I118\t{genome_dir.absolute()}/I118_chrI.fa.gz\n")
        f.write(f"IMX2600\t{genome_dir.absolute()}/IMX2600_chrI.fa.gz\n")

if __name__ == "__main__":
    prepare_real_yeast_test()
