#!/usr/bin/env python3
"""
German Legal Dataset Preparation for LLM Fine-tuning
Comprehensive data pipeline for downloading, processing, and formatting German legal texts
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
from huggingface_hub import hf_hub_download
from tqdm import tqdm
import pdfplumber
from langdetect import detect
import spacy

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class GermanLegalDataProcessor:
    """Main class for processing German legal datasets"""
    
    def __init__(self, output_dir: str = "./prepared_data/"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Create subdirectories
        self.data_sources_dir = Path("./data_sources/")
        self.data_sources_dir.mkdir(exist_ok=True)
        
        # Legal reference patterns
        self.legal_ref_patterns = [
            (r'§\s*(\d+[a-z]?)\s+(BGB|StGB|ZPO|GG|AO|HGB|VVG|InsO|SGB)', r'{LAW_REF_\2_\1}'),
            (r'Art\.\s*(\d+[a-z]?)\s+(GG|EMRK|EU-Vertrag)', r'{ART_REF_\2_\1}'),
            (r'(\d+)\s+([A-Z][a-zA-Z]+)\s+(\d{4})', r'{COURT_REF_\2_\1_\3}'),  # Court decisions
        ]
        
        # PII patterns
        self.pii_patterns = [
            (r'\b[A-ZÄÖÜÞ][a-zäöüßþ]+\s+[A-ZÄÖÜÞ][a-zäöüßþ]+\b', '{NAME}'),  # Names
            (r'\b\d{5}\s+[A-ZÄÖÜÞ][a-zäöüßþ]+\b', '{CITY}'),  # Cities with postal codes
            (r'\b\d{2}\.\d{2}\.\d{4}\b', '{DATE}'),  # Dates
            (r'\b\d+\s*€\b', '{AMOUNT}'),  # Monetary amounts
        ]
        
    def download_huggingface_datasets(self) -> Dict[str, Any]:
        """Download datasets from HuggingFace Hub"""
        logger.info("Downloading HuggingFace datasets...")
        datasets = {}
        
        try:
            # German Legal Sentences
            logger.info("Loading German Legal Sentences dataset...")
            german_legal = load_dataset("lexucab/german_legal_sentences", split="train")
            datasets['german_legal_sentences'] = german_legal
            logger.info(f"Loaded {len(german_legal)} German legal sentences")
            
            # Multi-EURLEX (German subset)
            logger.info("Loading Multi-EURLEX dataset...")
            multi_eurlex = load_dataset("multi_eurlex", "de", split="train")
            datasets['multi_eurlex'] = multi_eurlex
            logger.info(f"Loaded {len(multi_eurlex)} Multi-EURLEX documents")
            
        except Exception as e:
            logger.error(f"Error downloading HuggingFace datasets: {e}")
            
        return datasets
    
    def scrape_gesetze_im_internet(self, max_laws: int = 100) -> List[Dict[str, str]]:
        """Scrape German laws from gesetze-im-internet.de"""
        logger.info("Scraping Gesetze im Internet...")
        base_url = "https://www.gesetze-im-internet.de"
        scraped_laws = []
        
        try:
            # Get list of laws
            response = requests.get(f"{base_url}/aktuell.html", timeout=30)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            law_links = soup.find_all('a', href=re.compile(r'/[a-z]+/'))[:max_laws]
            
            for link in tqdm(law_links, desc="Scraping laws"):
                try:
                    law_url = urljoin(base_url, link.get('href'))
                    law_response = requests.get(law_url, timeout=30)
                    law_soup = BeautifulSoup(law_response.content, 'html.parser')
                    
                    # Extract law title and content
                    title_elem = law_soup.find('h1') or law_soup.find('title')
                    title = title_elem.get_text().strip() if title_elem else "Unknown Law"
                    
                    # Extract paragraphs
                    content_divs = law_soup.find_all('div', class_=['jurAbsatz', 'jnhtml'])
                    content = '\n\n'.join([div.get_text().strip() for div in content_divs if div.get_text().strip()])
                    
                    if content:
                        scraped_laws.append({
                            'title': title,
                            'content': content,
                            'source': 'gesetze_im_internet',
                            'url': law_url
                        })
                    
                    time.sleep(1)  # Be respectful to the server
                    
                except Exception as e:
                    logger.warning(f"Error scraping law {link.get('href')}: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error scraping Gesetze im Internet: {e}")
            
        logger.info(f"Scraped {len(scraped_laws)} laws from Gesetze im Internet")
        return scraped_laws
    
    def scrape_rechtsprechung_im_internet(self, max_decisions: int = 100) -> List[Dict[str, str]]:
        """Scrape court decisions from rechtsprechung-im-internet.de"""
        logger.info("Scraping Rechtsprechung im Internet...")
        base_url = "https://www.rechtsprechung-im-internet.de"
        scraped_decisions = []
        
        try:
            # Navigate through different courts and years
            courts = ['bgh', 'bag', 'bverwg', 'bfh', 'bsg']  # Major German courts
            
            for court in courts[:2]:  # Limit to avoid overwhelming
                try:
                    court_url = f"{base_url}/{court}/"
                    response = requests.get(court_url, timeout=30)
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # Find decision links
                    decision_links = soup.find_all('a', href=re.compile(r'\.html$'))[:max_decisions//len(courts)]
                    
                    for link in tqdm(decision_links, desc=f"Scraping {court.upper()} decisions"):
                        try:
                            decision_url = urljoin(court_url, link.get('href'))
                            decision_response = requests.get(decision_url, timeout=30)
                            decision_soup = BeautifulSoup(decision_response.content, 'html.parser')
                            
                            # Extract decision content
                            title_elem = decision_soup.find('h1') or decision_soup.find('title')
                            title = title_elem.get_text().strip() if title_elem else "Unknown Decision"
                            
                            # Extract decision text
                            content_divs = decision_soup.find_all('div', class_=['absatz', 'urteilstext'])
                            content = '\n\n'.join([div.get_text().strip() for div in content_divs if div.get_text().strip()])
                            
                            if content:
                                scraped_decisions.append({
                                    'title': title,
                                    'content': content,
                                    'court': court.upper(),
                                    'source': 'rechtsprechung_im_internet',
                                    'url': decision_url
                                })
                            
                            time.sleep(1)
                            
                        except Exception as e:
                            logger.warning(f"Error scraping decision {link.get('href')}: {e}")
                            continue
                            
                except Exception as e:
                    logger.warning(f"Error scraping court {court}: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error scraping Rechtsprechung im Internet: {e}")
            
        logger.info(f"Scraped {len(scraped_decisions)} court decisions")
        return scraped_decisions
    
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
        
        # Standardize legal references
        for pattern, replacement in self.legal_ref_patterns:
            text = re.sub(pattern, replacement, text)
            
        # Replace PII with placeholders
        for pattern, replacement in self.pii_patterns:
            text = re.sub(pattern, replacement, text)
            
        return text.strip()
    
    def create_instruction_pairs(self, data: Dict[str, Any]) -> List[Dict[str, str]]:
        """Create instruction-tuned prompt-completion pairs"""
        logger.info("Creating instruction-tuned pairs...")
        pairs = []
        
        # Process different data sources
        for source, items in data.items():
            if source == 'german_legal_sentences':
                # Create question-answering pairs
                for item in items:
                    if 'text' in item and len(item['text']) > 100:
                        text = self.clean_and_normalize_text(item['text'])
                        
                        # Create summarization task
                        pairs.append({
                            'prompt': 'Fasse den folgenden Rechtstext zusammen:',
                            'completion': text[:500] + '...' if len(text) > 500 else text,
                            'source': source
                        })
                        
                        # Create explanation task
                        if len(text) > 200:
                            pairs.append({
                                'prompt': 'Erkläre die rechtlichen Grundlagen in diesem Text:',
                                'completion': text,
                                'source': source
                            })
            
            elif source == 'multi_eurlex':
                # Process EU legal documents
                for item in items:
                    if 'text' in item and 'labels' in item:
                        text = self.clean_and_normalize_text(item['text'])
                        
                        pairs.append({
                            'prompt': 'Analysiere dieses EU-Rechtsdokument:',
                            'completion': text[:800] + '...' if len(text) > 800 else text,
                            'source': source
                        })
            
            elif isinstance(items, list):
                # Process scraped data
                for item in items:
                    if 'content' in item:
                        content = self.clean_and_normalize_text(item['content'])
                        title = item.get('title', 'Rechtsdokument')
                        
                        if len(content) > 100:
                            # Create various instruction types
                            instruction_types = [
                                ('Erkläre den Inhalt dieses Gesetzes:', content[:600]),
                                ('Was sind die wichtigsten Punkte in diesem Rechtstext?', content[:500]),
                                ('Fasse diesen Rechtstext zusammen:', content[:400]),
                            ]
                            
                            for prompt, completion in instruction_types:
                                if completion.strip():
                                    pairs.append({
                                        'prompt': prompt,
                                        'completion': completion.strip(),
                                        'source': source,
                                        'title': title
                                    })
        
        logger.info(f"Created {len(pairs)} instruction pairs")
        return pairs
    
    def format_for_instruction_tuning(self, pairs: List[Dict[str, str]]) -> List[str]:
        """Format pairs for instruction tuning with special tokens"""
        formatted_data = []
        
        for pair in pairs:
            formatted_text = f"<s>[INST] {pair['prompt']} [/INST] {pair['completion']} </s>"
            formatted_data.append(formatted_text)
            
        return formatted_data
    
    def split_and_export_data(self, formatted_data: List[str]) -> None:
        """Split data and export as JSONL files"""
        logger.info("Splitting and exporting data...")
        
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
            'domain': 'legal'
        }
        
        with open(self.output_dir / 'metadata.json', 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
    
    def run_full_pipeline(self) -> None:
        """Execute the complete data preparation pipeline"""
        logger.info("Starting German Legal Dataset preparation pipeline...")
        
        # Step 1: Download HuggingFace datasets
        hf_datasets = self.download_huggingface_datasets()
        
        # Step 2: Scrape websites
        scraped_laws = self.scrape_gesetze_im_internet(max_laws=50)
        scraped_decisions = self.scrape_rechtsprechung_im_internet(max_decisions=50)
        
        # Step 3: Combine all data
        all_data = hf_datasets.copy()
        all_data['scraped_laws'] = scraped_laws
        all_data['scraped_decisions'] = scraped_decisions
        
        # Step 4: Create instruction pairs
        instruction_pairs = self.create_instruction_pairs(all_data)
        
        # Step 5: Format for instruction tuning
        formatted_data = self.format_for_instruction_tuning(instruction_pairs)
        
        # Step 6: Split and export
        self.split_and_export_data(formatted_data)
        
        logger.info("Data preparation pipeline completed successfully!")

if __name__ == "__main__":
    processor = GermanLegalDataProcessor()
    processor.run_full_pipeline()