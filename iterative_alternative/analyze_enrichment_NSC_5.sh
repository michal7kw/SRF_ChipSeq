#!/bin/bash
#SBATCH --job-name=analyze_enrichment_NSC_separate_RNA_integration_3
#SBATCH --account=kubacki.michal
#SBATCH --mem=128GB
#SBATCH --time=24:00:00
#SBATCH --nodes=1
#SBATCH --ntasks=16
#SBATCH --mail-type=ALL
#SBATCH --exclusive
#SBATCH --mail-user=kubacki.michal@hsr.it
#SBATCH --error="logs/analyze_enrichment_NSC_5.err"
#SBATCH --output="logs/analyze_enrichment_NSC_5.out"

cd /beegfs/scratch/ric.broccoli/kubacki.michal/SRF_CUTandTAG/iterative_alternative

source /opt/common/tools/ric.cosr/miniconda3/bin/activate
conda activate snakemake

# Create logs directory if it doesn't exist
mkdir -p logs

# Run the script with working directory argument and full error traceback
python -u ../scripts/analyze_enrichment_NSC_separate_RNA_integration_3.py \
    --working-dir /beegfs/scratch/ric.broccoli/kubacki.michal/SRF_CUTandTAG/iterative_alternative \
    --data-dir /beegfs/scratch/ric.broccoli/kubacki.michal/SRF_CUTandTAG/iterative_alternative/results \
    --results-dir /beegfs/scratch/ric.broccoli/kubacki.michal/SRF_CUTandTAG/iterative_alternative/results_separate_RNA_integration_3 \
    2>&1 | tee "logs/analyze_enrichment_NSC_5.out"
