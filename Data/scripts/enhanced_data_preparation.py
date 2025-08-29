#!/usr/bin/env python3
"""
Enhanced German Legal Dataset Preparation for LLM Fine-tuning
Improved version with better data sources and error handling
"""

import os
import json
import re
import logging
import random
from pathlib import Path
from typing import List, Dict, Tuple, Any
from urllib.parse import urljoin, urlparse
import time

import requests
from bs4 import BeautifulSoup
import pandas as pd
from datasets import load_dataset, Dataset
from tqdm import tqdm

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class EnhancedGermanLegalDataProcessor:
    """Enhanced German Legal Dataset Processor with better data sources"""
    
    def __init__(self, output_dir: str = "./prepared_data/"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Create subdirectories
        self.data_sources_dir = Path("./data_sources/")
        self.data_sources_dir.mkdir(exist_ok=True)
        
        # Headers for web scraping
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
    def create_sample_legal_data(self) -> List[Dict[str, str]]:
        """Create sample German legal data for demonstration"""
        logger.info("Creating sample German legal data...")
        
        sample_data = [
            {
                'title': 'Bürgerliches Gesetzbuch - Allgemeiner Teil',
                'content': '''Das Bürgerliche Gesetzbuch regelt die Rechtsbeziehungen zwischen Privatpersonen. 
                § 1 BGB besagt, dass die Rechtsfähigkeit des Menschen mit der Vollendung der Geburt beginnt. 
                § 104 BGB definiert die Geschäftsunfähigkeit: Geschäftsunfähig ist, wer nicht das siebente Lebensjahr vollendet hat oder sich in einem die freie Willensbestimmung ausschließenden Zustand krankhafter Störung der Geistestätigkeit befindet.
                § 105 BGB regelt die Nichtigkeit der Willenserklärung eines Geschäftsunfähigen.''',
                'source': 'sample_bgb',
                'category': 'civil_law'
            },
            {
                'title': 'Strafgesetzbuch - Allgemeine Bestimmungen',
                'content': '''Das Strafgesetzbuch enthält die grundlegenden Straftatbestände.
                § 15 StGB behandelt den Vorsatz: Strafbar ist nur vorsätzliches Handeln, wenn nicht das Gesetz fahrlässiges Handeln ausdrücklich mit Strafe bedroht.
                § 16 StGB regelt den Tatbestandsirrtum: Wer bei Begehung der Tat einen Umstand nicht kennt, der zum gesetzlichen Tatbestand gehört, handelt nicht vorsätzlich.
                § 17 StGB behandelt den Verbotsirrtum: Fehlt dem Täter bei Begehung der Tat die Einsicht, Unrecht zu tun, so handelt er ohne Schuld, wenn er diesen Irrtum nicht vermeiden konnte.''',
                'source': 'sample_stgb',
                'category': 'criminal_law'
            },
            {
                'title': 'Grundgesetz - Grundrechte',
                'content': '''Das Grundgesetz gewährleistet fundamentale Rechte.
                Art. 1 GG: Die Würde des Menschen ist unantastbar. Sie zu achten und zu schützen ist Verpflichtung aller staatlichen Gewalt.
                Art. 2 GG: Jeder hat das Recht auf die freie Entfaltung seiner Persönlichkeit, soweit er nicht die Rechte anderer verletzt.
                Art. 3 GG: Alle Menschen sind vor dem Gesetz gleich. Männer und Frauen sind gleichberechtigt.''',
                'source': 'sample_gg',
                'category': 'constitutional_law'
            },
            {
                'title': 'Arbeitsrecht - Kündigungsschutz',
                'content': '''Das Kündigungsschutzgesetz schützt Arbeitnehmer vor ungerechtfertigten Kündigungen.
                § 1 KSchG: Die Kündigung des Arbeitsverhältnisses gegenüber einem Arbeitnehmer ist rechtsunwirksam, wenn sie sozial ungerechtfertigt ist.
                Eine Kündigung ist sozial ungerechtfertigt, wenn sie nicht durch Gründe bedingt ist, die in der Person oder in dem Verhalten des Arbeitnehmers liegen oder durch dringende betriebliche Erfordernisse.''',
                'source': 'sample_kschg',
                'category': 'labor_law'
            },
            {
                'title': 'Mietrecht - Mieterhöhung',
                'content': '''Das Mietrecht ist im BGB geregelt und schützt sowohl Mieter als auch Vermieter.
                § 558 BGB: Der Vermieter kann die Zustimmung zu einer Erhöhung der Miete bis zur ortsüblichen Vergleichsmiete verlangen.
                § 559 BGB: Eine Mieterhöhung nach § 558 ist nur zulässig, wenn die Miete seit 15 Monaten unverändert und seit der letzten Mieterhöhung mindestens ein Jahr verstrichen ist.
                Die Miete darf innerhalb von drei Jahren nicht um mehr als 20 Prozent erhöht werden.''',
                'source': 'sample_mietrecht',
                'category': 'housing_law'
            },
            {
                'title': 'Kaufvertragsrecht - Gewährleistung',
                'content': '''Das Kaufvertragsrecht regelt die Rechte und Pflichten beim Kauf.
                § 437 BGB: Ist die Sache mangelhaft, kann der Käufer Nacherfüllung verlangen, vom Vertrag zurücktreten oder den Kaufpreis mindern und unter den Voraussetzungen des § 440 Schadensersatz verlangen.
                § 438 BGB: Die Gewährleistungsansprüche verjähren in zwei Jahren ab dem Zeitpunkt, in dem die Sache übergeben wurde.
                Bei Bauwerken beträgt die Verjährungsfrist fünf Jahre.''',
                'source': 'sample_kaufrecht',
                'category': 'contract_law'
            }
        ]
        
        logger.info(f"Created {len(sample_data)} sample legal documents")
        return sample_data
    
    def try_download_alternative_datasets(self) -> Dict[str, Any]:
        """Try alternative dataset sources"""
        logger.info("Trying alternative German legal datasets...")
        datasets = {}
        
        # Try different dataset names
        alternative_datasets = [
            'joelito/legal_german_gpt',
            'malteos/legal-german',
            'german_legal_entity_recognition',
            'jphme/german_legal_ner'
        ]
        
        for dataset_name in alternative_datasets:
            try:
                logger.info(f"Attempting to load {dataset_name}...")
                dataset = load_dataset(dataset_name, split='train')
                datasets[dataset_name] = dataset
                logger.info(f"Successfully loaded {dataset_name} with {len(dataset)} samples")
                break  # Use first successful dataset
            except Exception as e:
                logger.warning(f"Could not load {dataset_name}: {e}")
                continue
        
        # If no datasets work, use sample data
        if not datasets:
            logger.info("Using sample legal data as fallback")
            sample_data = self.create_sample_legal_data()
            datasets['sample_legal_data'] = sample_data
            
        return datasets
    
    def clean_and_normalize_text(self, text: str) -> str:
        """Clean and normalize German legal text"""
        if not text:
            return ""
            
        # Remove extra whitespace and normalize line breaks
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'\n\s*\n', '\n\n', text)
        
        # Remove common headers and footers
        text = re.sub(r'^.*?Aktenzeichen:.*?\n', '', text, flags=re.MULTILINE)
        text = re.sub(r'Seite \d+ von \d+', '', text)
        text = re.sub(r'www\..*?\.de', '', text)
        
        # Standardize legal references - keep original for now
        legal_ref_patterns = [
            (r'§\s*(\d+[a-z]?)\s+(BGB|StGB|ZPO|GG|AO|HGB|VVG|InsO|SGB)', r'§ \1 \2'),
            (r'Art\.\s*(\d+[a-z]?)\s+(GG|EMRK)', r'Art. \1 \2'),
        ]
        
        for pattern, replacement in legal_ref_patterns:
            text = re.sub(pattern, replacement, text)
            
        # Replace common PII patterns
        pii_patterns = [
            (r'\b[A-ZÄÖÜÞ][a-zäöüßþ]+\s+[A-ZÄÖÜÞ][a-zäöüßþ]+\b', '{NAME}'),
            (r'\b\d{5}\s+[A-ZÄÖÜÞ][a-zäöüßþ]+\b', '{CITY}'),
            (r'\b\d{2}\.\d{2}\.\d{4}\b', '{DATE}'),
            (r'\b\d+\s*€\b', '{AMOUNT}'),
        ]
        
        for pattern, replacement in pii_patterns:
            text = re.sub(pattern, replacement, text)
            
        return text.strip()
    
    def create_instruction_pairs(self, data: Dict[str, Any]) -> List[Dict[str, str]]:
        """Create instruction-tuned prompt-completion pairs from legal data"""
        logger.info("Creating instruction-tuned pairs...")
        pairs = []
        
        # Define instruction templates
        instruction_templates = [
            ('Erkläre den Inhalt dieses Rechtstextes:', 'explanation'),
            ('Fasse den folgenden Rechtstext zusammen:', 'summary'),
            ('Was sind die wichtigsten Punkte in diesem Gesetz?', 'key_points'),
            ('Welche rechtlichen Grundlagen werden hier behandelt?', 'legal_basis'),
            ('Erkläre die Bedeutung dieser Rechtsvorschrift:', 'interpretation'),
            ('Was regelt dieser Paragraph?', 'regulation'),
        ]
        
        for source, items in data.items():
            logger.info(f"Processing {source}...")
            
            if isinstance(items, list):
                # Handle sample data format
                for item in items:
                    if 'content' in item:
                        content = self.clean_and_normalize_text(item['content'])
                        title = item.get('title', 'Rechtsdokument')
                        
                        if len(content) > 50:
                            # Create multiple instruction types for each document
                            for prompt_template, task_type in instruction_templates:
                                # Create appropriate completion based on task type
                                if task_type == 'summary':
                                    completion = content[:400] + '...' if len(content) > 400 else content
                                elif task_type == 'key_points':
                                    # Extract key points from content
                                    sentences = content.split('.')
                                    key_points = [s.strip() + '.' for s in sentences[:3] if s.strip()]
                                    completion = ' '.join(key_points)
                                else:
                                    completion = content[:500] + '...' if len(content) > 500 else content
                                
                                pairs.append({
                                    'prompt': prompt_template,
                                    'completion': completion.strip(),
                                    'source': source,
                                    'title': title,
                                    'task_type': task_type
                                })
            else:
                # Handle HuggingFace dataset format
                try:
                    for item in items:
                        if 'text' in item:
                            text = self.clean_and_normalize_text(item['text'])
                            if len(text) > 50:
                                pairs.append({
                                    'prompt': 'Erkläre diesen Rechtstext:',
                                    'completion': text[:600] + '...' if len(text) > 600 else text,
                                    'source': source
                                })
                except Exception as e:
                    logger.warning(f"Error processing {source}: {e}")
        
        logger.info(f"Created {len(pairs)} instruction pairs")
        return pairs
    
    def format_for_instruction_tuning(self, pairs: List[Dict[str, str]]) -> List[str]:
        """Format pairs for instruction tuning with special tokens"""
        formatted_data = []
        
        for pair in pairs:
            # Use the standard instruction tuning format
            formatted_text = f"<s>[INST] {pair['prompt']} [/INST] {pair['completion']} </s>"
            formatted_data.append(formatted_text)
            
        return formatted_data
    
    def split_and_export_data(self, formatted_data: List[str]) -> None:
        """Split data and export as JSONL files"""
        logger.info("Splitting and exporting data...")
        
        if not formatted_data:
            logger.warning("No data to export")
            return
        
        # Shuffle data
        random.shuffle(formatted_data)
        
        # Calculate split sizes
        total_size = len(formatted_data)
        train_size = int(0.8 * total_size)
        val_size = int(0.1 * total_size)
        
        # Split data
        train_data = formatted_data[:train_size]
        val_data = formatted_data[train_size:train_size + val_size]
        test_data = formatted_data[train_size + val_size:]
        
        # Export as JSONL
        datasets = {
            'train': train_data,
            'validation': val_data,
            'test': test_data
        }
        
        for split_name, split_data in datasets.items():
            output_file = self.output_dir / f"{split_name}.jsonl"
            
            with open(output_file, 'w', encoding='utf-8') as f:
                for text in split_data:
                    json.dump({'text': text}, f, ensure_ascii=False)
                    f.write('\n')
                    
            logger.info(f"Exported {len(split_data)} samples to {output_file}")
        
        # Export metadata
        metadata = {
            'total_samples': total_size,
            'splits': {
                'train': len(train_data),
                'validation': len(val_data),
                'test': len(test_data)
            },
            'format': 'instruction_tuning',
            'language': 'german',
            'domain': 'legal',
            'template': '<s>[INST] {prompt} [/INST] {completion} </s>',
            'description': 'German legal dataset prepared for instruction tuning'
        }
        
        with open(self.output_dir / 'metadata.json', 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
            
        logger.info(f"Exported metadata to {self.output_dir / 'metadata.json'}")
    
    def run_enhanced_pipeline(self) -> None:
        """Execute the enhanced data preparation pipeline"""
        logger.info("Starting Enhanced German Legal Dataset preparation pipeline...")
        
        # Step 1: Try to download datasets or use sample data
        datasets = self.try_download_alternative_datasets()
        
        # Step 2: Create instruction pairs
        instruction_pairs = self.create_instruction_pairs(datasets)
        
        # Step 3: Format for instruction tuning
        formatted_data = self.format_for_instruction_tuning(instruction_pairs)
        
        # Step 4: Split and export
        self.split_and_export_data(formatted_data)
        
        logger.info("Enhanced data preparation pipeline completed successfully!")

if __name__ == "__main__":
    processor = EnhancedGermanLegalDataProcessor()
    processor.run_enhanced_pipeline()