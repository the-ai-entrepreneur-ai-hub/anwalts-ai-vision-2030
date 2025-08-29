#!/usr/bin/env python3
"""
Enhanced runner for German Legal Dataset preparation
Uses improved data processing with sample data fallback
"""

import sys
import os
from pathlib import Path

# Add scripts directory to path
sys.path.append(str(Path(__file__).parent / "scripts"))

from enhanced_data_preparation import EnhancedGermanLegalDataProcessor

def main():
    """Main execution function"""
    print("Enhanced German Legal Dataset Preparation Pipeline")
    print("=" * 55)
    
    # Initialize enhanced processor
    processor = EnhancedGermanLegalDataProcessor(output_dir="./prepared_data/")
    
    try:
        # Run enhanced pipeline
        processor.run_enhanced_pipeline()
        
        print("\nPipeline completed successfully!")
        print("\nGenerated files:")
        print("- ./prepared_data/train.jsonl")
        print("- ./prepared_data/validation.jsonl") 
        print("- ./prepared_data/test.jsonl")
        print("- ./prepared_data/metadata.json")
        
        # Show file sizes and sample counts
        metadata_path = Path("./prepared_data/metadata.json")
        if metadata_path.exists():
            import json
            with open(metadata_path, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            
            print(f"\nDataset Statistics:")
            print(f"- Total samples: {metadata['total_samples']}")
            print(f"- Training samples: {metadata['splits']['train']}")
            print(f"- Validation samples: {metadata['splits']['validation']}")
            print(f"- Test samples: {metadata['splits']['test']}")
            
    except Exception as e:
        print(f"\nPipeline failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()