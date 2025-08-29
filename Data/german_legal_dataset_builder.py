#!/usr/bin/env python3
"""
German Legal Dataset Builder
Focused approach to building a comprehensive German legal training dataset
"""

import json
import re
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
import hashlib
import random
import requests
from urllib.parse import quote_plus
import time

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class GermanLegalDatasetBuilder:
    """Build comprehensive German legal dataset"""
    
    def __init__(self, output_dir: str = "final_expanded_data"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.collected_hashes = set()
        
        # German legal domain vocabulary
        self.legal_vocabulary = {
            'civil_law': [
                'Bürgerliches Gesetzbuch', 'BGB', 'Schuldrecht', 'Sachenrecht', 'Familienrecht',
                'Erbrecht', 'Kaufvertrag', 'Mietvertrag', 'Werkvertrag', 'Dienstvertrag',
                'Schadensersatz', 'Gewährleistung', 'Verjährung', 'Eigentum', 'Besitz'
            ],
            'criminal_law': [
                'Strafgesetzbuch', 'StGB', 'Straftat', 'Schuld', 'Vorsatz', 'Fahrlässigkeit',
                'Diebstahl', 'Betrug', 'Körperverletzung', 'Mord', 'Totschlag', 'Raub',
                'Untreue', 'Geldwäsche', 'Steuerhinterziehung', 'Urkundenfälschung'
            ],
            'constitutional_law': [
                'Grundgesetz', 'GG', 'Grundrechte', 'Menschenwürde', 'Persönlichkeitsrecht',
                'Meinungsfreiheit', 'Versammlungsfreiheit', 'Eigentumsgarantie', 'Rechtsstaat',
                'Gewaltenteilung', 'Bundesverfassungsgericht', 'Verfassungsbeschwerde'
            ],
            'administrative_law': [
                'Verwaltungsrecht', 'Verwaltungsakt', 'Ermessen', 'Verhältnismäßigkeit',
                'Rechtsmittel', 'Widerspruch', 'Anfechtungsklage', 'Verpflichtungsklage',
                'Baurecht', 'Umweltrecht', 'Steuerrecht', 'Sozialrecht'
            ]
        }
        
        # Legal instruction templates
        self.instruction_templates = {
            'explanation': [
                "Erklären Sie die rechtliche Bedeutung von: {}",
                "Was versteht man unter dem Begriff '{}'?",
                "Definieren Sie den Rechtsbegriff '{}'",
                "Erläutern Sie die juristische Bedeutung von: {}"
            ],
            'analysis': [
                "Analysieren Sie die rechtlichen Aspekte von: {}",
                "Welche rechtlichen Konsequenzen ergeben sich aus: {}?",
                "Bewerten Sie rechtlich folgenden Sachverhalt: {}",
                "Prüfen Sie die Rechtmäßigkeit von: {}"
            ],
            'application': [
                "Wie wird {} in der Praxis angewendet?",
                "Welche Voraussetzungen müssen für {} erfüllt sein?",
                "Unter welchen Umständen greift {}?",
                "Wie ist {} rechtlich zu beurteilen?"
            ],
            'comparison': [
                "Unterscheiden Sie zwischen {} und verwandten Begriffen",
                "Grenzen Sie {} von ähnlichen Rechtsinstituten ab",
                "Welche Gemeinsamkeiten und Unterschiede bestehen bei {}?",
                "Vergleichen Sie {} mit anderen Rechtsnormen"
            ]
        }
        
        # Common German legal phrases and structures
        self.legal_phrases = [
            "Nach der ständigen Rechtsprechung des Bundesgerichtshofs",
            "Die herrschende Meinung in der Literatur vertritt",
            "Aus systematischer Sicht ist zu beachten",
            "Der Wortlaut des Gesetzes besagt eindeutig",
            "Teleologisch betrachtet ergibt sich",
            "Im Rahmen der verfassungskonformen Auslegung",
            "Die Interessenabwägung führt zu dem Ergebnis",
            "Unter Berücksichtigung der Verkehrsanschauung"
        ]
    
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
    
    def load_base_data(self) -> List[Dict[str, Any]]:
        """Load existing base data"""
        base_data = []
        
        # Try to load from prepared_data
        prepared_data_dir = Path("prepared_data")
        if prepared_data_dir.exists():
            for file_name in ['train.jsonl', 'validation.jsonl', 'test.jsonl']:
                file_path = prepared_data_dir / file_name
                if file_path.exists():
                    with open(file_path, 'r', encoding='utf-8') as f:
                        for line in f:
                            try:
                                data = json.loads(line.strip())
                                base_data.append(data)
                            except json.JSONDecodeError:
                                continue
        
        # Try to load from expanded_legal_data
        expanded_data_dir = Path("expanded_legal_data")
        if expanded_data_dir.exists():
            for file_name in ['train.jsonl', 'validation.jsonl', 'test.jsonl']:
                file_path = expanded_data_dir / file_name
                if file_path.exists():
                    with open(file_path, 'r', encoding='utf-8') as f:
                        for line in f:
                            try:
                                data = json.loads(line.strip())
                                base_data.append(data)
                            except json.JSONDecodeError:
                                continue
        
        logger.info(f"Loaded {len(base_data)} base examples")
        return base_data
    
    def generate_legal_qa_pairs(self, count: int = 2000) -> List[Dict[str, Any]]:
        """Generate legal question-answer pairs"""
        qa_pairs = []
        
        logger.info(f"Generating {count} legal Q&A pairs...")
        
        for _ in range(count):
            # Choose random legal domain
            domain = random.choice(list(self.legal_vocabulary.keys()))
            terms = self.legal_vocabulary[domain]
            
            # Choose random term and instruction type
            term = random.choice(terms)
            instruction_type = random.choice(list(self.instruction_templates.keys()))
            template = random.choice(self.instruction_templates[instruction_type])
            
            # Generate question
            question = template.format(term)
            
            # Generate answer based on term and domain
            answer = self.generate_legal_answer(term, domain)
            
            # Create instruction format
            instruction_text = f"<s>[INST] {question} [/INST] {answer} </s>"
            
            if not self.is_duplicate(instruction_text):
                qa_pairs.append({
                    'text': instruction_text,
                    'source': 'synthetic_qa',
                    'category': domain,
                    'term': term,
                    'instruction_type': instruction_type
                })
        
        logger.info(f"Generated {len(qa_pairs)} Q&A pairs")
        return qa_pairs
    
    def generate_legal_answer(self, term: str, domain: str) -> str:
        """Generate a legal answer for a given term and domain"""
        # Start with a legal phrase
        opening = random.choice(self.legal_phrases)
        
        # Generate domain-specific content
        if domain == 'civil_law':
            content = self.generate_civil_law_content(term)
        elif domain == 'criminal_law':
            content = self.generate_criminal_law_content(term)
        elif domain == 'constitutional_law':
            content = self.generate_constitutional_law_content(term)
        elif domain == 'administrative_law':
            content = self.generate_administrative_law_content(term)
        else:
            content = self.generate_general_legal_content(term)
        
        # Combine opening and content
        full_answer = f"{opening}, dass {content}"
        
        # Add conclusion
        conclusions = [
            "Daher ist eine sorgfältige rechtliche Prüfung erforderlich.",
            "Dies führt zu entsprechenden Rechtsfolgen.",
            "Dabei sind die besonderen Umstände des Einzelfalls zu berücksichtigen.",
            "Eine abweichende Beurteilung kommt nur in Ausnahmefällen in Betracht."
        ]
        
        conclusion = random.choice(conclusions)
        full_answer += f" {conclusion}"
        
        return full_answer
    
    def generate_civil_law_content(self, term: str) -> str:
        """Generate civil law specific content"""
        templates = [
            f"{term} im Bürgerlichen Recht als wichtiges Rechtsinstitut zu verstehen ist",
            f"die Anwendung von {term} bestimmte Voraussetzungen erfüllt sein müssen",
            f"{term} sowohl Rechte als auch Pflichten der Beteiligten begründet",
            f"bei {term} die Interessenlage aller Parteien zu berücksichtigen ist"
        ]
        return random.choice(templates)
    
    def generate_criminal_law_content(self, term: str) -> str:
        """Generate criminal law specific content"""
        templates = [
            f"{term} als Straftatbestand bestimmte objektive und subjektive Merkmale aufweist",
            f"für die Verwirklichung von {term} Vorsatz oder Fahrlässigkeit erforderlich ist",
            f"{term} mit entsprechenden Rechtsfolgen im Strafrecht verbunden ist",
            f"die Abgrenzung von {term} zu anderen Straftaten von praktischer Bedeutung ist"
        ]
        return random.choice(templates)
    
    def generate_constitutional_law_content(self, term: str) -> str:
        """Generate constitutional law specific content"""
        templates = [
            f"{term} als Grundrecht verfassungsrechtlich geschützt ist",
            f"die Schranken von {term} verfassungskonform auszulegen sind",
            f"{term} im System der Grundrechte eine zentrale Stellung einnimmt",
            f"bei {term} eine Abwägung mit anderen Verfassungsgütern erforderlich ist"
        ]
        return random.choice(templates)
    
    def generate_administrative_law_content(self, term: str) -> str:
        """Generate administrative law specific content"""
        templates = [
            f"{term} im Verwaltungsrecht bestimmte Verfahrensvorschriften zu beachten sind",
            f"die Anwendung von {term} dem Verhältnismäßigkeitsgrundsatz unterliegt",
            f"{term} sowohl materiell-rechtliche als auch verfahrensrechtliche Aspekte umfasst",
            f"bei {term} die Grundsätze ordnungsgemäßer Verwaltung zu beachten sind"
        ]
        return random.choice(templates)
    
    def generate_general_legal_content(self, term: str) -> str:
        """Generate general legal content"""
        templates = [
            f"{term} in der Rechtspraxis von großer Bedeutung ist",
            f"die rechtliche Bewertung von {term} eine umfassende Würdigung erfordert",
            f"{term} sowohl theoretische als auch praktische Relevanz besitzt",
            f"bei der Anwendung von {term} die Rechtssicherheit zu gewährleisten ist"
        ]
        return random.choice(templates)
    
    def generate_case_studies(self, count: int = 500) -> List[Dict[str, Any]]:
        """Generate legal case studies"""
        case_studies = []
        
        logger.info(f"Generating {count} case studies...")
        
        for _ in range(count):
            # Generate a case scenario
            case_scenario = self.generate_case_scenario()
            
            # Generate legal analysis
            legal_analysis = self.generate_case_analysis(case_scenario)
            
            # Create instruction format
            instruction = "Analysieren Sie folgenden Rechtsfall und erläutern Sie die rechtlichen Aspekte:"
            instruction_text = f"<s>[INST] {instruction}\n\nSachverhalt: {case_scenario} [/INST] {legal_analysis} </s>"
            
            if not self.is_duplicate(instruction_text):
                case_studies.append({
                    'text': instruction_text,
                    'source': 'synthetic_case_study',
                    'category': 'case_analysis'
                })
        
        logger.info(f"Generated {len(case_studies)} case studies")
        return case_studies
    
    def generate_case_scenario(self) -> str:
        """Generate a legal case scenario"""
        scenarios = [
            "A und B schließen einen Kaufvertrag über ein gebrauchtes Fahrzeug. Nach der Übergabe stellt sich heraus, dass erhebliche Mängel vorliegen.",
            "Mieter M zahlt drei Monate lang keine Miete. Vermieter V möchte das Mietverhältnis kündigen.",
            "Arbeitnehmer AN wird fristlos gekündigt, nachdem er wiederholt zu spät zur Arbeit erschienen ist.",
            "Unternehmer U liefert mangelhafte Ware an Kunde K. K verweigert die Zahlung des Kaufpreises.",
            "Eheleute E wollen sich scheiden lassen. Streitig ist die Aufteilung des gemeinsamen Vermögens."
        ]
        
        return random.choice(scenarios)
    
    def generate_case_analysis(self, scenario: str) -> str:
        """Generate legal analysis for a case scenario"""
        analysis_parts = [
            "Rechtlich ist zunächst zu prüfen, welche Anspruchsgrundlagen in Betracht kommen.",
            "Die Voraussetzungen der einschlägigen Rechtsnormen sind im Einzelnen zu untersuchen.",
            "Dabei sind sowohl die Interessen der beteiligten Parteien als auch die Rechtsprechung zu berücksichtigen.",
            "Im Ergebnis führt dies zu folgenden rechtlichen Konsequenzen für die Beteiligten."
        ]
        
        return " ".join(analysis_parts)
    
    def create_final_dataset(self) -> int:
        """Create the final expanded dataset"""
        logger.info("Creating final expanded dataset...")
        
        all_data = []
        
        # 1. Load base data
        base_data = self.load_base_data()
        all_data.extend(base_data)
        
        # 2. Generate Q&A pairs
        qa_pairs = self.generate_legal_qa_pairs(2000)
        all_data.extend(qa_pairs)
        
        # 3. Generate case studies
        case_studies = self.generate_case_studies(500)
        all_data.extend(case_studies)
        
        # 4. Remove duplicates and apply quality filtering
        unique_data = []
        for item in all_data:
            text = item.get('text', '')
            if (len(text) > 50 and 
                len(text) < 8000 and 
                not self.is_duplicate(text)):
                unique_data.append(item)
        
        # 5. Shuffle and create splits
        random.shuffle(unique_data)
        
        total = len(unique_data)
        train_size = int(0.8 * total)
        val_size = int(0.1 * total)
        
        train_data = unique_data[:train_size]
        val_data = unique_data[train_size:train_size + val_size]
        test_data = unique_data[train_size + val_size:]
        
        # 6. Save splits
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
            
            logger.info(f"Saved {len(split_data)} examples to {split_name}.jsonl")
        
        # 7. Save metadata
        metadata = {
            'total_samples': len(unique_data),
            'splits': {name: len(split_data) for name, split_data in splits.items()},
            'format': 'instruction_tuning',
            'language': 'german',
            'domain': 'legal',
            'expansion_method': 'synthetic_generation',
            'build_date': '2025-08-05',
            'sources': list(set(item.get('source', 'unknown') for item in unique_data)),
            'categories': list(set(item.get('category', 'unknown') for item in unique_data))
        }
        
        with open(self.output_dir / 'metadata.json', 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Final dataset created with {len(unique_data)} examples!")
        return len(unique_data)

def main():
    """Main execution function"""
    builder = GermanLegalDatasetBuilder()
    total_examples = builder.create_final_dataset()
    print(f"Successfully built German legal dataset with {total_examples} examples!")

if __name__ == "__main__":
    main()