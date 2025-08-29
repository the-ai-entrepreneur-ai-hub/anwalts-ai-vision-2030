#!/usr/bin/env python3
"""
Massive German Legal Dataset Generator
Creates a large-scale German legal training dataset using multiple strategies
"""

import json
import re
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import hashlib
import random
import string
from datetime import datetime, timedelta
import uuid

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MassiveLegalDatasetGenerator:
    """Generate massive German legal dataset with diverse content"""
    
    def __init__(self, output_dir: str = "massive_legal_data"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.generated_count = 0
        
        # Comprehensive German legal vocabulary by domain
        self.legal_domains = {
            'buergerliches_recht': {
                'gesetze': ['BGB', 'Bürgerliches Gesetzbuch'],
                'begriffe': [
                    'Willenserklärung', 'Rechtsgeschäft', 'Vertrag', 'Kaufvertrag', 'Mietvertrag',
                    'Werkvertrag', 'Dienstvertrag', 'Schadensersatz', 'Gewährleistung', 'Verjährung',
                    'Eigentum', 'Besitz', 'Pfandrecht', 'Hypothek', 'Grundschuld', 'Erbrecht',
                    'Testament', 'Erbfolge', 'Pflichtteil', 'Familienrecht', 'Eheschließung',
                    'Scheidung', 'Unterhalt', 'Sorgerecht', 'Vormundschaft'
                ],
                'paragraphen': list(range(1, 2400))
            },
            'strafrecht': {
                'gesetze': ['StGB', 'Strafgesetzbuch', 'StPO', 'Strafprozessordnung'],
                'begriffe': [
                    'Straftat', 'Schuld', 'Vorsatz', 'Fahrlässigkeit', 'Versuch', 'Täterschaft',
                    'Teilnahme', 'Mord', 'Totschlag', 'Körperverletzung', 'Diebstahl', 'Raub',
                    'Betrug', 'Untreue', 'Urkundenfälschung', 'Beleidigung', 'Verleumdung',
                    'Nötigung', 'Erpressung', 'Geldwäsche', 'Steuerhinterziehung'
                ],
                'paragraphen': list(range(1, 358))
            },
            'verfassungsrecht': {
                'gesetze': ['GG', 'Grundgesetz', 'BVerfGG'],
                'begriffe': [
                    'Grundrechte', 'Menschenwürde', 'Persönlichkeitsrecht', 'Meinungsfreiheit',
                    'Pressefreiheit', 'Versammlungsfreiheit', 'Vereinigungsfreiheit', 'Religionsfreiheit',
                    'Eigentumsgarantie', 'Berufsfreiheit', 'Rechtsstaat', 'Gewaltenteilung',
                    'Bundesstaat', 'Verfassungsbeschwerde', 'Normenkontrolle'
                ],
                'paragraphen': list(range(1, 146))
            },
            'verwaltungsrecht': {
                'gesetze': ['VwVfG', 'Verwaltungsverfahrensgesetz', 'VwGO'],
                'begriffe': [
                    'Verwaltungsakt', 'Ermessen', 'Verhältnismäßigkeit', 'Rechtsmäßigkeit',
                    'Zweckmäßigkeit', 'Ermessenfehler', 'Beurteilungsspielraum', 'Widerspruch',
                    'Anfechtungsklage', 'Verpflichtungsklage', 'Feststellungsklage', 'Baurecht',
                    'Umweltrecht', 'Steuerrecht', 'Sozialrecht', 'Polizeirecht'
                ],
                'paragraphen': list(range(1, 200))
            },
            'arbeitsrecht': {
                'gesetze': ['ArbZG', 'Arbeitszeitgesetz', 'KSchG', 'Kündigungsschutzgesetz'],
                'begriffe': [
                    'Arbeitsvertrag', 'Arbeitszeit', 'Überstunden', 'Urlaub', 'Kündigung',
                    'Kündigungsschutz', 'Abmahnung', 'Zeugnis', 'Lohn', 'Gehalt',
                    'Tarifvertrag', 'Betriebsrat', 'Mitbestimmung', 'Streik', 'Aussperrung'
                ],
                'paragraphen': list(range(1, 150))
            }
        }
        
        # German legal instruction templates
        self.instruction_patterns = {
            'definition': [
                "Was versteht man unter dem Begriff '{}'?",
                "Definieren Sie den Rechtsbegriff '{}'.",
                "Erklären Sie die rechtliche Bedeutung von '{}'.",
                "Was bedeutet '{}' im juristischen Sinne?",
                "Wie ist der Begriff '{}' rechtlich zu verstehen?"
            ],
            'explanation': [
                "Erläutern Sie die Regelung des {} {}.",
                "Welche Bedeutung hat {} {} für die Rechtspraxis?",
                "Erklären Sie den Inhalt von {} {}.",
                "Was regelt {} {}?",
                "Wie ist {} {} zu interpretieren?"
            ],
            'application': [
                "Unter welchen Voraussetzungen ist {} anwendbar?",
                "Wann greift die Regelung des {} ein?",
                "In welchen Fällen ist {} relevant?",
                "Welche Voraussetzungen müssen für {} erfüllt sein?",
                "Wie wird {} in der Praxis angewendet?"
            ],
            'consequences': [
                "Welche Rechtsfolgen ergeben sich aus {}?",
                "Was sind die Konsequenzen von {}?",
                "Welche rechtlichen Auswirkungen hat {}?",
                "Welche Folgen hat die Anwendung von {}?",
                "Was bewirkt {} rechtlich?"
            ],
            'comparison': [
                "Wie unterscheidet sich {} von ähnlichen Rechtsinstituten?",
                "Grenzen Sie {} von verwandten Begriffen ab.",
                "Was ist der Unterschied zwischen {} und anderen Normen?",
                "Wie verhält sich {} zu anderen Rechtsnormen?",
                "Welche Abgrenzung besteht zwischen {} und ähnlichen Begriffen?"
            ]
        }
        
        # Legal answer construction templates
        self.answer_structures = {
            'definition_answer': [
                "Nach der Legaldefinition in {} {} versteht man unter {} folgendes:",
                "Der Begriff {} ist in {} {} geregelt und bedeutet:",
                "Rechtlich ist {} als {} zu verstehen, wie aus {} {} hervorgeht:",
                "{} wird in {} {} definiert als:"
            ],
            'explanation_answer': [
                "Die Regelung des {} {} besagt, dass",
                "Nach der Vorschrift des {} {} ist",
                "Die Norm des {} {} bestimmt, dass",
                "Gemäß {} {} gilt, dass"
            ],
            'legal_reasoning': [
                "Nach der ständigen Rechtsprechung des Bundesgerichtshofs",
                "Die herrschende Meinung in der Literatur vertritt die Auffassung",
                "Aus systematischer Sicht ist zu beachten",
                "Der Wortlaut des Gesetzes besagt eindeutig",
                "Teleologisch betrachtet ergibt sich",
                "Im Rahmen der verfassungskonformen Auslegung",
                "Die Interessenabwägung führt zu dem Ergebnis",
                "Unter Berücksichtigung der Verkehrsanschauung"
            ]
        }
        
        # Legal conclusions
        self.legal_conclusions = [
            "Daher ist eine sorgfältige rechtliche Prüfung im Einzelfall erforderlich.",
            "Dies führt zu entsprechenden Rechtsfolgen für die Beteiligten.",
            "Dabei sind stets die besonderen Umstände des konkreten Falls zu berücksichtigen.",
            "Eine abweichende Beurteilung kommt nur in begründeten Ausnahmefällen in Betracht.",
            "Die praktische Anwendung erfordert eine umfassende Würdigung aller Umstände.",
            "Im Zweifelsfall ist eine fachkundige Rechtsberatung zu empfehlen.",
            "Die Rechtssicherheit gebietet eine einheitliche Anwendung dieser Grundsätze."
        ]
    
    def generate_legal_qa_pair(self, domain: str) -> Dict[str, Any]:
        """Generate a single legal Q&A pair for a domain"""
        domain_data = self.legal_domains[domain]
        
        # Choose random elements
        gesetz = random.choice(domain_data['gesetze'])
        begriff = random.choice(domain_data['begriffe'])
        paragraph = random.choice(domain_data['paragraphen'])
        
        # Choose instruction type and pattern
        instruction_type = random.choice(list(self.instruction_patterns.keys()))
        instruction_template = random.choice(self.instruction_patterns[instruction_type])
        
        # Generate question based on type
        if instruction_type in ['definition']:
            question = instruction_template.format(begriff)
        elif instruction_type in ['explanation', 'application', 'consequences']:
            question = instruction_template.format(gesetz, paragraph)
        else:  # comparison
            question = instruction_template.format(begriff)
        
        # Generate answer
        answer = self.generate_legal_answer(domain, gesetz, begriff, paragraph, instruction_type)
        
        # Create instruction format
        instruction_text = f"<s>[INST] {question} [/INST] {answer} </s>"
        
        return {
            'text': instruction_text,
            'source': 'synthetic_legal_qa',
            'category': domain,
            'instruction_type': instruction_type,
            'legal_term': begriff,
            'legal_source': f"{gesetz} § {paragraph}",
            'id': str(uuid.uuid4())
        }
    
    def generate_legal_answer(self, domain: str, gesetz: str, begriff: str, paragraph: int, instruction_type: str) -> str:
        """Generate a comprehensive legal answer"""
        # Start with legal reasoning
        opening = random.choice(self.answer_structures['legal_reasoning'])
        
        # Add specific content based on instruction type
        if instruction_type == 'definition':
            definition_template = random.choice(self.answer_structures['definition_answer'])
            main_content = definition_template.format(begriff, gesetz, paragraph, self.generate_definition_content(domain, begriff))
        elif instruction_type == 'explanation':
            explanation_template = random.choice(self.answer_structures['explanation_answer'])
            main_content = explanation_template.format(gesetz, paragraph) + " " + self.generate_explanation_content(domain, begriff)
        else:
            main_content = self.generate_general_content(domain, begriff, gesetz, paragraph)
        
        # Add domain-specific elaboration
        elaboration = self.generate_domain_elaboration(domain, begriff)
        
        # Add conclusion
        conclusion = random.choice(self.legal_conclusions)
        
        # Combine all parts
        full_answer = f"{opening}, dass {main_content}. {elaboration} {conclusion}"
        
        return full_answer
    
    def generate_definition_content(self, domain: str, begriff: str) -> str:
        """Generate definition content for a legal term"""
        templates = {
            'buergerliches_recht': f"{begriff} ein zentrales Institut des Zivilrechts darstellt, das die Rechtsbeziehungen zwischen Privatpersonen regelt",
            'strafrecht': f"{begriff} als Straftatbestand bestimmte objektive und subjektive Tatbestandsmerkmale aufweist",
            'verfassungsrecht': f"{begriff} als verfassungsrechtlich geschütztes Gut von fundamentaler Bedeutung für die Rechtsordnung ist",
            'verwaltungsrecht': f"{begriff} ein Instrument des Verwaltungshandelns darstellt, das bestimmten Verfahrensvorschriften unterliegt",
            'arbeitsrecht': f"{begriff} die Rechtsbeziehungen zwischen Arbeitgeber und Arbeitnehmer regelt"
        }
        return templates.get(domain, f"{begriff} ein wichtiges Rechtsinstitut darstellt")
    
    def generate_explanation_content(self, domain: str, begriff: str) -> str:
        """Generate explanation content"""
        explanations = [
            f"die Anwendung von {begriff} bestimmte rechtliche Voraussetzungen erfüllt sein müssen",
            f"{begriff} sowohl materielle als auch verfahrensrechtliche Aspekte umfasst",
            f"bei {begriff} die Grundsätze der Verhältnismäßigkeit und Rechtssicherheit zu beachten sind",
            f"die Auslegung von {begriff} nach den anerkannten Methoden der Rechtsfindung zu erfolgen hat"
        ]
        return random.choice(explanations)
    
    def generate_general_content(self, domain: str, begriff: str, gesetz: str, paragraph: int) -> str:
        """Generate general content"""
        contents = [
            f"die Regelung des {gesetz} § {paragraph} bezüglich {begriff} von praktischer Relevanz ist",
            f"{begriff} im Kontext des {gesetz} eine wichtige Funktion erfüllt",
            f"die Anwendung von {begriff} nach {gesetz} § {paragraph} spezielle Anforderungen stellt",
            f"{begriff} als Teil des {gesetz} systematisch einzuordnen ist"
        ]
        return random.choice(contents)
    
    def generate_domain_elaboration(self, domain: str, begriff: str) -> str:
        """Generate domain-specific elaboration"""
        elaborations = {
            'buergerliches_recht': f"Im Zivilrecht ist {begriff} von erheblicher praktischer Bedeutung für die Vertragsgestaltung und Schadensprävention.",
            'strafrecht': f"Die strafrechtliche Bewertung von {begriff} erfordert eine genaue Prüfung der Tatbestandsmerkmale und der Schuld.",
            'verfassungsrecht': f"Verfassungsrechtlich ist {begriff} im Lichte der Grundrechte und des Rechtsstaatsprinzips zu beurteilen.",
            'verwaltungsrecht': f"Im Verwaltungsrecht unterliegt {begriff} den allgemeinen Grundsätzen ordnungsgemäßer Verwaltung.",
            'arbeitsrecht': f"Arbeitsrechtlich ist {begriff} unter Berücksichtigung des Arbeitnehmerschutzes zu bewerten."
        }
        return elaborations.get(domain, f"Rechtlich ist {begriff} von großer Bedeutung für die Rechtsanwendung.")
    
    def generate_case_study(self) -> Dict[str, Any]:
        """Generate a legal case study"""
        # Choose random domain
        domain = random.choice(list(self.legal_domains.keys()))
        
        # Generate case facts
        case_facts = self.generate_case_facts(domain)
        
        # Generate legal question
        legal_question = self.generate_legal_question(domain)
        
        # Generate legal analysis
        legal_analysis = self.generate_legal_analysis(domain, case_facts)
        
        # Create full case study
        full_case = f"Sachverhalt: {case_facts}\n\nRechtsfrage: {legal_question}"
        instruction_text = f"<s>[INST] Analysieren Sie folgenden Rechtsfall:\n\n{full_case} [/INST] {legal_analysis} </s>"
        
        return {
            'text': instruction_text,
            'source': 'synthetic_case_study',
            'category': f'{domain}_case',
            'case_type': 'legal_analysis',
            'id': str(uuid.uuid4())
        }
    
    def generate_case_facts(self, domain: str) -> str:
        """Generate case facts based on domain"""
        facts_templates = {
            'buergerliches_recht': [
                "A und B schließen einen Kaufvertrag über ein gebrauchtes Fahrzeug zum Preis von 15.000 Euro. Nach der Übergabe stellt A fest, dass der Motor einen erheblichen Defekt aufweist.",
                "Mieter M zahlt seit drei Monaten keine Miete mehr. Vermieter V möchte das Mietverhältnis fristlos kündigen und Räumung verlangen.",
                "Unternehmer U liefert mangelhafte Ware an Kunde K. K verweigert die Zahlung und verlangt Nacherfüllung."
            ],
            'strafrecht': [
                "A schlägt B mit der Faust ins Gesicht und verletzt ihn dabei erheblich. B muss im Krankenhaus behandelt werden.",
                "A nimmt heimlich das Portemonnaie des B aus dessen Jacke und entfernt sich damit.",
                "A täuscht gegenüber B vor, ein wertvolles Kunstwerk zu verkaufen, obwohl es sich um eine Fälschung handelt."
            ],
            'verfassungsrecht': [
                "Die Gemeinde G erlässt eine Satzung, die Demonstrationen in der Innenstadt grundsätzlich verbietet.",
                "Ein Gesetz sieht vor, dass bestimmte Berufsgruppen ihre Tätigkeit nur noch mit staatlicher Genehmigung ausüben dürfen.",
                "Eine Behörde durchsucht ohne richterlichen Beschluss die Wohnung des A."
            ],
            'verwaltungsrecht': [
                "Die Bauaufsichtsbehörde lehnt den Bauantrag des A ohne ausreichende Begründung ab.",
                "A erhält einen Bußgeldbescheid wegen Geschwindigkeitsüberschreitung und legt Widerspruch ein.",
                "Die Gemeinde G verweigert A die Gaststättenerlaubnis ohne ersichtlichen Grund."
            ],
            'arbeitsrecht': [
                "Arbeitgeber AG kündigt Arbeitnehmer AN fristlos, nachdem dieser einmalig zu spät zur Arbeit erschienen ist.",
                "AN verlangt Zahlung von Überstunden, die AG bestreitet die Arbeitszeit.",
                "AG verweigert AN den vertraglich zugesicherten Urlaub."
            ]
        }
        
        templates = facts_templates.get(domain, facts_templates['buergerliches_recht'])
        return random.choice(templates)
    
    def generate_legal_question(self, domain: str) -> str:
        """Generate legal question for case"""
        questions = [
            "Welche Ansprüche bestehen?",
            "Ist das Verhalten rechtmäßig?",
            "Welche Rechtsfolgen ergeben sich?",
            "Liegt ein Rechtsverstoß vor?",
            "Welche rechtlichen Schritte sind möglich?"
        ]
        return random.choice(questions)
    
    def generate_legal_analysis(self, domain: str, case_facts: str) -> str:
        """Generate legal analysis for case"""
        analysis_parts = [
            "Rechtlich ist zunächst zu prüfen, welche Anspruchsgrundlagen in Betracht kommen.",
            "Die Voraussetzungen der einschlägigen Rechtsnormen sind im Einzelnen zu untersuchen.",
            "Dabei sind sowohl die Interessen der beteiligten Parteien als auch die Rechtsprechung zu berücksichtigen.",
            "Die tatbestandlichen Voraussetzungen müssen vollständig erfüllt sein.",
            "Rechtswidrigkeit und Verschulden sind gesondert zu prüfen.",
            "Im Ergebnis führt dies zu folgenden rechtlichen Konsequenzen für die Beteiligten."
        ]
        
        # Add domain-specific analysis
        domain_analysis = {
            'buergerliches_recht': "Im Rahmen des Zivilrechts sind insbesondere die Gewährleistungsrechte und Schadensersatzansprüche zu prüfen.",
            'strafrecht': "Strafrechtlich ist zu untersuchen, ob die objektiven und subjektiven Tatbestandsmerkmale erfüllt sind.",
            'verfassungsrecht': "Verfassungsrechtlich ist eine Grundrechtsprüfung durchzuführen und die Verhältnismäßigkeit zu beachten.",
            'verwaltungsrecht': "Verwaltungsrechtlich sind die Rechtmäßigkeitsvoraussetzungen des Verwaltungshandelns zu prüfen.",
            'arbeitsrecht': "Arbeitsrechtlich sind die besonderen Schutzvorschriften für Arbeitnehmer zu berücksichtigen."
        }
        
        specific_analysis = domain_analysis.get(domain, "Eine umfassende rechtliche Würdigung ist erforderlich.")
        
        return " ".join(analysis_parts[:4]) + f" {specific_analysis} " + analysis_parts[-1]
    
    def generate_massive_dataset(self, target_size: int = 10000) -> int:
        """Generate massive dataset with target size"""
        logger.info(f"Generating massive German legal dataset with target size: {target_size}")
        
        all_data = []
        
        # Load existing data first
        existing_data = self.load_existing_data()
        all_data.extend(existing_data)
        logger.info(f"Loaded {len(existing_data)} existing examples")
        
        # Calculate how many new examples to generate
        remaining_target = target_size - len(existing_data)
        
        if remaining_target <= 0:
            logger.info("Target size already reached with existing data")
            return len(all_data)
        
        # Generate Q&A pairs (80% of new data)
        qa_target = int(remaining_target * 0.8)
        qa_per_domain = qa_target // len(self.legal_domains)
        
        for domain in self.legal_domains.keys():
            logger.info(f"Generating {qa_per_domain} Q&A pairs for {domain}")
            for i in range(qa_per_domain):
                qa_pair = self.generate_legal_qa_pair(domain)
                all_data.append(qa_pair)
                
                if (i + 1) % 100 == 0:
                    logger.info(f"Generated {i + 1}/{qa_per_domain} Q&A pairs for {domain}")
        
        # Generate case studies (20% of new data)
        case_target = remaining_target - qa_target
        logger.info(f"Generating {case_target} case studies")
        
        for i in range(case_target):
            case_study = self.generate_case_study()
            all_data.append(case_study)
            
            if (i + 1) % 50 == 0:
                logger.info(f"Generated {i + 1}/{case_target} case studies")
        
        # Shuffle and create splits
        random.shuffle(all_data)
        
        total = len(all_data)
        train_size = int(0.8 * total)
        val_size = int(0.1 * total)
        
        train_data = all_data[:train_size]
        val_data = all_data[train_size:train_size + val_size]
        test_data = all_data[train_size + val_size:]
        
        # Save data
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
        
        # Save metadata
        sources = list(set(item.get('source', 'unknown') for item in all_data))
        categories = list(set(item.get('category', 'unknown') for item in all_data))
        
        metadata = {
            'total_samples': len(all_data),
            'splits': {name: len(split_data) for name, split_data in splits.items()},
            'format': 'instruction_tuning',
            'language': 'german',
            'domain': 'legal',
            'generation_method': 'massive_synthetic_generation',
            'build_date': datetime.now().isoformat(),
            'target_size': target_size,
            'domains_covered': list(self.legal_domains.keys()),
            'sources': sources,
            'categories': categories,
            'instruction_types': list(self.instruction_patterns.keys())
        }
        
        with open(self.output_dir / 'metadata.json', 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Massive dataset generation complete! Total: {len(all_data)} examples")
        return len(all_data)
    
    def load_existing_data(self) -> List[Dict[str, Any]]:
        """Load existing data from all available sources"""
        existing_data = []
        
        # Check multiple source directories
        source_dirs = [
            Path("prepared_data"),
            Path("expanded_legal_data"),
            Path("final_expanded_data")
        ]
        
        for source_dir in source_dirs:
            if source_dir.exists():
                for file_name in ['train.jsonl', 'validation.jsonl', 'test.jsonl']:
                    file_path = source_dir / file_name
                    if file_path.exists():
                        logger.info(f"Loading from {file_path}")
                        with open(file_path, 'r', encoding='utf-8') as f:
                            for line in f:
                                try:
                                    data = json.loads(line.strip())
                                    # Add source tracking
                                    data['original_source'] = str(source_dir)
                                    existing_data.append(data)
                                except json.JSONDecodeError:
                                    continue
        
        return existing_data

def main():
    """Main execution function"""
    generator = MassiveLegalDatasetGenerator()
    
    # Generate massive dataset - targeting 10,000 examples
    total_examples = generator.generate_massive_dataset(target_size=10000)
    print(f"Successfully generated massive German legal dataset with {total_examples} examples!")

if __name__ == "__main__":
    main()