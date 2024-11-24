import os
import pandas as pd
import subprocess
from pathlib import Path

class CutAndTagHeatmap:
    def __init__(self, output_dir, window_size=5000, bin_size=50):
        """
        Initialize Cut&Tag heatmap generator
        
        Parameters:
        -----------
        output_dir : str
            Directory for output files
        window_size : int
            Size of the window around reference points (default: 5000 bp)
        bin_size : int
            Size of bins for computing coverage (default: 50 bp)
        """
        self.output_dir = Path(output_dir)
        self.window_size = window_size
        self.bin_size = bin_size
        
        # Define paths based on previous pipeline structure
        self.bigwig_dir = Path("results/bigwig")
        self.consensus_dir = Path("results/consensus_peaks")
        
        # Create output directory if it doesn't exist
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    def get_bigwig_files(self):
        """
        Get bigwig files generated by merge_replicates script
        Returns dictionary of condition_tissue: bigwig_path
        """
        bigwig_files = {}
        conditions = ["Exogenous", "Endogenous"]
        tissues = ["Neuron", "NSC"]
        
        for condition in conditions:
            for tissue in tissues:
                bw_file = self.bigwig_dir / f"{condition}_{tissue}.bw"
                if bw_file.exists():
                    bigwig_files[f"{condition}_{tissue}"] = str(bw_file)
        
        # Add control
        control_bw = self.bigwig_dir / "Control_IgG.bw"
        if control_bw.exists():
            bigwig_files["Control"] = str(control_bw)
            
        return bigwig_files
    
    def get_tss_regions(self, genome_gtf):
        """
        Extract TSS regions from genome annotation
        """
        tss_file = self.output_dir / "tss_regions.bed"
        
        # Read GTF file and extract TSS regions
        df = pd.read_csv(genome_gtf, sep='\t', comment='#', header=None,
                        names=['chrom', 'source', 'feature', 'start', 'end', 
                              'score', 'strand', 'frame', 'attributes'])
        
        # Filter for genes
        genes = df[df['feature'] == 'gene']
        
        # Extract TSS based on strand
        tss = genes.copy()
        tss.loc[tss['strand'] == '+', 'end'] = tss['start']  # Forward strand TSS
        tss.loc[tss['strand'] == '-', 'start'] = tss['end']  # Reverse strand TSS
        
        # Create 1bp TSS regions and extend by 1bp (required for deepTools)
        tss['start'] = tss['start'] - 1
        
        # Extract gene names from attributes
        tss['name'] = tss['attributes'].str.extract('gene_name "([^"]+)"')
        
        # Select and order columns for BED format
        tss_bed = tss[['chrom', 'start', 'end', 'name', 'score', 'strand']]
        
        # Sort by chromosome and position
        tss_bed = tss_bed.sort_values(['chrom', 'start'])
        
        # Write to file
        tss_bed.to_csv(tss_file, sep='\t', header=False, index=False)
        
        return tss_file
    
    def compute_matrix(self, tss_file, bigwig_files):
        """
        Compute matrix of Cut&Tag signal around TSS
        """
        matrix_file = self.output_dir / "tss_matrix.gz"
        
        # Prepare bigwig files list
        bw_list = " ".join(bigwig_files.values())
        sample_labels = " ".join(bigwig_files.keys())
        
        # Build computeMatrix command
        cmd = f"""
        computeMatrix reference-point \
            --referencePoint TSS \
            --scoreFileName {bw_list} \
            --regionsFileName {tss_file} \
            --beforeRegionStartLength {self.window_size//2} \
            --afterRegionStartLength {self.window_size//2} \
            --binSize {self.bin_size} \
            --skipZeros \
            --missingDataAsZero \
            --samplesLabel {sample_labels} \
            -o {matrix_file}
        """
        
        # Run command
        subprocess.run(cmd, shell=True, check=True)
        
        return matrix_file
    
    def plot_heatmap(self, matrix_file):
        """
        Generate heatmap plot from computed matrix
        """
        heatmap_file = self.output_dir / "tss_heatmap.pdf"
        
        # Build plotHeatmap command
        cmd = f"""
        plotHeatmap \
            -m {matrix_file} \
            -o {heatmap_file} \
            --colorMap Blues \
            --whatToShow 'heatmap and colorbar' \
            --heatmapHeight 15 \
            --heatmapWidth 8 \
            --xAxisLabel "Distance from TSS (bp)" \
            --refPointLabel "TSS" \
            --legendLocation upper-right \
            --sortRegions descend \
            --sortUsing mean \
            --averageTypeSummaryPlot mean
        """
        
        # Run command
        subprocess.run(cmd, shell=True, check=True)
        
        return heatmap_file
    
    def generate_heatmap(self, genome_gtf):
        """
        Main method to generate heatmap
        """
        print("Getting bigwig files...")
        bigwig_files = self.get_bigwig_files()
        
        print("Extracting TSS regions...")
        tss_file = self.get_tss_regions(genome_gtf)
        
        print("Computing signal matrix...")
        matrix = self.compute_matrix(tss_file, bigwig_files)
        
        print("Generating heatmap...")
        heatmap = self.plot_heatmap(matrix)
        
        print(f"Heatmap generated: {heatmap}")
        return heatmap

# Example usage
if __name__ == "__main__":
    # Initialize and run analysis
    heatmap_generator = CutAndTagHeatmap(
        output_dir="results/heatmaps",
        window_size=10000,  # 10kb window
        bin_size=50       # 50bp bins
    )
    
    # Generate heatmap using genome GTF file
    heatmap_generator.generate_heatmap(genome_gtf="/beegfs/scratch/ric.broccoli/kubacki.michal/SRF_CUTandTAG/gencode.vM10.annotation.gtf")