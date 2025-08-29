#!/usr/bin/env python3
"""
Export Final Dataset to Multiple Formats
Convert the massive German legal dataset to various training formats
"""

import json
import pandas as pd
from pathlib import Path
import logging
from datasets import Dataset
import csv

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def export_to_multiple_formats():
    """Export dataset to multiple formats for different training frameworks"""
    
    source_dir = Path("massive_legal_data")
    export_dir = Path("exported_datasets")
    export_dir.mkdir(exist_ok=True)
    
    # Load all data
    all_data = []
    splits = {}
    
    for split_name in ['train', 'validation', 'test']:
        file_path = source_dir / f"{split_name}.jsonl"
        split_data = []
        
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                data = json.loads(line.strip())
                split_data.append(data)
                all_data.append(data)
        
        splits[split_name] = split_data
        logger.info(f"Loaded {len(split_data)} examples from {split_name}")
    
    # 1. Export as Parquet files (HuggingFace/Pandas compatible)
    logger.info("Exporting to Parquet format...")
    parquet_dir = export_dir / "parquet"
    parquet_dir.mkdir(exist_ok=True)
    
    for split_name, split_data in splits.items():
        df = pd.DataFrame(split_data)
        parquet_path = parquet_dir / f"{split_name}.parquet"
        df.to_parquet(parquet_path, index=False)
        logger.info(f"Exported {split_name} to {parquet_path}")
    
    # 2. Export as CSV files
    logger.info("Exporting to CSV format...")
    csv_dir = export_dir / "csv"
    csv_dir.mkdir(exist_ok=True)
    
    for split_name, split_data in splits.items():
        df = pd.DataFrame(split_data)
        csv_path = csv_dir / f"{split_name}.csv"
        df.to_csv(csv_path, index=False, encoding='utf-8')
        logger.info(f"Exported {split_name} to {csv_path}")
    
    # 3. Export as HuggingFace Dataset format
    logger.info("Exporting to HuggingFace Dataset format...")
    hf_dir = export_dir / "huggingface"
    hf_dir.mkdir(exist_ok=True)
    
    for split_name, split_data in splits.items():
        dataset = Dataset.from_list(split_data)
        dataset.save_to_disk(str(hf_dir / split_name))
        logger.info(f"Exported {split_name} to HuggingFace format")
    
    # 4. Export as plain text format (for basic training)
    logger.info("Exporting to plain text format...")
    text_dir = export_dir / "text"  
    text_dir.mkdir(exist_ok=True)
    
    for split_name, split_data in splits.items():
        text_path = text_dir / f"{split_name}.txt"
        with open(text_path, 'w', encoding='utf-8') as f:
            for item in split_data:
                f.write(item['text'] + '\n')
        logger.info(f"Exported {split_name} to {text_path}")
    
    # 5. Export combined dataset
    logger.info("Creating combined dataset...")
    combined_df = pd.DataFrame(all_data)
    combined_df.to_parquet(export_dir / "combined_dataset.parquet", index=False)
    combined_df.to_csv(export_dir / "combined_dataset.csv", index=False, encoding='utf-8')
    
    # 6. Create dataset info file
    dataset_info = {
        'name': 'German Legal Training Dataset',
        'description': 'Comprehensive German legal dataset for instruction tuning',
        'total_samples': len(all_data),
        'splits': {name: len(data) for name, data in splits.items()},
        'language': 'German',
        'domain': 'Legal',
        'format': 'Instruction tuning',
        'created': '2025-08-05',
        'categories': list(set(item.get('category', 'unknown') for item in all_data)),
        'instruction_types': list(set(item.get('instruction_type', 'unknown') for item in all_data if 'instruction_type' in item)),
        'legal_domains': [
            'Bürgerliches Recht (Civil Law)',
            'Strafrecht (Criminal Law)', 
            'Verfassungsrecht (Constitutional Law)',
            'Verwaltungsrecht (Administrative Law)',
            'Arbeitsrecht (Labor Law)'
        ],
        'export_formats': {
            'jsonl': 'Original format in massive_legal_data/',
            'parquet': 'Pandas/HuggingFace compatible in exported_datasets/parquet/',
            'csv': 'Standard CSV format in exported_datasets/csv/',
            'huggingface': 'HuggingFace Dataset format in exported_datasets/huggingface/',
            'text': 'Plain text format in exported_datasets/text/',
            'combined': 'Single file formats: combined_dataset.parquet, combined_dataset.csv'
        },
        'usage_examples': {
            'pandas': 'df = pd.read_parquet("exported_datasets/parquet/train.parquet")',
            'huggingface': 'from datasets import load_from_disk; dataset = load_from_disk("exported_datasets/huggingface/train")',
            'transformers': 'Use with any transformer library for German legal AI training'
        }
    }
    
    with open(export_dir / 'dataset_info.json', 'w', encoding='utf-8') as f:
        json.dump(dataset_info, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Dataset export complete! Total: {len(all_data)} examples exported to multiple formats")
    return len(all_data)

if __name__ == "__main__":
    export_to_multiple_formats()