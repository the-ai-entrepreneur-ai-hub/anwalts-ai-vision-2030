#!/usr/bin/env python3
"""
Advanced German Legal Data Expansion System
Multi-source approach with synthetic augmentation and quality control
"""

import json
import re
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
import hashlib
import random
from datasets import load_dataset, Dataset
import pandas as pd
import requests
from urllib.parse import quote
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AdvancedLegalDataExpander:
    """Advanced system for expanding German legal datasets"""
    
    def __init__(self, input_dir: str = "prepared_data", output_dir: str = "expanded_legal_data"):
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.collected_hashes = set()
        self.lock = threading.Lock()
        
        # Alternative German legal datasets
        self.alternative_datasets = [
            {
                'name': 'multi_legal_pile',
                'subset': 'german',
                'config': 'german'
            },
            {
                'name': 'legal_pile_lexglue',
                'subset': 'german',
                'config': None
            }
        ]
        
        # German legal text patterns for synthetic generation
        self.legal_patterns = {
            'contract_clauses': [
                "Der Auftragnehmer verpflichtet sich zur",
                "Gemäß § {} BGB ist festzustellen, dass",
                "Die Vertragsparteien vereinbaren hiermit",
                "Im Falle einer Vertragsverletzung gilt",
                "Der Vertrag tritt mit Unterzeichnung in Kraft"
            ],
            'court_decisions': [
                "Das Gericht entscheidet wie folgt:",
                "Nach Würdigung aller Umstände ist festzustellen",
                "Die Revision wird zurückgewiesen, weil",
                "Das Landgericht hat richtig erkannt",
                "Die Berufung ist begründet"
            ],
            'legal_analysis': [
                "Nach der ständigen Rechtsprechung des BGH",
                "Die herrschende Meinung in der Literatur",
                "Systematisch ist zu beachten, dass",
                "Der Wortlaut des Gesetzes besagt",
                "Teleologisch betrachtet ergibt sich"
            ]
        }
        
        # Instruction templates for data augmentation
        self.instruction_templates = [
            "Erklären Sie den folgenden deutschen Rechtstext:",
            "Fassen Sie diese Rechtsvorschrift zusammen:",
            "Welche rechtlichen Konsequenzen ergeben sich aus:",
            "Analysieren Sie die Bedeutung von:",
            "Was regelt dieser Paragraph?",
            "Interpretieren Sie den folgenden Gesetzestext:",
            "Welche Rechte und Pflichten entstehen durch:",
            "Erläutern Sie die praktische Anwendung von:",
            "Was bedeutet dieser juristische Begriff:",
            "Wie ist diese Rechtsnorm zu verstehen?"
        ]
    
    def calculate_hash(self, content: str) -> str:
        """Calculate SHA-256 hash for deduplication"""
        return hashlib.sha256(content.encode('utf-8')).hexdigest()
    
    def is_duplicate(self, content: str) -> bool:
        """Thread-safe duplicate checking"""
        content_hash = self.calculate_hash(content)
        with self.lock:
            if content_hash in self.collected_hashes:
                return True
            self.collected_hashes.add(content_hash)
            return False
    
    def load_existing_data(self) -> List[Dict[str, Any]]:
        """Load existing training data"""
        existing_data = []
        
        # Load from prepared_data directory
        for file_path in ['train.jsonl', 'validation.jsonl', 'test.jsonl']:
            full_path = self.input_dir / file_path
            if full_path.exists():
                logger.info(f"Loading existing data from {file_path}")
                with open(full_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        try:
                            data = json.loads(line.strip())
                            existing_data.append(data)
                        except json.JSONDecodeError:
                            continue
        
        logger.info(f"Loaded {len(existing_data)} existing examples")
        return existing_data
    
    def search_alternative_datasets(self) -> List[Dict[str, Any]]:
        """Search for alternative legal datasets"""
        all_data = []
        
        # Try to load German legal datasets from HuggingFace
        legal_datasets = [
            'joelniklaus/lextreme',
            'joelniklaus/MultiLegalPile', 
            'joelniklaus/legal_case_document_summarization',
            'microsoft/legal_pile',
            'pile-of-law/pile-of-law'
        ]
        
        for dataset_name in legal_datasets:
            try:
                logger.info(f"Attempting to load {dataset_name}")
                
                # Try different configurations
                configurations = [None, 'train', 'german', 'de']
                
                for config in configurations:
                    try:
                        if config:
                            dataset = load_dataset(dataset_name, config, split='train', streaming=True)
                        else:
                            dataset = load_dataset(dataset_name, split='train', streaming=True)
                        
                        # Process up to 1000 examples per dataset
                        count = 0
                        for example in dataset:
                            if count >= 1000:
                                break
                                
                            # Extract German text content
                            content = self.extract_german_content(example)
                            if content and len(content) > 100:
                                if not self.is_duplicate(content):
                                    all_data.append({
                                        'text': content,
                                        'source': f'huggingface_{dataset_name}',
                                        'category': 'legal_corpus'
                                    })
                                    count += 1
                        
                        logger.info(f"Loaded {count} examples from {dataset_name} (config: {config})")
                        break  # Success, don't try other configs
                        
                    except Exception as e:
                        logger.debug(f"Config {config} failed for {dataset_name}: {e}")
                        continue
                        
            except Exception as e:
                logger.warning(f"Failed to load {dataset_name}: {e}")
                continue
        
        return all_data
    
    def extract_german_content(self, example: Dict[str, Any]) -> Optional[str]:
        """Extract German content from dataset example"""
        # Common text fields
        text_fields = ['text', 'content', 'document', 'case_text', 'judgment', 'opinion', 'input', 'target']
        
        for field in text_fields:
            if field in example and example[field]:
                content = str(example[field])
                
                # Check if content is likely German
                if self.is_likely_german(content) and len(content) > 100:
                    return self.clean_text(content)
        
        return None
    
    def is_likely_german(self, text: str) -> bool:
        """Check if text is likely German"""
        # German indicators
        german_indicators = [
            'der', 'die', 'das', 'und', 'oder', 'mit', 'von', 'zu', 'im', 'am',
            'ist', 'sind', 'wird', 'werden', 'haben', 'hat', 'sein', 'eine', 'einen',
            'recht', 'gesetz', 'paragraph', 'artikel', 'bgb', 'stgb', 'gg',
            'gericht', 'richter', 'urteil', 'entscheidung', 'klage'
        ]
        
        # German umlauts
        german_chars = ['ä', 'ö', 'ü', 'ß', 'Ä', 'Ö', 'Ü']
        
        text_lower = text.lower()
        
        # Count German indicators
        indicator_count = sum(1 for indicator in german_indicators if indicator in text_lower)
        char_count = sum(1 for char in german_chars if char in text)
        
        # Simple heuristic
        return indicator_count > 3 or char_count > 0
    
    def clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', text)
        # Keep German characters and basic punctuation
        text = re.sub(r'[^\w\säöüÄÖÜß.,;:!?()"-]', '', text)
        return text.strip()
    
    def generate_synthetic_variations(self, existing_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate synthetic variations of existing data"""
        synthetic_data = []
        
        logger.info("Generating synthetic variations...")
        
        for item in existing_data[:100]:  # Limit to avoid too much synthetic data
            original_text = item.get('text', '')
            
            if len(original_text) > 200:
                # Create different instruction formats
                variations = self.create_instruction_variations(original_text)
                synthetic_data.extend(variations)
        
        # Generate completely synthetic legal examples
        synthetic_legal = self.generate_synthetic_legal_texts(500)
        synthetic_data.extend(synthetic_legal)
        
        logger.info(f"Generated {len(synthetic_data)} synthetic examples")
        return synthetic_data
    
    def create_instruction_variations(self, text: str) -> List[Dict[str, Any]]:
        """Create different instruction-following formats from text"""
        variations = []
        
        # Truncate text for instruction format
        text_excerpt = text[:800] + "..." if len(text) > 800 else text
        
        # Create 3 random instruction variations
        selected_templates = random.sample(self.instruction_templates, min(3, len(self.instruction_templates)))
        
        for template in selected_templates:
            instruction_text = f"<s>[INST] {template} [/INST] {text_excerpt} </s>"
            
            if not self.is_duplicate(instruction_text):
                variations.append({
                    'text': instruction_text,
                    'source': 'synthetic_instruction',
                    'category': 'instruction_following'
                })
        
        return variations
    
    def generate_synthetic_legal_texts(self, count: int) -> List[Dict[str, Any]]:
        """Generate completely synthetic legal texts"""
        synthetic_texts = []
        
        paragraph_numbers = [str(i) for i in range(1, 1000)]
        
        for i in range(count):
            # Choose random pattern type
            pattern_type = random.choice(list(self.legal_patterns.keys()))
            patterns = self.legal_patterns[pattern_type]
            
            # Generate synthetic text
            base_pattern = random.choice(patterns)
            
            # Fill in paragraph numbers where needed
            if '{}' in base_pattern:
                paragraph = random.choice(paragraph_numbers)
                base_pattern = base_pattern.format(paragraph)
            
            # Add random legal content
            legal_content = self.generate_legal_content()
            full_text = f"{base_pattern} {legal_content}"
            
            # Create instruction format
            instruction = random.choice(self.instruction_templates)
            synthetic_text = f"<s>[INST] {instruction} [/INST] {full_text} </s>"
            
            if not self.is_duplicate(synthetic_text):
                synthetic_texts.append({
                    'text': synthetic_text,
                    'source': 'synthetic_generated',
                    'category': pattern_type
                })
        
        return synthetic_texts
    
    def generate_legal_content(self) -> str:
        """Generate random legal content"""
        legal_terms = [
            "Vertragspartner", "Rechtsprechung", "Gesetzeslage", "Rechtsnorm",
            "Rechtsfolge", "Anspruchsgrundlage", "Schadensersatz", "Erfüllung",
            "Leistungsstörung", "Gewährleistung", "Haftung", "Verjährung"
        ]
        
        # Generate 2-4 sentences
        sentences = []
        for _ in range(random.randint(2, 4)):
            terms = random.sample(legal_terms, random.randint(1, 3))
            sentence = f"Die {terms[0]} betrifft die rechtliche Bewertung der Situation."
            if len(terms) > 1:
                sentence += f" Dabei ist die {terms[1]} zu berücksichtigen."
            sentences.append(sentence)
        
        return " ".join(sentences)
    
    def apply_quality_filtering(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Apply quality filtering to the data"""
        filtered_data = []
        
        for item in data:
            text = item.get('text', '')
            
            # Quality criteria
            if (len(text) > 50 and  # Minimum length
                len(text) < 8000 and  # Maximum length
                not self.is_duplicate(text) and  # No duplicates
                self.contains_legal_content(text)):  # Legal relevance
                
                filtered_data.append(item)
        
        logger.info(f"Quality filtering: {len(data)} -> {len(filtered_data)} examples")
        return filtered_data
    
    def contains_legal_content(self, text: str) -> bool:
        """Check if text contains legal content"""
        legal_keywords = [
            'recht', 'gesetz', 'paragraph', 'artikel', 'bgb', 'stgb', 'gg',
            'gericht', 'richter', 'urteil', 'vertrag', 'anspruch', 'haftung',
            'schadensersatz', 'klage', 'revision', 'berufung', 'instanz'
        ]
        
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in legal_keywords)
    
    def save_expanded_dataset(self, data: List[Dict[str, Any]]):
        """Save the expanded dataset in multiple formats"""
        # Shuffle data
        random.shuffle(data)
        
        # Create splits
        total = len(data)
        train_size = int(0.8 * total)
        val_size = int(0.1 * total)
        
        train_data = data[:train_size]
        val_data = data[train_size:train_size + val_size]
        test_data = data[train_size + val_size:]
        
        # Save splits
        splits = {
            'train': train_data,
            'validation': val_data,
            'test': test_data
        }
        
        for split_name, split_data in splits.items():
            # Save as JSONL
            jsonl_path = self.output_dir / f"{split_name}.jsonl"
            with open(jsonl_path, 'w', encoding='utf-8') as f:
                for item in split_data:
                    json.dump(item, f, ensure_ascii=False)
                    f.write('\n')
            
            # Save as Parquet
            df = pd.DataFrame(split_data)
            parquet_path = self.output_dir / f"{split_name}.parquet"
            df.to_parquet(parquet_path, index=False)
            
            logger.info(f"Saved {len(split_data)} examples to {split_name} split")
        
        # Save metadata
        metadata = {
            'total_samples': len(data),
            'splits': {name: len(split_data) for name, split_data in splits.items()},
            'format': 'instruction_tuning',
            'language': 'german',
            'domain': 'legal',
            'expansion_date': pd.Timestamp.now().isoformat(),
            'sources': list(set(item.get('source', 'unknown') for item in data))
        }
        
        with open(self.output_dir / 'metadata.json', 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Dataset expansion complete! Total: {len(data)} examples")
        return len(data)
    
    def expand_dataset(self) -> int:
        """Main method to expand the dataset"""
        logger.info("Starting advanced dataset expansion...")
        
        all_data = []
        
        # 1. Load existing data
        existing_data = self.load_existing_data()
        all_data.extend(existing_data)
        
        # 2. Search for alternative datasets
        alternative_data = self.search_alternative_datasets()
        all_data.extend(alternative_data)
        
        # 3. Generate synthetic variations
        synthetic_data = self.generate_synthetic_variations(existing_data)
        all_data.extend(synthetic_data)
        
        # 4. Apply quality filtering
        filtered_data = self.apply_quality_filtering(all_data)
        
        # 5. Save expanded dataset
        total_examples = self.save_expanded_dataset(filtered_data)
        
        return total_examples

def main():
    """Main execution function"""
    expander = AdvancedLegalDataExpander()
    total_examples = expander.expand_dataset()
    print(f"Successfully expanded dataset to {total_examples} examples!")

if __name__ == "__main__":
    main()