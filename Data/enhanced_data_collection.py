#!/usr/bin/env python3
"""
Enhanced German Legal Data Collection System
Comprehensive data gathering from multiple sources with quality control
"""

import asyncio
import aiohttp
import json
import re
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import hashlib
import random
from bs4 import BeautifulSoup
import requests
from datasets import load_dataset, Dataset
import pandas as pd
from urllib.parse import urljoin, urlparse
import time

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class LegalDocument:
    """Structure for legal documents"""
    title: str
    content: str
    source: str
    category: str
    court_level: Optional[str] = None
    date: Optional[str] = None
    reference: Optional[str] = None
    hash_id: Optional[str] = None

class GermanLegalDataCollector:
    """Comprehensive German legal data collection system"""
    
    def __init__(self, output_dir: str = "expanded_legal_data"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.session = None
        self.collected_hashes = set()
        
        # German legal websites to scrape
        self.legal_sources = {
            'bundesverfassungsgericht': {
                'base_url': 'https://www.bundesverfassungsgericht.de',
                'search_pattern': '/entscheidungen/',
                'category': 'constitutional_law'
            },
            'bundesgerichtshof': {
                'base_url': 'https://www.bundesgerichtshof.de',
                'search_pattern': '/entscheidungen/',
                'category': 'federal_court'
            },
            'rechtsprechung_im_internet': {
                'base_url': 'https://www.rechtsprechung-im-internet.de',
                'search_pattern': '/jportal/',
                'category': 'general_law'
            }
        }
        
        # HuggingFace datasets with German legal content
        self.hf_datasets = [
            "joelniklaus/lextreme",
            "joelniklaus/german_legal_entity_recognition",
            "joelniklaus/MultiLegalPile",
            "joelniklaus/legal_case_document_summarization",
            "coastalcph/danish_legal_corpus"  # Often includes German translations
        ]
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    def calculate_hash(self, content: str) -> str:
        """Calculate SHA-256 hash for deduplication"""
        return hashlib.sha256(content.encode('utf-8')).hexdigest()
    
    def is_duplicate(self, content: str) -> bool:
        """Check if content is duplicate"""
        content_hash = self.calculate_hash(content)
        if content_hash in self.collected_hashes:
            return True
        self.collected_hashes.add(content_hash)
        return False
    
    async def scrape_legal_website(self, source_name: str, source_config: Dict[str, str], max_pages: int = 100) -> List[LegalDocument]:
        """Scrape legal documents from German legal websites"""
        documents = []
        base_url = source_config['base_url']
        
        try:
            logger.info(f"Starting scraping of {source_name}")
            
            # Get main page
            async with self.session.get(base_url) as response:
                if response.status != 200:
                    logger.warning(f"Failed to access {base_url}: Status {response.status}")
                    return documents
                
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                
                # Find legal document links
                links = soup.find_all('a', href=True)
                legal_links = [
                    urljoin(base_url, link['href']) 
                    for link in links 
                    if source_config['search_pattern'] in link['href']
                ]
                
                # Limit number of pages to scrape
                legal_links = legal_links[:max_pages]
                
                # Scrape each document
                for i, link in enumerate(legal_links):
                    try:
                        await asyncio.sleep(1)  # Rate limiting
                        
                        async with self.session.get(link) as doc_response:
                            if doc_response.status != 200:
                                continue
                                
                            doc_html = await doc_response.text()
                            doc_soup = BeautifulSoup(doc_html, 'html.parser')
                            
                            # Extract content
                            title = self.extract_title(doc_soup)
                            content = self.extract_content(doc_soup)
                            
                            if content and len(content) > 200 and not self.is_duplicate(content):
                                doc = LegalDocument(
                                    title=title or f"Document {i+1}",
                                    content=content,
                                    source=source_name,
                                    category=source_config['category'],
                                    hash_id=self.calculate_hash(content)
                                )
                                documents.append(doc)
                                
                        if (i + 1) % 10 == 0:
                            logger.info(f"Scraped {i+1}/{len(legal_links)} documents from {source_name}")
                            
                    except Exception as e:
                        logger.warning(f"Error scraping document {link}: {e}")
                        continue
                        
        except Exception as e:
            logger.error(f"Error scraping {source_name}: {e}")
            
        logger.info(f"Collected {len(documents)} documents from {source_name}")
        return documents
    
    def extract_title(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract title from HTML"""
        title_selectors = ['h1', 'title', '.title', '#title', '.heading']
        
        for selector in title_selectors:
            title_elem = soup.select_one(selector)
            if title_elem:
                title = title_elem.get_text(strip=True)
                if title and len(title) > 5:
                    return title[:200]  # Limit title length
        return None
    
    def extract_content(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract main content from HTML"""
        # Remove script and style elements
        for script in soup(["script", "style", "nav", "header", "footer"]):
            script.decompose()
        
        # Try different content selectors
        content_selectors = [
            '.content', '#content', '.main-content', '#main-content',
            '.article', '#article', '.text', '#text', 'main', 'article'
        ]
        
        for selector in content_selectors:
            content_elem = soup.select_one(selector)
            if content_elem:
                content = content_elem.get_text(strip=True, separator=' ')
                if content and len(content) > 200:
                    return self.clean_text(content)
        
        # Fallback: get all text from body
        body = soup.find('body')
        if body:
            content = body.get_text(strip=True, separator=' ')
            if content and len(content) > 200:
                return self.clean_text(content)
        
        return None
    
    def clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove special characters but keep German umlauts
        text = re.sub(r'[^\w\säöüÄÖÜß.,;:!?()-]', '', text)
        return text.strip()
    
    def load_huggingface_datasets(self) -> List[LegalDocument]:
        """Load German legal datasets from HuggingFace"""
        documents = []
        
        for dataset_name in self.hf_datasets:
            try:
                logger.info(f"Loading HuggingFace dataset: {dataset_name}")
                
                # Load dataset
                dataset = load_dataset(dataset_name, split='train', streaming=False)
                
                # Process dataset based on structure
                for i, example in enumerate(dataset):
                    if i >= 1000:  # Limit per dataset
                        break
                    
                    # Extract text content (adapt based on dataset structure)
                    content = self.extract_hf_content(example)
                    if content and len(content) > 200 and not self.is_duplicate(content):
                        doc = LegalDocument(
                            title=f"HF Document {i+1}",
                            content=content,
                            source=f"huggingface_{dataset_name}",
                            category="legal_corpus",
                            hash_id=self.calculate_hash(content)
                        )
                        documents.append(doc)
                        
                logger.info(f"Loaded {len([d for d in documents if dataset_name in d.source])} documents from {dataset_name}")
                
            except Exception as e:
                logger.warning(f"Error loading dataset {dataset_name}: {e}")
                continue
        
        return documents
    
    def extract_hf_content(self, example: Dict[str, Any]) -> Optional[str]:
        """Extract content from HuggingFace dataset example"""
        # Common text fields in legal datasets
        text_fields = ['text', 'content', 'document', 'case_text', 'judgment', 'opinion']
        
        for field in text_fields:
            if field in example and example[field]:
                content = str(example[field])
                if len(content) > 200:
                    return self.clean_text(content)
        
        return None
    
    def augment_data(self, documents: List[LegalDocument]) -> List[LegalDocument]:
        """Apply data augmentation techniques"""
        augmented = []
        
        for doc in documents:
            # Original document
            augmented.append(doc)
            
            # Create instruction-following variants
            variants = self.create_instruction_variants(doc)
            augmented.extend(variants)
        
        return augmented
    
    def create_instruction_variants(self, doc: LegalDocument) -> List[LegalDocument]:
        """Create different instruction-following formats"""
        variants = []
        content = doc.content
        
        # Summarization task
        if len(content) > 500:
            summary_instruction = f"Fassen Sie den folgenden deutschen Rechtstext zusammen:\n\n{content[:800]}..."
            variants.append(LegalDocument(
                title=f"Zusammenfassung: {doc.title}",
                content=summary_instruction,
                source=f"{doc.source}_summary",
                category="instruction_following"
            ))
        
        # Question-answering task
        qa_instruction = f"Basierend auf diesem deutschen Rechtstext, beantworten Sie Fragen zum Inhalt:\n\n{content[:600]}..."
        variants.append(LegalDocument(
            title=f"Q&A: {doc.title}",
            content=qa_instruction,
            source=f"{doc.source}_qa",
            category="instruction_following"
        ))
        
        # Legal analysis task
        analysis_instruction = f"Analysieren Sie die rechtlichen Aspekte des folgenden deutschen Texts:\n\n{content[:600]}..."
        variants.append(LegalDocument(
            title=f"Analyse: {doc.title}",
            content=analysis_instruction,
            source=f"{doc.source}_analysis",
            category="instruction_following"
        ))
        
        return variants
    
    def save_documents(self, documents: List[LegalDocument], filename: str):
        """Save documents in multiple formats"""
        # Save as JSONL
        jsonl_path = self.output_dir / f"{filename}.jsonl"
        with open(jsonl_path, 'w', encoding='utf-8') as f:
            for doc in documents:
                json_obj = {
                    'title': doc.title,
                    'content': doc.content,
                    'source': doc.source,
                    'category': doc.category,
                    'court_level': doc.court_level,
                    'date': doc.date,
                    'reference': doc.reference,
                    'hash_id': doc.hash_id
                }
                f.write(json.dumps(json_obj, ensure_ascii=False) + '\n')
        
        # Save as Parquet for efficiency
        df = pd.DataFrame([{
            'title': doc.title,
            'content': doc.content,
            'source': doc.source,
            'category': doc.category,
            'court_level': doc.court_level,
            'date': doc.date,
            'reference': doc.reference,
            'hash_id': doc.hash_id
        } for doc in documents])
        
        parquet_path = self.output_dir / f"{filename}.parquet"
        df.to_parquet(parquet_path, index=False)
        
        logger.info(f"Saved {len(documents)} documents to {jsonl_path} and {parquet_path}")
    
    async def collect_all_data(self):
        """Main method to collect all data"""
        logger.info("Starting comprehensive German legal data collection")
        
        all_documents = []
        
        # 1. Scrape legal websites
        for source_name, source_config in self.legal_sources.items():
            documents = await self.scrape_legal_website(source_name, source_config, max_pages=50)
            all_documents.extend(documents)
            
            # Save intermediate results
            if documents:
                self.save_documents(documents, f"scraped_{source_name}")
        
        # 2. Load HuggingFace datasets
        hf_documents = self.load_huggingface_datasets()
        all_documents.extend(hf_documents)
        
        if hf_documents:
            self.save_documents(hf_documents, "huggingface_datasets")
        
        # 3. Apply data augmentation
        logger.info("Applying data augmentation...")
        augmented_documents = self.augment_data(all_documents)
        
        # 4. Save final dataset
        self.save_documents(augmented_documents, "expanded_german_legal_dataset")
        
        # 5. Create train/validation/test splits
        self.create_data_splits(augmented_documents)
        
        logger.info(f"Data collection complete! Total documents: {len(augmented_documents)}")
        return augmented_documents
    
    def create_data_splits(self, documents: List[LegalDocument]):
        """Create proper train/validation/test splits"""
        random.shuffle(documents)
        
        total = len(documents)
        train_size = int(0.8 * total)
        val_size = int(0.1 * total)
        
        train_docs = documents[:train_size]
        val_docs = documents[train_size:train_size + val_size]
        test_docs = documents[train_size + val_size:]
        
        self.save_documents(train_docs, "train")
        self.save_documents(val_docs, "validation")
        self.save_documents(test_docs, "test")
        
        logger.info(f"Created splits - Train: {len(train_docs)}, Val: {len(val_docs)}, Test: {len(test_docs)}")

async def main():
    """Main execution function"""
    collector = GermanLegalDataCollector()
    
    async with collector:
        documents = await collector.collect_all_data()
        print(f"Successfully collected {len(documents)} German legal documents!")

if __name__ == "__main__":
    asyncio.run(main())