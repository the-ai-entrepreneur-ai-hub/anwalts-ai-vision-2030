#!/usr/bin/env python3
"""
German Legal Model Evaluation Metrics

This script provides comprehensive evaluation capabilities for German legal language models,
including specialized metrics for legal domain understanding, text quality, and performance benchmarks.

Usage:
    python evaluation_metrics.py --model path/to/model --test-data test.jsonl
    python evaluation_metrics.py --config evaluation_config.yaml
"""

import argparse
import json
import logging
import re
import yaml
from pathlib import Path
from typing import List, Dict, Union, Tuple, Optional
from dataclasses import dataclass
import numpy as np
import pandas as pd
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
from datasets import load_dataset, Dataset
from sklearn.metrics import accuracy_score, precision_recall_fscore_support, classification_report
from rouge import Rouge
from bert_score import score as bert_score
import sacrebleu
from tqdm import tqdm
import matplotlib.pyplot as plt
import seaborn as sns

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('evaluation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class EvaluationConfig:
    """Configuration for evaluation pipeline"""
    
    # Model settings
    model_path: str
    tokenizer_path: Optional[str] = None
    
    # Test data
    test_data_path: str
    test_data_format: str = "jsonl"  # jsonl, csv, hf_dataset
    
    # Evaluation settings
    batch_size: int = 1
    max_length: int = 512
    max_new_tokens: int = 100
    temperature: float = 0.7
    top_p: float = 0.95
    
    # Metrics to compute
    compute_perplexity: bool = True
    compute_rouge: bool = True
    compute_bert_score: bool = True
    compute_legal_metrics: bool = True
    compute_bleu: bool = False
    
    # Legal-specific evaluation
    legal_terms_file: Optional[str] = None
    expected_citations_file: Optional[str] = None
    
    # Output settings
    output_dir: str = "./evaluation_results"
    save_predictions: bool = True
    generate_report: bool = True

class GermanLegalEvaluator:
    """Comprehensive evaluator for German legal models"""
    
    def __init__(self, config: EvaluationConfig):
        self.config = config
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        # German legal terminology for evaluation
        self.legal_terms = {
            "laws": [
                "BGB", "Bürgerliches Gesetzbuch", "StGB", "Strafgesetzbuch",
                "HGB", "Handelsgesetzbuch", "GG", "Grundgesetz",
                "ZPO", "Zivilprozessordnung", "StPO", "Strafprozessordnung",
                "VwGO", "Verwaltungsgerichtsordnung", "FGO", "Finanzgerichtsordnung",
                "SGG", "Sozialgerichtsgesetz", "AO", "Abgabenordnung",
                "EStG", "Einkommensteuergesetz", "UStG", "Umsatzsteuergesetz"
            ],
            "courts": [
                "BGH", "Bundesgerichtshof", "BVerfG", "Bundesverfassungsgericht",
                "BVerwG", "Bundesverwaltungsgericht", "BSG", "Bundessozialgericht",
                "BFH", "Bundesfinanzhof", "BAG", "Bundesarbeitsgericht",
                "OLG", "Oberlandesgericht", "LG", "Landgericht",
                "AG", "Amtsgericht", "VG", "Verwaltungsgericht"
            ],
            "legal_concepts": [
                "Rechtsfähigkeit", "Handlungsfähigkeit", "Deliktsfähigkeit",
                "Verjährung", "Verschulden", "Fahrlässigkeit", "Vorsatz",
                "Schadensersatz", "Gewährleistung", "Anfechtung", "Nichtigkeit",
                "Widerruf", "Kündigung", "Vertragsstrafe", "Pfandrecht"
            ],
            "procedures": [
                "Urteil", "Beschluss", "Verfügung", "Berufung", "Revision",
                "Beschwerde", "Einspruch", "Antrag", "Klage", "Anzeige",
                "Vollstreckung", "Zwangsvollstreckung", "Arrest", "Einstweilige Verfügung"
            ]
        }
        
        # Load model and tokenizer
        self.model, self.tokenizer = self._load_model()
        self.pipeline = self._create_pipeline()
        
        # Initialize metrics
        self.rouge = Rouge()
        self.results = {}
        
    def _load_model(self) -> Tuple[AutoModelForCausalLM, AutoTokenizer]:
        """Load the trained model and tokenizer"""
        logger.info(f"Loading model from {self.config.model_path}")
        
        tokenizer_path = self.config.tokenizer_path or self.config.model_path
        
        try:
            tokenizer = AutoTokenizer.from_pretrained(tokenizer_path)
            model = AutoModelForCausalLM.from_pretrained(
                self.config.model_path,
                torch_dtype=torch.float16,
                device_map="auto"
            )
            
            if tokenizer.pad_token is None:
                tokenizer.pad_token = tokenizer.eos_token
            
            logger.info("Model loaded successfully")
            return model, tokenizer
            
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            raise
    
    def _create_pipeline(self):
        """Create text generation pipeline"""
        return pipeline(
            "text-generation",
            model=self.model,
            tokenizer=self.tokenizer,
            torch_dtype=torch.float16,
            device_map="auto"
        )
    
    def load_test_data(self) -> Dataset:
        """Load test dataset"""
        logger.info(f"Loading test data from {self.config.test_data_path}")
        
        if self.config.test_data_format == "jsonl":
            data = []
            with open(self.config.test_data_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        data.append(json.loads(line))
            dataset = Dataset.from_pandas(pd.DataFrame(data))
            
        elif self.config.test_data_format == "csv":
            df = pd.read_csv(self.config.test_data_path)
            dataset = Dataset.from_pandas(df)
            
        elif self.config.test_data_format == "hf_dataset":
            dataset = load_dataset(self.config.test_data_path)
            
        else:
            raise ValueError(f"Unsupported test data format: {self.config.test_data_format}")
        
        logger.info(f"Loaded {len(dataset)} test examples")
        return dataset
    
    def compute_perplexity(self, texts: List[str]) -> float:
        """Compute perplexity on test texts"""
        logger.info("Computing perplexity...")
        
        total_loss = 0
        total_tokens = 0
        
        self.model.eval()
        with torch.no_grad():
            for text in tqdm(texts, desc="Computing perplexity"):
                try:
                    # Tokenize
                    inputs = self.tokenizer(
                        text,
                        return_tensors="pt",
                        truncation=True,
                        max_length=self.config.max_length,
                        padding=False
                    ).to(self.device)
                    
                    # Forward pass
                    outputs = self.model(**inputs, labels=inputs["input_ids"])
                    loss = outputs.loss
                    
                    # Accumulate
                    num_tokens = inputs["input_ids"].size(1)
                    total_loss += loss.item() * num_tokens
                    total_tokens += num_tokens
                    
                except Exception as e:
                    logger.warning(f"Error processing text for perplexity: {e}")
                    continue
        
        if total_tokens == 0:
            return float('inf')
        
        avg_loss = total_loss / total_tokens
        perplexity = np.exp(avg_loss)
        
        logger.info(f"Perplexity: {perplexity:.2f}")
        return perplexity
    
    def generate_responses(self, prompts: List[str]) -> List[str]:
        """Generate responses for given prompts"""
        logger.info("Generating responses...")
        
        responses = []
        
        for prompt in tqdm(prompts, desc="Generating responses"):
            try:
                result = self.pipeline(
                    prompt,
                    max_new_tokens=self.config.max_new_tokens,
                    temperature=self.config.temperature,
                    top_p=self.config.top_p,
                    do_sample=True,
                    pad_token_id=self.tokenizer.eos_token_id,
                    return_full_text=False
                )
                
                generated_text = result[0]['generated_text'] if result else ""
                responses.append(generated_text.strip())
                
            except Exception as e:
                logger.warning(f"Error generating response: {e}")
                responses.append("")
        
        return responses
    
    def compute_rouge_scores(self, predictions: List[str], references: List[str]) -> Dict:
        """Compute ROUGE scores"""
        logger.info("Computing ROUGE scores...")
        
        # Filter out empty predictions/references
        valid_pairs = [(p, r) for p, r in zip(predictions, references) if p.strip() and r.strip()]
        
        if not valid_pairs:
            logger.warning("No valid prediction-reference pairs for ROUGE")
            return {"rouge-1": 0, "rouge-2": 0, "rouge-l": 0}
        
        predictions_clean, references_clean = zip(*valid_pairs)
        
        try:
            scores = self.rouge.get_scores(
                list(predictions_clean),
                list(references_clean),
                avg=True
            )
            
            rouge_scores = {
                "rouge-1": scores["rouge-1"]["f"],
                "rouge-2": scores["rouge-2"]["f"],
                "rouge-l": scores["rouge-l"]["f"]
            }
            
            logger.info(f"ROUGE-1: {rouge_scores['rouge-1']:.3f}")
            logger.info(f"ROUGE-2: {rouge_scores['rouge-2']:.3f}")
            logger.info(f"ROUGE-L: {rouge_scores['rouge-l']:.3f}")
            
            return rouge_scores
            
        except Exception as e:
            logger.error(f"Error computing ROUGE scores: {e}")
            return {"rouge-1": 0, "rouge-2": 0, "rouge-l": 0}
    
    def compute_bert_scores(self, predictions: List[str], references: List[str]) -> Dict:
        """Compute BERTScore"""
        logger.info("Computing BERTScore...")
        
        # Filter out empty predictions/references
        valid_pairs = [(p, r) for p, r in zip(predictions, references) if p.strip() and r.strip()]
        
        if not valid_pairs:
            logger.warning("No valid prediction-reference pairs for BERTScore")
            return {"bert_precision": 0, "bert_recall": 0, "bert_f1": 0}
        
        predictions_clean, references_clean = zip(*valid_pairs)
        
        try:
            P, R, F1 = bert_score(
                list(predictions_clean),
                list(references_clean),
                lang="de",
                verbose=False
            )
            
            bert_scores = {
                "bert_precision": P.mean().item(),
                "bert_recall": R.mean().item(),
                "bert_f1": F1.mean().item()
            }
            
            logger.info(f"BERTScore P: {bert_scores['bert_precision']:.3f}")
            logger.info(f"BERTScore R: {bert_scores['bert_recall']:.3f}")
            logger.info(f"BERTScore F1: {bert_scores['bert_f1']:.3f}")
            
            return bert_scores
            
        except Exception as e:
            logger.error(f"Error computing BERTScore: {e}")
            return {"bert_precision": 0, "bert_recall": 0, "bert_f1": 0}
    
    def compute_bleu_score(self, predictions: List[str], references: List[str]) -> float:
        """Compute BLEU score"""
        logger.info("Computing BLEU score...")
        
        # Filter and format for BLEU
        valid_pairs = [(p, [r]) for p, r in zip(predictions, references) if p.strip() and r.strip()]
        
        if not valid_pairs:
            logger.warning("No valid prediction-reference pairs for BLEU")
            return 0.0
        
        predictions_clean, references_clean = zip(*valid_pairs)
        
        try:
            bleu_score = sacrebleu.corpus_bleu(
                list(predictions_clean),
                list(references_clean)
            ).score
            
            logger.info(f"BLEU score: {bleu_score:.3f}")
            return bleu_score
            
        except Exception as e:
            logger.error(f"Error computing BLEU score: {e}")
            return 0.0
    
    def evaluate_legal_knowledge(self, texts: List[str]) -> Dict:
        """Evaluate legal domain knowledge"""
        logger.info("Evaluating legal knowledge...")
        
        legal_metrics = {
            "legal_term_coverage": 0,
            "paragraph_reference_accuracy": 0,
            "court_reference_accuracy": 0,
            "legal_concept_usage": 0,
            "avg_legal_terms_per_text": 0,
            "citation_format_accuracy": 0
        }
        
        total_texts = len(texts)
        if total_texts == 0:
            return legal_metrics
        
        legal_term_counts = []
        texts_with_legal_terms = 0
        texts_with_paragraph_refs = 0
        texts_with_court_refs = 0
        texts_with_legal_concepts = 0
        proper_citations = 0
        total_citations = 0
        
        for text in texts:
            text_lower = text.lower()
            
            # Count legal terms
            legal_terms_found = 0
            for category, terms in self.legal_terms.items():
                for term in terms:
                    if term.lower() in text_lower:
                        legal_terms_found += 1
            
            legal_term_counts.append(legal_terms_found)
            if legal_terms_found > 0:
                texts_with_legal_terms += 1
            
            # Check for specific categories
            if any(term.lower() in text_lower for term in self.legal_terms["laws"]):
                texts_with_paragraph_refs += 1
            
            if any(term.lower() in text_lower for term in self.legal_terms["courts"]):
                texts_with_court_refs += 1
            
            if any(term.lower() in text_lower for term in self.legal_terms["legal_concepts"]):
                texts_with_legal_concepts += 1
            
            # Check citation formats
            paragraph_refs = re.findall(r'§\s*\d+', text)
            article_refs = re.findall(r'Art\.\s*\d+', text)
            
            for ref in paragraph_refs + article_refs:
                total_citations += 1
                # Check if properly formatted (basic check)
                if re.match(r'(§|Art\.)\s+\d+', ref):
                    proper_citations += 1
        
        # Calculate metrics
        legal_metrics["legal_term_coverage"] = texts_with_legal_terms / total_texts
        legal_metrics["paragraph_reference_accuracy"] = texts_with_paragraph_refs / total_texts
        legal_metrics["court_reference_accuracy"] = texts_with_court_refs / total_texts
        legal_metrics["legal_concept_usage"] = texts_with_legal_concepts / total_texts
        legal_metrics["avg_legal_terms_per_text"] = np.mean(legal_term_counts) if legal_term_counts else 0
        legal_metrics["citation_format_accuracy"] = proper_citations / total_citations if total_citations > 0 else 0
        
        logger.info(f"Legal term coverage: {legal_metrics['legal_term_coverage']:.3f}")
        logger.info(f"Average legal terms per text: {legal_metrics['avg_legal_terms_per_text']:.1f}")
        logger.info(f"Citation format accuracy: {legal_metrics['citation_format_accuracy']:.3f}")
        
        return legal_metrics
    
    def evaluate_text_quality(self, texts: List[str]) -> Dict:
        """Evaluate general text quality metrics"""
        logger.info("Evaluating text quality...")
        
        quality_metrics = {
            "avg_length": 0,
            "avg_sentences": 0,
            "avg_words_per_sentence": 0,
            "repetition_rate": 0,
            "coherence_score": 0,
            "readability_score": 0
        }
        
        if not texts:
            return quality_metrics
        
        lengths = []
        sentence_counts = []
        words_per_sentence = []
        repetition_scores = []
        
        for text in texts:
            if not text.strip():
                continue
            
            # Basic metrics
            words = text.split()
            lengths.append(len(words))
            
            # Sentence count
            sentences = re.split(r'[.!?]+', text)
            sentences = [s.strip() for s in sentences if s.strip()]
            sentence_counts.append(len(sentences))
            
            if sentences:
                words_per_sentence.append(len(words) / len(sentences))
            
            # Repetition analysis
            if len(words) > 0:
                unique_words = len(set(words))
                repetition_scores.append(1 - (unique_words / len(words)))
        
        # Calculate averages
        quality_metrics["avg_length"] = np.mean(lengths) if lengths else 0
        quality_metrics["avg_sentences"] = np.mean(sentence_counts) if sentence_counts else 0
        quality_metrics["avg_words_per_sentence"] = np.mean(words_per_sentence) if words_per_sentence else 0
        quality_metrics["repetition_rate"] = np.mean(repetition_scores) if repetition_scores else 0
        
        # Simplified coherence score (based on sentence length consistency)
        if words_per_sentence:
            std_words_per_sentence = np.std(words_per_sentence)
            mean_words_per_sentence = np.mean(words_per_sentence)
            if mean_words_per_sentence > 0:
                quality_metrics["coherence_score"] = 1 / (1 + std_words_per_sentence / mean_words_per_sentence)
        
        logger.info(f"Average length: {quality_metrics['avg_length']:.1f} words")
        logger.info(f"Average sentences: {quality_metrics['avg_sentences']:.1f}")
        logger.info(f"Repetition rate: {quality_metrics['repetition_rate']:.3f}")
        
        return quality_metrics
    
    def run_evaluation(self, dataset: Dataset) -> Dict:
        """Run complete evaluation pipeline"""
        logger.info("Starting comprehensive evaluation...")
        
        # Extract data from dataset
        if "text" in dataset.column_names:
            texts = dataset["text"]
        elif "input" in dataset.column_names:
            texts = dataset["input"]
        else:
            raise ValueError("Dataset must contain 'text' or 'input' column")
        
        references = dataset.get("output", dataset.get("target", []))
        prompts = dataset.get("instruction", texts)
        
        results = {}
        
        # Generate responses
        if prompts and any(p.strip() for p in prompts):
            logger.info("Generating model responses...")
            predictions = self.generate_responses(prompts[:100])  # Limit for demo
            results["predictions"] = predictions
        else:
            predictions = []
        
        # 1. Perplexity
        if self.config.compute_perplexity:
            perplexity = self.compute_perplexity(texts[:100])  # Limit for demo
            results["perplexity"] = perplexity
        
        # 2. ROUGE scores (if we have references)
        if self.config.compute_rouge and references and predictions:
            rouge_scores = self.compute_rouge_scores(predictions, references[:len(predictions)])
            results.update(rouge_scores)
        
        # 3. BERTScore (if we have references)
        if self.config.compute_bert_score and references and predictions:
            try:
                bert_scores = self.compute_bert_scores(predictions, references[:len(predictions)])
                results.update(bert_scores)
            except Exception as e:
                logger.warning(f"BERTScore computation failed: {e}")
        
        # 4. BLEU score (if we have references)
        if self.config.compute_bleu and references and predictions:
            bleu_score = self.compute_bleu_score(predictions, references[:len(predictions)])
            results["bleu"] = bleu_score
        
        # 5. Legal knowledge evaluation
        if self.config.compute_legal_metrics:
            eval_texts = predictions if predictions else texts[:100]
            legal_metrics = self.evaluate_legal_knowledge(eval_texts)
            results.update(legal_metrics)
        
        # 6. Text quality evaluation
        eval_texts = predictions if predictions else texts[:100]
        quality_metrics = self.evaluate_text_quality(eval_texts)
        results.update(quality_metrics)
        
        # Store results
        self.results = results
        
        logger.info("Evaluation completed successfully!")
        return results
    
    def save_results(self, output_dir: Path):
        """Save evaluation results"""
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Save detailed results
        results_file = output_dir / "evaluation_results.json"
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False, default=str)
        
        logger.info(f"Results saved to {results_file}")
        
        # Save predictions if available
        if self.config.save_predictions and "predictions" in self.results:
            predictions_file = output_dir / "predictions.jsonl"
            with open(predictions_file, 'w', encoding='utf-8') as f:
                for pred in self.results["predictions"]:
                    json.dump({"prediction": pred}, f, ensure_ascii=False)
                    f.write('\n')
            
            logger.info(f"Predictions saved to {predictions_file}")
    
    def generate_report(self, output_dir: Path):
        """Generate comprehensive evaluation report"""
        if not self.results:
            logger.warning("No results available for report generation")
            return
        
        output_dir = Path(output_dir)
        report_file = output_dir / "evaluation_report.md"
        
        report = f"""# German Legal Model Evaluation Report

## Model Information
- **Model Path**: {self.config.model_path}
- **Evaluation Date**: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}
- **Test Data**: {self.config.test_data_path}

## Performance Summary

### Language Model Metrics
"""
        
        if "perplexity" in self.results:
            report += f"- **Perplexity**: {self.results['perplexity']:.2f}\n"
        
        if "rouge-1" in self.results:
            report += f"- **ROUGE-1**: {self.results['rouge-1']:.3f}\n"
            report += f"- **ROUGE-2**: {self.results['rouge-2']:.3f}\n"
            report += f"- **ROUGE-L**: {self.results['rouge-l']:.3f}\n"
        
        if "bert_f1" in self.results:
            report += f"- **BERTScore F1**: {self.results['bert_f1']:.3f}\n"
        
        if "bleu" in self.results:
            report += f"- **BLEU Score**: {self.results['bleu']:.3f}\n"
        
        report += "\n### Legal Domain Metrics\n"
        
        if "legal_term_coverage" in self.results:
            report += f"- **Legal Term Coverage**: {self.results['legal_term_coverage']:.3f}\n"
            report += f"- **Paragraph Reference Accuracy**: {self.results['paragraph_reference_accuracy']:.3f}\n"
            report += f"- **Court Reference Accuracy**: {self.results['court_reference_accuracy']:.3f}\n"
            report += f"- **Legal Concept Usage**: {self.results['legal_concept_usage']:.3f}\n"
            report += f"- **Avg Legal Terms per Text**: {self.results['avg_legal_terms_per_text']:.1f}\n"
            report += f"- **Citation Format Accuracy**: {self.results['citation_format_accuracy']:.3f}\n"
        
        report += "\n### Text Quality Metrics\n"
        
        if "avg_length" in self.results:
            report += f"- **Average Length**: {self.results['avg_length']:.1f} words\n"
            report += f"- **Average Sentences**: {self.results['avg_sentences']:.1f}\n"
            report += f"- **Words per Sentence**: {self.results['avg_words_per_sentence']:.1f}\n"
            report += f"- **Repetition Rate**: {self.results['repetition_rate']:.3f}\n"
            report += f"- **Coherence Score**: {self.results.get('coherence_score', 0):.3f}\n"
        
        # Performance interpretation
        report += "\n## Performance Interpretation\n\n"
        
        if "perplexity" in self.results:
            ppl = self.results["perplexity"]
            if ppl < 20:
                report += "✅ **Excellent** language modeling performance (Perplexity < 20)\n"
            elif ppl < 50:
                report += "🟡 **Good** language modeling performance (Perplexity 20-50)\n"
            else:
                report += "❌ **Poor** language modeling performance (Perplexity > 50)\n"
        
        if "legal_term_coverage" in self.results:
            coverage = self.results["legal_term_coverage"]
            if coverage > 0.7:
                report += "✅ **Strong** legal domain knowledge coverage\n"
            elif coverage > 0.4:
                report += "🟡 **Moderate** legal domain knowledge coverage\n"
            else:
                report += "❌ **Weak** legal domain knowledge coverage\n"
        
        if "bert_f1" in self.results:
            bert_f1 = self.results["bert_f1"]
            if bert_f1 > 0.8:
                report += "✅ **High** semantic similarity to references\n"
            elif bert_f1 > 0.6:
                report += "🟡 **Moderate** semantic similarity to references\n"
            else:
                report += "❌ **Low** semantic similarity to references\n"
        
        # Recommendations
        report += "\n## Recommendations\n\n"
        
        if "legal_term_coverage" in self.results and self.results["legal_term_coverage"] < 0.5:
            report += "- 📚 **Increase legal terminology** in training data\n"
        
        if "perplexity" in self.results and self.results["perplexity"] > 50:
            report += "- 🔄 **Additional training** may improve language modeling\n"
        
        if "repetition_rate" in self.results and self.results["repetition_rate"] > 0.3:
            report += "- 🔀 **Reduce repetition** through diverse training examples\n"
        
        if "citation_format_accuracy" in self.results and self.results["citation_format_accuracy"] < 0.7:
            report += "- 📖 **Improve citation formatting** through targeted training\n"
        
        # Configuration details
        report += f"\n## Evaluation Configuration\n\n"
        report += f"- **Batch Size**: {self.config.batch_size}\n"
        report += f"- **Max Length**: {self.config.max_length}\n"
        report += f"- **Temperature**: {self.config.temperature}\n"
        report += f"- **Top-p**: {self.config.top_p}\n"
        report += f"- **Max New Tokens**: {self.config.max_new_tokens}\n"
        
        # Save report
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        logger.info(f"Evaluation report saved to {report_file}")
    
    def create_visualizations(self, output_dir: Path):
        """Create evaluation visualizations"""
        output_dir = Path(output_dir)
        
        if not self.results:
            logger.warning("No results available for visualization")
            return
        
        # Set style
        plt.style.use('seaborn-v0_8')
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        fig.suptitle('German Legal Model Evaluation Results', fontsize=16, fontweight='bold')
        
        # 1. Performance metrics radar chart
        if all(key in self.results for key in ["rouge-1", "rouge-2", "rouge-l", "bert_f1"]):
            ax = axes[0, 0]
            metrics = ["ROUGE-1", "ROUGE-2", "ROUGE-L", "BERTScore F1"]
            values = [
                self.results["rouge-1"],
                self.results["rouge-2"], 
                self.results["rouge-l"],
                self.results["bert_f1"]
            ]
            
            ax.bar(metrics, values, alpha=0.7, color='skyblue')
            ax.set_title('Text Generation Metrics')
            ax.set_ylabel('Score')
            ax.set_ylim(0, 1)
            plt.setp(ax.get_xticklabels(), rotation=45, ha='right')
        
        # 2. Legal knowledge metrics
        if "legal_term_coverage" in self.results:
            ax = axes[0, 1]
            legal_metrics = [
                "Term Coverage",
                "Paragraph Refs",
                "Court Refs", 
                "Legal Concepts",
                "Citation Format"
            ]
            legal_values = [
                self.results.get("legal_term_coverage", 0),
                self.results.get("paragraph_reference_accuracy", 0),
                self.results.get("court_reference_accuracy", 0),
                self.results.get("legal_concept_usage", 0),
                self.results.get("citation_format_accuracy", 0)
            ]
            
            ax.bar(legal_metrics, legal_values, alpha=0.7, color='lightcoral')
            ax.set_title('Legal Domain Knowledge')
            ax.set_ylabel('Score')
            ax.set_ylim(0, 1)
            plt.setp(ax.get_xticklabels(), rotation=45, ha='right')
        
        # 3. Text quality metrics
        if "avg_length" in self.results:
            ax = axes[1, 0]
            quality_metrics = ["Avg Length", "Avg Sentences", "Words/Sentence"]
            quality_values = [
                self.results.get("avg_length", 0) / 100,  # Normalize
                self.results.get("avg_sentences", 0) / 10,  # Normalize
                self.results.get("avg_words_per_sentence", 0) / 20  # Normalize
            ]
            
            ax.bar(quality_metrics, quality_values, alpha=0.7, color='lightgreen')
            ax.set_title('Text Quality (Normalized)')
            ax.set_ylabel('Normalized Score')
            plt.setp(ax.get_xticklabels(), rotation=45, ha='right')
        
        # 4. Overall performance gauge
        ax = axes[1, 1]
        if "bert_f1" in self.results and "legal_term_coverage" in self.results:
            # Calculate overall score
            text_score = (self.results.get("rouge-1", 0) + 
                         self.results.get("bert_f1", 0)) / 2
            legal_score = self.results.get("legal_term_coverage", 0)
            overall_score = (text_score + legal_score) / 2
            
            # Create gauge-like visualization
            categories = ['Text Quality', 'Legal Knowledge', 'Overall']
            scores = [text_score, legal_score, overall_score]
            colors = ['blue', 'red', 'green']
            
            bars = ax.barh(categories, scores, color=colors, alpha=0.7)
            ax.set_xlim(0, 1)
            ax.set_title('Overall Performance')
            ax.set_xlabel('Score')
            
            # Add score labels
            for i, (bar, score) in enumerate(zip(bars, scores)):
                ax.text(score + 0.02, i, f'{score:.3f}', va='center')
        
        plt.tight_layout()
        
        # Save plot
        plot_file = output_dir / "evaluation_plots.png"
        plt.savefig(plot_file, dpi=300, bbox_inches='tight')
        plt.close()
        
        logger.info(f"Visualizations saved to {plot_file}")

def load_config(config_path: str) -> EvaluationConfig:
    """Load configuration from YAML file"""
    with open(config_path, 'r', encoding='utf-8') as f:
        config_dict = yaml.safe_load(f)
    
    return EvaluationConfig(**config_dict)

def main():
    parser = argparse.ArgumentParser(description="Evaluate German legal models")
    parser.add_argument("--model", "-m", required=True, help="Path to trained model")
    parser.add_argument("--test-data", "-t", required=True, help="Path to test data")
    parser.add_argument("--config", "-c", help="Configuration file (YAML)")
    parser.add_argument("--output", "-o", default="./evaluation_results", help="Output directory")
    parser.add_argument("--batch-size", type=int, default=1, help="Batch size for evaluation")
    parser.add_argument("--max-length", type=int, default=512, help="Maximum sequence length")
    parser.add_argument("--format", choices=["jsonl", "csv", "hf_dataset"], default="jsonl", help="Test data format")
    
    args = parser.parse_args()
    
    # Load configuration
    if args.config:
        config = load_config(args.config)
    else:
        config = EvaluationConfig(
            model_path=args.model,
            test_data_path=args.test_data,
            test_data_format=args.format,
            output_dir=args.output,
            batch_size=args.batch_size,
            max_length=args.max_length
        )
    
    # Initialize evaluator
    evaluator = GermanLegalEvaluator(config)
    
    # Load test data
    test_dataset = evaluator.load_test_data()
    
    # Run evaluation
    results = evaluator.run_evaluation(test_dataset)
    
    # Save results
    output_dir = Path(config.output_dir)
    evaluator.save_results(output_dir)
    
    # Generate report
    if config.generate_report:
        evaluator.generate_report(output_dir)
    
    # Create visualizations
    evaluator.create_visualizations(output_dir)
    
    # Print summary
    print("\n" + "="*60)
    print("EVALUATION SUMMARY")
    print("="*60)
    
    if "perplexity" in results:
        print(f"Perplexity: {results['perplexity']:.2f}")
    
    if "rouge-1" in results:
        print(f"ROUGE-1: {results['rouge-1']:.3f}")
        print(f"ROUGE-2: {results['rouge-2']:.3f}")
        print(f"ROUGE-L: {results['rouge-l']:.3f}")
    
    if "bert_f1" in results:
        print(f"BERTScore F1: {results['bert_f1']:.3f}")
    
    if "legal_term_coverage" in results:
        print(f"Legal Term Coverage: {results['legal_term_coverage']:.3f}")
    
    print(f"\nDetailed results saved to: {output_dir}")
    
    logger.info("Evaluation completed successfully!")

if __name__ == "__main__":
    main()