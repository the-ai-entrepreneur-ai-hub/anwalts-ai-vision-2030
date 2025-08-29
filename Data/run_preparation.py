#!/usr/bin/env python3
"""
Main runner for German Legal Dataset preparation
Execute this script to run the complete data preparation pipeline
"""

import sys
import os
from pathlib import Path

# Add scripts directory to path
sys.path.append(str(Path(__file__).parent / "scripts"))

from data_preparation import GermanLegalDataProcessor

def main():
    """Main execution function"""
    print("German Legal Dataset Preparation Pipeline")
    print("=" * 50)
    
    # Initialize processor
    processor = GermanLegalDataProcessor(output_dir="./prepared_data/")
    
    try:
        # Run complete pipeline
        processor.run_full_pipeline()
        
        print("\nPipeline completed successfully!")
        print("\nGenerated files:")
        print("- ./prepared_data/train.jsonl")
        print("- ./prepared_data/validation.jsonl") 
        print("- ./prepared_data/test.jsonl")
        print("- ./prepared_data/metadata.json")
        
    except Exception as e:
        print(f"\nPipeline failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()