#!/usr/bin/env python3
"""
German Legal Dataset Preparation Script
Prepares and formats German legal documents for fine-tuning
"""

import json
import pandas as pd
import os
import re
from typing import List, Dict, Any
from pathlib import Path
import argparse
from datasets import Dataset
import spacy

# Load German NLP model
try:
    nlp = spacy.load("de_core_news_sm")
except OSError:
    print("Please install German spaCy model: python -m spacy download de_core_news_sm")
    exit(1)

class GermanLegalDatasetPreprocessor:
    """Preprocessor for German legal documents."""
    
    def __init__(self, min_length: int = 50, max_length: int = 2048):
        self.min_length = min_length
        self.max_length = max_length
        
        # Legal document patterns
        self.legal_patterns = {
            'paragraph': r'§\s*\d+[a-z]?(?:\s+[A-Za-z]+)?',
            'article': r'Art\.?\s*\d+[a-z]?',
            'bgb': r'BGB',
            'stgb': r'StGB',
            'hgb': r'HGB',
            'zpo': r'ZPO',
            'case_reference': r'\d+\s+[A-Z]+\s+\d+/\d+',
            'court': r'(?:Bundesgerichtshof|Landgericht|Amtsgericht|Oberlandesgericht)',
        }
    
    def clean_text(self, text: str) -> str:
        """Clean and normalize German legal text."""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Normalize quotes
        text = re.sub(r'[„""]', '"', text)
        text = re.sub(r'[‚'']', "'", text)
        
        # Fix common OCR errors
        text = re.sub(r'(?<=\d)\s+(?=\d)', '', text)  # Remove spaces in numbers
        text = re.sub(r'(?<=[a-z])\s+(?=[A-Z][a-z])', ' ', text)  # Normalize word spacing
        
        # Normalize legal references
        text = re.sub(r'§§\s*(\d+)', r'§ \1', text)
        text = re.sub(r'Art\.\s*(\d+)', r'Art. \1', text)
        
        return text.strip()
    
    def extract_legal_entities(self, text: str) -> Dict[str, List[str]]:
        """Extract legal entities from German text."""
        entities = {
            'paragraphs': [],
            'articles': [],
            'laws': [],
            'courts': [],
            'case_references': []
        }
        
        # Extract paragraphs
        entities['paragraphs'] = re.findall(self.legal_patterns['paragraph'], text)
        
        # Extract articles
        entities['articles'] = re.findall(self.legal_patterns['article'], text)
        
        # Extract laws
        for law in ['BGB', 'StGB', 'HGB', 'ZPO', 'GG', 'AO']:
            if law in text:
                entities['laws'].append(law)
        
        # Extract courts
        entities['courts'] = re.findall(self.legal_patterns['court'], text)
        
        # Extract case references
        entities['case_references'] = re.findall(self.legal_patterns['case_reference'], text)
        
        return entities
    
    def create_instruction_dataset(self, documents: List[Dict]) -> List[Dict]:
        """Create instruction-following dataset from legal documents."""
        instruction_templates = [
            "Analysiere diesen rechtlichen Text und erkläre die wichtigsten Punkte:",
            "Fasse die rechtlichen Aspekte dieses Dokuments zusammen:",
            "Erkläre die rechtlichen Implikationen dieses Textes:",
            "Identifiziere potenzielle rechtliche Probleme in diesem Dokument:",
            "Bewerte die rechtliche Situation basierend auf diesem Text:",
            "Erstelle eine rechtliche Einschätzung zu folgendem Fall:",
            "Analysiere die Rechtslage anhand dieser Informationen:",
            "Gib eine rechtliche Bewertung zu diesem Sachverhalt ab:",
        ]
        
        qa_templates = [
            "Was besagt {} in diesem Kontext?",
            "Wie ist {} rechtlich zu bewerten?",
            "Welche Bedeutung hat {} für diesen Fall?",
            "Erkläre die Anwendung von {} hier:",
            "Was sind die Konsequenzen von {} in dieser Situation?",
        ]
        
        dataset = []
        
        for doc in documents:
            text = self.clean_text(doc.get('content', ''))
            if len(text) < self.min_length:
                continue
                
            # Extract legal entities
            entities = self.extract_legal_entities(text)
            
            # Create general analysis instructions
            for template in instruction_templates[:3]:  # Use first 3 templates
                if len(text) <= self.max_length - 200:  # Leave room for instruction
                    dataset.append({
                        'instruction': template,
                        'input': text[:1500],  # Limit input length
                        'output': self.generate_analysis(text, entities),
                        'category': 'analysis',
                        'entities': entities
                    })
            
            # Create specific Q&A pairs
            for entity_type, entity_list in entities.items():
                if entity_list:
                    for entity in entity_list[:2]:  # Max 2 per type
                        for template in qa_templates[:2]:  # Use first 2 templates
                            question = template.format(entity)
                            dataset.append({
                                'instruction': question,
                                'input': text[:1000],
                                'output': self.generate_entity_explanation(entity, entity_type, text),
                                'category': 'qa',
                                'entities': {entity_type: [entity]}
                            })
        
        return dataset
    
    def generate_analysis(self, text: str, entities: Dict) -> str:
        """Generate legal analysis for a document."""
        analysis_parts = []
        
        # Start with overview
        analysis_parts.append("Rechtliche Analyse:")
        
        # Identify main legal areas
        if entities['laws']:
            laws_str = ', '.join(set(entities['laws']))
            analysis_parts.append(f"Das Dokument bezieht sich hauptsächlich auf {laws_str}.")
        
        # Mention relevant paragraphs
        if entities['paragraphs']:
            paras = ', '.join(entities['paragraphs'][:3])  # Max 3
            analysis_parts.append(f"Relevante Bestimmungen: {paras}.")
        
        # Court references
        if entities['courts']:
            courts = ', '.join(set(entities['courts']))
            analysis_parts.append(f"Gerichtliche Instanzen: {courts}.")
        
        # Add generic legal assessment
        analysis_parts.append("Die rechtliche Bewertung hängt von den spezifischen Umständen des Einzelfalls ab.")
        analysis_parts.append("Es wird empfohlen, für eine detaillierte Einschätzung rechtlichen Rat einzuholen.")
        
        return ' '.join(analysis_parts)
    
    def generate_entity_explanation(self, entity: str, entity_type: str, context: str) -> str:
        """Generate explanation for a legal entity."""
        if entity_type == 'paragraphs':
            return f"{entity} ist eine wichtige rechtliche Bestimmung im deutschen Recht. Im vorliegenden Kontext regelt diese Vorschrift die entsprechenden rechtlichen Verhältnisse und ist für die Bewertung des Sachverhalts von Bedeutung."
        
        elif entity_type == 'laws':
            law_explanations = {
                'BGB': 'Das Bürgerliche Gesetzbuch (BGB) regelt die zentralen Bereiche des Privatrechts in Deutschland.',
                'StGB': 'Das Strafgesetzbuch (StGB) enthält die wichtigsten Straftatbestände des deutschen Strafrechts.',
                'HGB': 'Das Handelsgesetzbuch (HGB) regelt das deutsche Handels- und Gesellschaftsrecht.',
                'ZPO': 'Die Zivilprozessordnung (ZPO) regelt das Verfahren in Zivilsachen vor deutschen Gerichten.',
            }
            return law_explanations.get(entity, f"{entity} ist ein wichtiges Gesetz im deutschen Rechtssystem.")
        
        elif entity_type == 'courts':
            return f"{entity} ist eine wichtige gerichtliche Instanz im deutschen Rechtssystem, die für die Rechtsprechung in entsprechenden Verfahren zuständig ist."
        
        else:
            return f"{entity} ist ein relevanter rechtlicher Begriff im vorliegenden Kontext und von Bedeutung für die rechtliche Bewertung."

def load_sample_data() -> List[Dict]:
    """Load sample German legal data for demonstration."""
    sample_data = [
        {
            'content': '''Ein Mietvertrag wurde am 1. Januar 2024 geschlossen. Der Vermieter verlangt eine Kaution von 5 Monatsmieten. 
            Die Miete beträgt 1.000 Euro monatlich. Nach § 551 BGB ist die Kaution auf maximal 3 Monatsmieten begrenzt. 
            Der Mieter kann die Überschreitung der gesetzlichen Höchstgrenze rechtlich beanstanden.''',
            'category': 'Mietrecht',
            'title': 'Kautionshöhe Mietvertrag'
        },
        {
            'content': '''Ein Arbeitnehmer wurde während der Probezeit gekündigt. Die Probezeit beträgt 12 Monate. 
            Nach § 622 Abs. 3 BGB darf die Probezeit höchstens 6 Monate betragen. Eine längere Probezeit ist unwirksam. 
            Die Kündigung könnte daher rechtswidrig sein, wenn sie nach Ablauf der zulässigen Probezeit erfolgte.''',
            'category': 'Arbeitsrecht',
            'title': 'Kündigung in der Probezeit'
        },
        {
            'content': '''Bei einem Kaufvertrag über ein gebrauchtes Auto wurde verschwiegen, dass das Fahrzeug einen Unfallschaden hatte. 
            Der Käufer kann nach § 437 BGB Gewährleistungsrechte geltend machen. Bei arglistiger Täuschung nach § 123 BGB 
            ist eine Anfechtung des Vertrags möglich. Die Verjährungsfrist beträgt nach § 438 BGB zwei Jahre.''',
            'category': 'Kaufrecht',
            'title': 'Mangelhafter Gebrauchtwagenkauf'
        },
        {
            'content': '''Das Landgericht München entschied in einem Fall des Gesellschaftsrechts nach HGB. 
            Die GmbH hatte ihre Geschäftsführerpflichten verletzt. Nach § 43 GmbHG haftet der Geschäftsführer 
            für Schäden bei Pflichtverletzungen. Das Urteil wurde am 15. März 2024 unter Az. 12 O 1234/23 gefällt.''',
            'category': 'Gesellschaftsrecht',
            'title': 'Geschäftsführerhaftung GmbH'
        }
    ]
    return sample_data

def main():
    parser = argparse.ArgumentParser(description='Prepare German legal dataset for fine-tuning')
    parser.add_argument('--input-file', type=str, help='Input JSON file with legal documents')
    parser.add_argument('--output-dir', type=str, default='./dataset', help='Output directory')
    parser.add_argument('--min-length', type=int, default=50, help='Minimum text length')
    parser.add_argument('--max-length', type=int, default=2048, help='Maximum text length')
    parser.add_argument('--sample-data', action='store_true', help='Use sample data for demonstration')
    
    args = parser.parse_args()
    
    # Create output directory
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Initialize preprocessor
    preprocessor = GermanLegalDatasetPreprocessor(
        min_length=args.min_length,
        max_length=args.max_length
    )
    
    # Load data
    if args.sample_data:
        print("Using sample data for demonstration...")
        documents = load_sample_data()
    elif args.input_file:
        print(f"Loading data from {args.input_file}...")
        with open(args.input_file, 'r', encoding='utf-8') as f:
            documents = json.load(f)
    else:
        print("Please provide --input-file or use --sample-data")
        return
    
    # Create instruction dataset
    print("Creating instruction-following dataset...")
    instruction_data = preprocessor.create_instruction_dataset(documents)
    
    print(f"Generated {len(instruction_data)} training examples")
    
    # Save datasets
    train_file = os.path.join(args.output_dir, 'german_legal_train.json')
    with open(train_file, 'w', encoding='utf-8') as f:
        json.dump(instruction_data, f, ensure_ascii=False, indent=2)
    
    # Create CSV for easier inspection
    df = pd.DataFrame(instruction_data)
    csv_file = os.path.join(args.output_dir, 'german_legal_train.csv')
    df.to_csv(csv_file, index=False, encoding='utf-8')
    
    # Save statistics
    stats = {
        'total_examples': len(instruction_data),
        'categories': df['category'].value_counts().to_dict(),
        'avg_instruction_length': df['instruction'].str.len().mean(),
        'avg_input_length': df['input'].str.len().mean(),
        'avg_output_length': df['output'].str.len().mean(),
    }
    
    stats_file = os.path.join(args.output_dir, 'dataset_stats.json')
    with open(stats_file, 'w', encoding='utf-8') as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)
    
    print(f"\nDataset saved to:")
    print(f"  📄 {train_file}")
    print(f"  📊 {csv_file}")
    print(f"  📈 {stats_file}")
    
    print(f"\nDataset Statistics:")
    print(f"  Total examples: {stats['total_examples']}")
    print(f"  Categories: {stats['categories']}")
    print(f"  Avg lengths - Instruction: {stats['avg_instruction_length']:.1f}, Input: {stats['avg_input_length']:.1f}, Output: {stats['avg_output_length']:.1f}")
    
    # Show sample
    print(f"\nSample training example:")
    print(f"Instruction: {instruction_data[0]['instruction']}")
    print(f"Input: {instruction_data[0]['input'][:200]}...")
    print(f"Output: {instruction_data[0]['output'][:200]}...")

if __name__ == "__main__":
    main()