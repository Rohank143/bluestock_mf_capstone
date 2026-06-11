"""
Module: run_pipeline.py
Description: Master execution script for the Bluestock MF Capstone pipeline.
Orchestrates ETL, Data Cleaning, Analytics, EDA notebook generation, 
and final report/presentation generation.
"""

import subprocess
import logging
import sys
import os
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

BASE_DIR = Path(__file__).resolve().parent

def run_script(script_path):
    """Utility function to run a python script as a subprocess."""
    full_path = BASE_DIR / script_path
    if not full_path.exists():
        logging.error(f"Script not found: {full_path}")
        return False
        
    logging.info(f"--- Starting: {script_path} ---")
    try:
        # Use sys.executable to ensure we use the same Python interpreter
        result = subprocess.run([sys.executable, str(full_path)], check=True, text=True, capture_output=True)
        logging.info(f"--- Completed successfully: {script_path} ---")
        return True
    except subprocess.CalledProcessError as e:
        logging.error(f"--- Failed: {script_path} ---")
        logging.error(f"Exit code: {e.returncode}")
        logging.error(f"Error output:\n{e.stderr}")
        return False

def main():
    """Main function to run the full pipeline."""
    logging.info("========================================")
    logging.info("Starting Full Bluestock MF Pipeline")
    logging.info("========================================")

    # 1. Pipeline Execution Steps
    # Note: These paths are relative to the project root
    scripts_to_run = [
        "scripts/etl_pipeline.py",
        "scripts/02_data_cleaning.py",
        "scripts/run_analytics.py",
        "create_eda_nb.py",
        "compute_metrics.py",
        "scripts/generate_final_report.py",
        "scripts/generate_presentation.py"
    ]

    for script in scripts_to_run:
        success = run_script(script)
        if not success:
            logging.critical(f"Pipeline halted due to failure in {script}")
            sys.exit(1)

    logging.info("========================================")
    logging.info("Pipeline Execution Finished Successfully")
    logging.info("========================================")

if __name__ == "__main__":
    main()
