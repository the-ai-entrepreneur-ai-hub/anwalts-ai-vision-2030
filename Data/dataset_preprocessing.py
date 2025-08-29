#!/usr/bin/env python3
"""
German Legal Dataset Preprocessing Script

This script provides comprehensive preprocessing capabilities for German legal documents
to prepare them for training legal language models. It handles various input formats,
applies legal-specific cleaning, and outputs training-ready datasets.

Usage:
    python dataset_preprocessing.py --input data/ --output processed_dataset/
    python dataset_preprocessing.py --config config.yaml
"""

import argparse
import json
import re
import logging
import yaml
from pathlib import Path
from typing import List, Dict, Union, Optional, Tuple
from dataclasses import dataclass
import pandas as pd
from datasets import Dataset, DatasetDict
import nltk
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.corpus import stopwords
from tqdm import tqdm
import spacy

# Download required NLTK data
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('preprocessing.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class PreprocessingConfig:
    """Configuration for preprocessing pipeline"""
    
    # Input/Output settings
    input_path: str
    output_path: str
    
    # Text processing settings
    max_length: int = 512
    min_length: int = 50
    overlap_size: int = 50
    
    # Legal-specific settings
    preserve_paragraph_refs: bool = True
    normalize_legal_terms: bool = True
    extract_citations: bool = True
    
    # Dataset formatting
    instruction_format: bool = True
    validation_split: float = 0.1
    test_split: float = 0.1
    
    # Output settings
    save_format: str = "jsonl"  # Options: jsonl, csv, parquet, hf_dataset
    push_to_hub: bool = False
    hub_dataset_id: Optional[str] = None

class GermanLegalPreprocessor:
    """Comprehensive preprocessor for German legal documents"""
    
    def __init__(self, config: PreprocessingConfig):
        self.config = config
        
        # Legal terminology mapping
        self.legal_abbreviations = {
            "BGB": "Bürgerliches Gesetzbuch",
            "StGB": "Strafgesetzbuch",
            "HGB": "Handelsgesetzbuch",
            "GG": "Grundgesetz",
            "ZPO": "Zivilprozessordnung",
            "StPO": "Strafprozessordnung",
            "VwGO": "Verwaltungsgerichtsordnung",
            "FGO": "Finanzgerichtsordnung",
            "SGG": "Sozialgerichtsgesetz",
            "AO": "Abgabenordnung",
            "EStG": "Einkommensteuergesetz",
            "UStG": "Umsatzsteuergesetz",
            "GmbHG": "GmbH-Gesetz",
            "AktG": "Aktiengesetz",
            "BetrVG": "Betriebsverfassungsgesetz",
            "TVG": "Tarifvertragsgesetz",
            "KSchG": "Kündigungsschutzgesetz"
        }
        
        # Court abbreviations
        self.court_abbreviations = {
            "BGH": "Bundesgerichtshof",
            "BVerfG": "Bundesverfassungsgericht",
            "BVerwG": "Bundesverwaltungsgericht",
            "BSG": "Bundessozialgericht",
            "BFH": "Bundesfinanzhof",
            "BAG": "Bundesarbeitsgericht",
            "OLG": "Oberlandesgericht",
            "LG": "Landgericht",
            "AG": "Amtsgericht",
            "VG": "Verwaltungsgericht",
            "OVG": "Oberverwaltungsgericht",
            "SG": "Sozialgericht",
            "LSG": "Landessozialgericht",
            "FG": "Finanzgericht"
        }
        
        # Legal document types
        self.document_types = [
            "Urteil", "Beschluss", "Verfügung", "Verordnung", "Gesetz",
            "Satzung", "Vertrag", "Vollmacht", "Einspruch", "Berufung",
            "Revision", "Beschwerde", "Antrag", "Klage", "Anzeige"
        ]
        
        # Load spaCy model for advanced NLP (optional)
        try:
            self.nlp = spacy.load("de_core_news_sm")
            logger.info("Loaded spaCy German model")
        except OSError:
            logger.warning("spaCy German model not found. Install with: python -m spacy download de_core_news_sm")
            self.nlp = None
        
        # Statistics tracking
        self.stats = {
            "total_documents": 0,
            "total_chunks": 0,
            "avg_chunk_length": 0,
            "legal_terms_found": 0,
            "citations_extracted": 0,
            "filtered_chunks": 0
        }
    
    def load_documents(self, input_path: Union[str, Path]) -> List[Dict]:
        """Load documents from various input formats"""
        input_path = Path(input_path)
        documents = []
        
        if input_path.is_file():
            documents.extend(self._load_single_file(input_path))
        elif input_path.is_dir():
            # Process all files in directory
            for file_path in input_path.rglob("*"):
                if file_path.is_file() and file_path.suffix in ['.json', '.jsonl', '.txt', '.csv']:
                    documents.extend(self._load_single_file(file_path))
        else:
            raise ValueError(f"Input path does not exist: {input_path}")
        
        logger.info(f"Loaded {len(documents)} documents from {input_path}")
        self.stats["total_documents"] = len(documents)
        return documents
    
    def _load_single_file(self, file_path: Path) -> List[Dict]:
        """Load documents from a single file"""
        documents = []
        
        try:
            if file_path.suffix == '.json':
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                if isinstance(data, list):
                    documents = data
                else:
                    documents = [data]
            
            elif file_path.suffix == '.jsonl':
                with open(file_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        if line.strip():
                            documents.append(json.loads(line))
            
            elif file_path.suffix == '.txt':
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                documents = [{"text": content, "source": str(file_path)}]
            
            elif file_path.suffix == '.csv':
                df = pd.read_csv(file_path)
                # Assume 'text' column exists
                if 'text' in df.columns:
                    documents = df.to_dict('records')
                else:
                    logger.warning(f"No 'text' column found in {file_path}")
            
        except Exception as e:
            logger.error(f"Error loading {file_path}: {e}")
        
        return documents
    
    def clean_text(self, text: str) -> str:
        """Clean and normalize German legal text"""
        if not text or not isinstance(text, str):
            return ""
        
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Normalize quotation marks
        text = re.sub(r'[""„"]', '"', text)
        text = re.sub(r'[''‚']', "'", text)
        
        # Fix paragraph references (§ symbols)
        if self.config.preserve_paragraph_refs:
            text = re.sub(r'§\s*(\d+)', r'§ \1', text)
            text = re.sub(r'§§\s*(\d+)', r'§§ \1', text)
        
        # Fix article references
        text = re.sub(r'Art\.\s*(\d+)', r'Art. \1', text)
        
        # Normalize legal abbreviations
        if self.config.normalize_legal_terms:
            for abbrev, full_name in self.legal_abbreviations.items():
                # Replace with full name in parentheses for clarity
                pattern = rf'\b{re.escape(abbrev)}\b'
                text = re.sub(pattern, f"{abbrev} ({full_name})", text)
        
        # Remove footnote markers
        text = re.sub(r'\[\d+\]', '', text)
        text = re.sub(r'\(\d+\)', '', text)
        
        # Clean up page numbers and headers/footers
        text = re.sub(r'\n\s*\d+\s*\n', '\n', text)
        text = re.sub(r'\n\s*Seite\s+\d+.*?\n', '\n', text, flags=re.IGNORECASE)
        
        # Remove excessive line breaks
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        # Clean up spaces around punctuation
        text = re.sub(r'\s+([.,;:!?])', r'\1', text)
        text = re.sub(r'([.,;:!?])\s+', r'\1 ', text)
        
        # Remove trailing/leading whitespace
        text = text.strip()
        
        return text
    
    def extract_legal_metadata(self, text: str) -> Dict:
        """Extract legal metadata from text"""
        metadata = {
            "legal_references": [],
            "court_references": [],
            "document_type": None,
            "date_references": [],
            "case_numbers": []
        }
        
        # Extract paragraph references
        paragraphs = re.findall(r'§\s*(\d+(?:\s*[a-z])?)(?:\s+((?:BGB|StGB|HGB|GG|ZPO|StPO|VwGO|FGO|SGG|AO|EStG|UStG|GmbHG|AktG|BetrVG|TVG|KSchG)))?', text, re.IGNORECASE)
        for para, law in paragraphs:
            ref = f"§ {para}"
            if law:
                ref += f" {law}"
            metadata["legal_references"].append(ref)
        
        # Extract court references
        for court_abbrev, court_name in self.court_abbreviations.items():
            if court_abbrev in text:
                metadata["court_references"].append(court_name)
        
        # Identify document type
        for doc_type in self.document_types:
            if doc_type.lower() in text.lower():
                metadata["document_type"] = doc_type
                break
        
        # Extract dates (German format)
        dates = re.findall(r'\b(\d{1,2}\.)\s*(\d{1,2}\.)\s*(\d{4})\b', text)
        metadata["date_references"] = [f"{d[0]}{d[1]}{d[2]}" for d in dates]
        
        # Extract case numbers
        case_numbers = re.findall(r'\b\d+\s*[A-Z]+\s*\d+/\d+\b', text)
        metadata["case_numbers"] = case_numbers
        
        return metadata
    
    def chunk_text(self, text: str, metadata: Dict = None) -> List[Dict]:
        """Split text into overlapping chunks with metadata"""
        if len(text) < self.config.min_length:
            return []
        
        chunks = []
        
        # First try to split by sentences for better coherence
        try:
            sentences = sent_tokenize(text, language='german')
        except:
            # Fallback to simple sentence splitting
            sentences = re.split(r'[.!?]+\s+', text)
        
        current_chunk = ""
        current_length = 0
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            
            sentence_length = len(sentence.split())
            
            # If adding this sentence would exceed max_length, finalize current chunk
            if current_length + sentence_length > self.config.max_length:
                if current_chunk and current_length >= self.config.min_length:
                    chunk_data = {
                        "text": current_chunk.strip(),
                        "length": current_length,
                        "metadata": metadata.copy() if metadata else {}
                    }
                    chunks.append(chunk_data)
                
                # Start new chunk with overlap
                overlap_text = self._get_overlap_text(current_chunk, self.config.overlap_size)
                current_chunk = overlap_text + " " + sentence if overlap_text else sentence
                current_length = len(current_chunk.split())
            else:
                current_chunk += " " + sentence if current_chunk else sentence
                current_length += sentence_length
        
        # Add final chunk if it meets minimum length
        if current_chunk and current_length >= self.config.min_length:
            chunk_data = {
                "text": current_chunk.strip(),
                "length": current_length,
                "metadata": metadata.copy() if metadata else {}
            }
            chunks.append(chunk_data)
        
        return chunks
    
    def _get_overlap_text(self, text: str, overlap_words: int) -> str:
        """Get the last N words from text for overlap"""
        words = text.split()
        if len(words) <= overlap_words:
            return text
        return " ".join(words[-overlap_words:])
    
    def create_instruction_format(self, chunk: Dict) -> Dict:
        """Convert chunk to instruction-following format"""
        text = chunk["text"]
        metadata = chunk.get("metadata", {})
        
        # Create different types of instructions based on content
        instructions = [
            "Erkläre den folgenden deutschen Rechtstext:",
            "Analysiere das folgende deutsche Rechtsdokument:",
            "Fasse den folgenden Rechtstext zusammen:",
            "Welche rechtlichen Aspekte werden im folgenden Text behandelt?",
            "Erläutere die wichtigsten Punkte des folgenden Rechtstexts:"
        ]
        
        # Choose instruction based on document type or randomly
        doc_type = metadata.get("document_type")
        if doc_type:
            if doc_type in ["Urteil", "Beschluss"]:
                instruction = "Analysiere die folgende Gerichtsentscheidung:"
            elif doc_type in ["Gesetz", "Verordnung"]:
                instruction = "Erkläre die folgende Rechtsvorschrift:"
            elif doc_type in ["Vertrag"]:
                instruction = "Analysiere die folgenden Vertragsbestimmungen:"
            else:
                instruction = instructions[0]
        else:
            instruction = instructions[0]  # Default
        
        # Create training example
        example = {
            "instruction": instruction,
            "input": text[:800],  # Limit input length
            "output": self._generate_summary(text, metadata),
            "metadata": metadata
        }
        
        if self.config.instruction_format:
            # Format as single text field
            formatted_text = f"### Anweisung:\n{example['instruction']}\n\n### Eingabe:\n{example['input']}\n\n### Antwort:\n{example['output']}"
            return {
                "text": formatted_text,
                "metadata": metadata
            }
        else:
            return example
    
    def _generate_summary(self, text: str, metadata: Dict) -> str:
        """Generate a basic summary/response for the text"""
        # Extract key information for summary
        legal_refs = metadata.get("legal_references", [])
        court_refs = metadata.get("court_references", [])
        doc_type = metadata.get("document_type")
        
        # Build summary
        summary_parts = []
        
        if doc_type:
            summary_parts.append(f"Dieses Dokument ist ein {doc_type}.")
        
        if legal_refs:
            refs_str = ", ".join(legal_refs[:3])  # Limit to first 3
            summary_parts.append(f"Es bezieht sich auf {refs_str}.")
        
        if court_refs:
            court_str = ", ".join(set(court_refs[:2]))  # Limit and deduplicate
            summary_parts.append(f"Das Verfahren betrifft {court_str}.")
        
        # Add first sentence of original text as context
        sentences = text.split('. ')
        if sentences:
            first_sentence = sentences[0].strip()
            if not first_sentence.endswith('.'):
                first_sentence += '.'
            summary_parts.append(f"Kerninhalt: {first_sentence}")
        
        return " ".join(summary_parts) if summary_parts else f"Dies ist ein deutsches Rechtsdokument mit {len(text.split())} Wörtern."
    
    def filter_quality(self, chunks: List[Dict]) -> List[Dict]:
        """Filter chunks based on quality criteria"""
        filtered_chunks = []
        
        for chunk in chunks:
            text = chunk["text"]
            
            # Skip if too short or too long
            word_count = len(text.split())
            if word_count < self.config.min_length or word_count > self.config.max_length:
                continue
            
            # Skip if mostly numbers or special characters
            alpha_ratio = sum(c.isalpha() for c in text) / len(text)
            if alpha_ratio < 0.6:
                continue
            
            # Skip if no legal content indicators
            has_legal_content = any(term in text for term in self.legal_abbreviations.keys())
            has_legal_words = any(word in text.lower() for word in ["recht", "gesetz", "urteil", "gericht", "richter", "anwalt"])
            
            if not (has_legal_content or has_legal_words):
                continue
            
            # Skip duplicates (simple check)
            text_hash = hash(text[:100])  # Hash first 100 chars
            if any(hash(existing["text"][:100]) == text_hash for existing in filtered_chunks):
                continue
            
            filtered_chunks.append(chunk)
        
        self.stats["filtered_chunks"] = len(chunks) - len(filtered_chunks)
        logger.info(f"Filtered {self.stats['filtered_chunks']} low-quality chunks")
        
        return filtered_chunks
    
    def process_documents(self, documents: List[Dict]) -> List[Dict]:
        """Process all documents through the complete pipeline"""
        all_examples = []
        
        logger.info("Starting document processing...")
        
        for doc in tqdm(documents, desc="Processing documents"):
            try:
                # Extract text
                text = doc.get("text", "")
                if not text:
                    continue
                
                # Clean text
                cleaned_text = self.clean_text(text)
                if not cleaned_text:
                    continue
                
                # Extract metadata
                metadata = self.extract_legal_metadata(cleaned_text)
                metadata.update(doc.get("metadata", {}))
                
                # Add source information
                metadata["source"] = doc.get("source", "unknown")
                
                # Update statistics
                self.stats["legal_terms_found"] += len(metadata.get("legal_references", []))
                self.stats["citations_extracted"] += len(metadata.get("case_numbers", []))
                
                # Chunk text
                chunks = self.chunk_text(cleaned_text, metadata)
                
                # Convert to training format
                for chunk in chunks:
                    if self.config.instruction_format:
                        example = self.create_instruction_format(chunk)
                    else:
                        example = chunk
                    
                    all_examples.append(example)
                
                self.stats["total_chunks"] += len(chunks)
                
            except Exception as e:
                logger.error(f"Error processing document: {e}")
                continue
        
        # Filter for quality
        filtered_examples = self.filter_quality(all_examples)
        
        # Calculate statistics
        if filtered_examples:
            avg_length = sum(len(ex["text"].split()) for ex in filtered_examples) / len(filtered_examples)
            self.stats["avg_chunk_length"] = avg_length
        
        logger.info(f"Processing complete: {len(filtered_examples)} examples created")
        return filtered_examples
    
    def create_dataset_splits(self, examples: List[Dict]) -> DatasetDict:
        """Create train/validation/test splits"""
        
        # Convert to pandas for easier manipulation
        df = pd.DataFrame(examples)
        
        # Shuffle the data
        df = df.sample(frac=1, random_state=42).reset_index(drop=True)
        
        # Calculate split sizes
        total_size = len(df)
        test_size = int(total_size * self.config.test_split)
        val_size = int(total_size * self.config.validation_split)
        train_size = total_size - test_size - val_size
        
        # Create splits
        train_df = df[:train_size]
        val_df = df[train_size:train_size + val_size]
        test_df = df[train_size + val_size:]
        
        # Convert to datasets
        dataset_dict = DatasetDict({
            "train": Dataset.from_pandas(train_df),
            "validation": Dataset.from_pandas(val_df),
            "test": Dataset.from_pandas(test_df)
        })
        
        logger.info(f"Dataset splits created: Train={len(train_df)}, Val={len(val_df)}, Test={len(test_df)}")
        
        return dataset_dict
    
    def save_dataset(self, dataset: Union[Dataset, DatasetDict], output_path: Path):
        """Save dataset in specified format"""
        output_path = Path(output_path)
        output_path.mkdir(parents=True, exist_ok=True)
        
        if self.config.save_format == "jsonl":
            if isinstance(dataset, DatasetDict):
                for split_name, split_dataset in dataset.items():
                    output_file = output_path / f"{split_name}.jsonl"
                    split_dataset.to_json(output_file)
            else:
                output_file = output_path / "dataset.jsonl"
                dataset.to_json(output_file)
        
        elif self.config.save_format == "csv":
            if isinstance(dataset, DatasetDict):
                for split_name, split_dataset in dataset.items():
                    output_file = output_path / f"{split_name}.csv"
                    split_dataset.to_csv(output_file)
            else:
                output_file = output_path / "dataset.csv"
                dataset.to_csv(output_file)
        
        elif self.config.save_format == "parquet":
            if isinstance(dataset, DatasetDict):
                for split_name, split_dataset in dataset.items():
                    output_file = output_path / f"{split_name}.parquet"
                    split_dataset.to_parquet(output_file)
            else:
                output_file = output_path / "dataset.parquet"
                dataset.to_parquet(output_file)
        
        elif self.config.save_format == "hf_dataset":
            dataset.save_to_disk(output_path)
        
        logger.info(f"Dataset saved to {output_path} in {self.config.save_format} format")
        
        # Save statistics
        stats_file = output_path / "preprocessing_stats.json"
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(self.stats, f, indent=2, ensure_ascii=False)
        
        # Push to hub if requested
        if self.config.push_to_hub and self.config.hub_dataset_id:
            try:
                dataset.push_to_hub(self.config.hub_dataset_id)
                logger.info(f"Dataset pushed to Hugging Face Hub: {self.config.hub_dataset_id}")
            except Exception as e:
                logger.error(f"Failed to push to hub: {e}")
    
    def generate_report(self, output_path: Path):
        """Generate a preprocessing report"""
        report = f"""
# German Legal Dataset Preprocessing Report

## Processing Statistics
- Total Documents Processed: {self.stats['total_documents']}
- Total Chunks Created: {self.stats['total_chunks']}
- Average Chunk Length: {self.stats['avg_chunk_length']:.1f} words
- Legal Terms Found: {self.stats['legal_terms_found']}
- Citations Extracted: {self.stats['citations_extracted']}
- Filtered Low-Quality Chunks: {self.stats['filtered_chunks']}

## Configuration Used
- Max Length: {self.config.max_length} words
- Min Length: {self.config.min_length} words
- Overlap Size: {self.config.overlap_size} words
- Instruction Format: {self.config.instruction_format}
- Validation Split: {self.config.validation_split}
- Test Split: {self.config.test_split}

## Data Quality Measures
- Text cleaning and normalization applied
- Legal metadata extraction performed
- Quality filtering based on:
  - Minimum/maximum length requirements
  - Legal content indicators
  - Alphanumeric character ratio
  - Duplicate detection

## Legal Terminology Recognized
- Laws: {', '.join(self.legal_abbreviations.keys())}
- Courts: {', '.join(self.court_abbreviations.keys())}
- Document Types: {', '.join(self.document_types)}

## Output Format
- Format: {self.config.save_format}
- Location: {output_path}
- Hugging Face Hub: {'Yes' if self.config.push_to_hub else 'No'}

## Recommendations
- Review filtered chunks for potential false negatives
- Consider expanding legal terminology lists for your specific domain
- Validate instruction formats with sample model training
- Monitor data quality metrics in production
"""
        
        report_file = output_path / "preprocessing_report.md"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        logger.info(f"Preprocessing report saved to {report_file}")

def load_config(config_path: str) -> PreprocessingConfig:
    """Load configuration from YAML file"""
    with open(config_path, 'r', encoding='utf-8') as f:
        config_dict = yaml.safe_load(f)
    
    return PreprocessingConfig(**config_dict)

def main():
    parser = argparse.ArgumentParser(description="Preprocess German legal documents for training")
    parser.add_argument("--input", "-i", required=True, help="Input path (file or directory)")
    parser.add_argument("--output", "-o", required=True, help="Output directory")
    parser.add_argument("--config", "-c", help="Configuration file (YAML)")
    parser.add_argument("--max-length", type=int, default=512, help="Maximum chunk length in words")
    parser.add_argument("--min-length", type=int, default=50, help="Minimum chunk length in words")
    parser.add_argument("--format", choices=["jsonl", "csv", "parquet", "hf_dataset"], default="jsonl", help="Output format")
    parser.add_argument("--instruction-format", action="store_true", help="Use instruction-following format")
    parser.add_argument("--push-to-hub", action="store_true", help="Push dataset to Hugging Face Hub")
    parser.add_argument("--hub-dataset-id", help="Hugging Face dataset ID")
    
    args = parser.parse_args()
    
    # Load configuration
    if args.config:
        config = load_config(args.config)
    else:
        config = PreprocessingConfig(
            input_path=args.input,
            output_path=args.output,
            max_length=args.max_length,
            min_length=args.min_length,
            save_format=args.format,
            instruction_format=args.instruction_format,
            push_to_hub=args.push_to_hub,
            hub_dataset_id=args.hub_dataset_id
        )
    
    # Initialize preprocessor
    preprocessor = GermanLegalPreprocessor(config)
    
    # Load documents
    documents = preprocessor.load_documents(config.input_path)
    
    if not documents:
        logger.error("No documents found to process")
        return
    
    # Process documents
    examples = preprocessor.process_documents(documents)
    
    if not examples:
        logger.error("No examples created after processing")
        return
    
    # Create dataset splits
    if config.validation_split > 0 or config.test_split > 0:
        dataset = preprocessor.create_dataset_splits(examples)
    else:
        dataset = Dataset.from_pandas(pd.DataFrame(examples))
    
    # Save dataset
    output_path = Path(config.output_path)
    preprocessor.save_dataset(dataset, output_path)
    
    # Generate report
    preprocessor.generate_report(output_path)
    
    logger.info("Preprocessing pipeline completed successfully!")

if __name__ == "__main__":
    main()