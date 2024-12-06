#!/bin/bash
#SBATCH --job-name=qc_metrics
#SBATCH --account=kubacki.michal
#SBATCH --mem=16GB
#SBATCH --time=4:00:00
#SBATCH --nodes=1
#SBATCH --ntasks=8
#SBATCH --ntasks-per-node=8
#SBATCH --mail-type=ALL
#SBATCH --mail-user=kubacki.michal@hsr.it
#SBATCH --error="logs/qc_%a.err"
#SBATCH --output="logs/qc_%a.out"
#SBATCH --array=0-11

# Set working directory
cd /beegfs/scratch/ric.broccoli/kubacki.michal/SRF_CUTandTAG/iterative_alternative
source /opt/common/tools/ric.cosr/miniconda3/bin/activate /beegfs/scratch/ric.broccoli/kubacki.michal/conda_envs/snakemake

# Get sample names
EXOGENOUS_SAMPLES=($(ls ../DATA/EXOGENOUS/*_R1_001.fastq.gz | xargs -n 1 basename | sed 's/_R1_001.fastq.gz//'))
ENDOGENOUS_SAMPLES=($(ls ../DATA/ENDOGENOUS/*_R1_001.fastq.gz | xargs -n 1 basename | sed 's/_R1_001.fastq.gz//'))
ALL_SAMPLES=("${EXOGENOUS_SAMPLES[@]}" "${ENDOGENOUS_SAMPLES[@]}")

# Get current sample
SAMPLE=${ALL_SAMPLES[$SLURM_ARRAY_TASK_ID]}

# Create output directories
mkdir -p results/qc/tss_enrichment

# 3. TSS enrichment (requires TSS bed file)
if [ -s "../DATA/mm10_TSS.bed" ]; then
    computeMatrix reference-point \
        --referencePoint TSS \
        -b 2000 -a 2000 \
        -R ../DATA/mm10_TSS.bed \
        -S results/bigwig/${SAMPLE}.bw \
        --skipZeros \
        --numberOfProcessors 8 \
        -o results/qc/tss_enrichment/${SAMPLE}_matrix.gz

    # Only attempt to create profile plot if matrix was generated successfully
    if [ -f "results/qc/tss_enrichment/${SAMPLE}_matrix.gz" ]; then
        plotProfile \
            -m results/qc/tss_enrichment/${SAMPLE}_matrix.gz \
            -o results/qc/tss_enrichment/${SAMPLE}_profile.png \
            --plotTitle "${SAMPLE} TSS Enrichment" \
            --averageType mean
    else
        echo "Warning: Matrix file was not generated for ${SAMPLE}"
    fi
else
    echo "Error: TSS bed file is missing or empty at ../DATA/mm10_TSS.bed"
fi