# German Legal Model Training Guide - Free Resources Setup

## Table of Contents
1. [Google Colab Pro/Pro+ Setup](#google-colab-pro-setup)
2. [Alternative Free Training Platforms](#alternative-free-platforms)
3. [Hugging Face Integration](#hugging-face-integration)
4. [Training Optimization Techniques](#training-optimization)
5. [Dataset Preparation Workflows](#dataset-preparation)
6. [LoRA/QLoRA Configuration](#lora-qlora-configuration)
7. [Code Examples](#code-examples)
8. [Configuration Files](#configuration-files)

---

## Google Colab Pro/Pro+ Setup

### GPU Configuration and Requirements

**Colab Pro vs Pro+ Comparison:**
- **Colab Pro ($9.99/month)**: Access to faster GPUs (T4, P100), longer runtimes (24h)
- **Colab Pro+ ($49.99/month)**: Premium GPUs (V100, A100), background execution, priority access

### Initial Setup Script

```python
# Check GPU availability and type
!nvidia-smi

# Install required libraries
!pip install transformers==4.36.0
!pip install datasets==2.15.0
!pip install peft==0.7.1
!pip install bitsandbytes==0.41.3
!pip install accelerate==0.25.0
!pip install torch==2.1.0
!pip install trl==0.7.4
!pip install wandb==0.16.0
!pip install sentencepiece==0.1.99
!pip install protobuf==3.20.3

# Verify installations
import torch
print(f"PyTorch version: {torch.__version__}")
print(f"CUDA available: {torch.cuda.is_available()}")
print(f"GPU count: {torch.cuda.device_count()}")
if torch.cuda.is_available():
    print(f"GPU name: {torch.cuda.get_device_name(0)}")
    print(f"GPU memory: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB")
```

### Memory Management Setup

```python
import gc
import torch

def clear_memory():
    """Clear GPU and system memory"""
    gc.collect()
    torch.cuda.empty_cache()
    if torch.cuda.is_available():
        torch.cuda.synchronize()

def check_memory():
    """Check current memory usage"""
    if torch.cuda.is_available():
        allocated = torch.cuda.memory_allocated() / 1024**3
        reserved = torch.cuda.memory_reserved() / 1024**3
        print(f"GPU Memory - Allocated: {allocated:.2f} GB, Reserved: {reserved:.2f} GB")
```

---

## Alternative Free Training Platforms

### 1. Kaggle Notebooks

**Setup:**
```python
# Kaggle-specific setup
import os
os.environ['KAGGLE_CONFIG_DIR'] = '/kaggle/working'

# Install packages (Kaggle has pre-installed many libraries)
!pip install peft bitsandbytes trl wandb

# GPU verification
!nvidia-smi
```

**Advantages:**
- 30 hours/week GPU time (P100)
- 20GB RAM
- Internet access
- Easy dataset integration

### 2. Paperspace Gradient

**Free Tier:**
- 6 hours/month GPU time
- M4000 GPU (8GB VRAM)
- Good for smaller models

```python
# Paperspace setup
!pip install papermill
!pip install gradient

# Environment setup
import os
os.environ['GRADIENT_ACCESS_TOKEN'] = 'your_token_here'
```

### 3. Lightning AI Studio

**Setup:**
```python
# Lightning AI specific setup
!pip install lightning-ai
!pip install lightning

# GPU configuration
import lightning as L
```

---

## Hugging Face Integration

### Authentication Setup

```python
from huggingface_hub import notebook_login
import os

# Login to Hugging Face
notebook_login()

# Alternative: Set token manually
# os.environ["HUGGINGFACE_HUB_TOKEN"] = "your_token_here"

# Verify authentication
from huggingface_hub import whoami
print(f"Logged in as: {whoami()}")
```

### Model and Dataset Integration

```python
from datasets import load_dataset
from transformers import AutoTokenizer, AutoModelForCausalLM

# Load German legal dataset (example)
dataset = load_dataset("your-username/german-legal-corpus")

# Load base model
model_name = "microsoft/DialoGPT-medium"  # or "meta-llama/Llama-2-7b-hf"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(
    model_name,
    torch_dtype=torch.float16,
    device_map="auto"
)

# Set pad token if not present
if tokenizer.pad_token is None:
    tokenizer.pad_token = tokenizer.eos_token
```

### Dataset Upload Script

```python
from datasets import Dataset
from huggingface_hub import HfApi
import pandas as pd

def upload_legal_dataset(data_path, dataset_name):
    """Upload German legal dataset to Hugging Face Hub"""
    
    # Load and prepare data
    df = pd.read_json(data_path, lines=True)
    dataset = Dataset.from_pandas(df)
    
    # Push to hub
    dataset.push_to_hub(f"your-username/{dataset_name}")
    print(f"Dataset uploaded: https://huggingface.co/datasets/your-username/{dataset_name}")

# Example usage
# upload_legal_dataset("german_legal_data.jsonl", "german-legal-corpus")
```

---

## Training Optimization Techniques

### 1. Gradient Checkpointing

```python
from transformers import TrainingArguments

training_args = TrainingArguments(
    output_dir="./german-legal-model",
    gradient_checkpointing=True,  # Save memory at cost of speed
    dataloader_pin_memory=False,  # Reduce memory usage
    max_grad_norm=1.0,  # Gradient clipping
    
    # Batch size optimization
    per_device_train_batch_size=1,
    gradient_accumulation_steps=16,  # Effective batch size = 1 * 16 = 16
    
    # Learning rate scheduling
    learning_rate=2e-4,
    lr_scheduler_type="cosine",
    warmup_ratio=0.03,
    
    # Efficiency settings
    fp16=True,  # Use mixed precision
    remove_unused_columns=False,
    
    # Saving and logging
    save_steps=500,
    logging_steps=10,
    save_total_limit=3,
    
    # Training duration
    num_train_epochs=3,
    max_steps=-1,
)
```

### 2. Dynamic Batch Size Adjustment

```python
def find_optimal_batch_size(model, tokenizer, dataset, max_batch_size=8):
    """Find the largest batch size that fits in memory"""
    
    for batch_size in range(max_batch_size, 0, -1):
        try:
            # Test batch
            batch = dataset.select(range(min(batch_size, len(dataset))))
            inputs = tokenizer(
                batch['text'],
                padding=True,
                truncation=True,
                max_length=512,
                return_tensors="pt"
            ).to(model.device)
            
            # Forward pass test
            with torch.no_grad():
                outputs = model(**inputs)
            
            print(f"Optimal batch size: {batch_size}")
            clear_memory()
            return batch_size
            
        except torch.cuda.OutOfMemoryError:
            clear_memory()
            continue
    
    return 1  # Fallback to batch size 1
```

### 3. Training Resumption

```python
import json
import os

def save_training_state(trainer, step, epoch, loss):
    """Save training state for resumption"""
    state = {
        "step": step,
        "epoch": epoch,
        "loss": loss,
        "model_path": trainer.args.output_dir
    }
    
    with open("training_state.json", "w") as f:
        json.dump(state, f)

def resume_training():
    """Resume training from saved state"""
    if os.path.exists("training_state.json"):
        with open("training_state.json", "r") as f:
            state = json.load(f)
        print(f"Resuming from step {state['step']}, epoch {state['epoch']}")
        return state
    return None
```

---

## Dataset Preparation Workflows

### German Legal Document Preprocessing

```python
import re
import pandas as pd
from datasets import Dataset
from typing import List, Dict

class GermanLegalPreprocessor:
    def __init__(self):
        self.legal_terms = {
            "BGB": "Bürgerliches Gesetzbuch",
            "StGB": "Strafgesetzbuch",
            "GG": "Grundgesetz",
            "ZPO": "Zivilprozessordnung"
        }
    
    def clean_text(self, text: str) -> str:
        """Clean German legal text"""
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Normalize quotation marks
        text = re.sub(r'[""„"]', '"', text)
        
        # Fix paragraph references
        text = re.sub(r'§\s*(\d+)', r'§ \1', text)
        
        # Remove page numbers and footnotes
        text = re.sub(r'\[\d+\]', '', text)
        
        return text.strip()
    
    def extract_legal_context(self, text: str) -> Dict[str, str]:
        """Extract legal context from text"""
        context = {
            "law_references": [],
            "paragraph_references": [],
            "court_references": []
        }
        
        # Extract law references
        for abbrev, full_name in self.legal_terms.items():
            if abbrev in text:
                context["law_references"].append(full_name)
        
        # Extract paragraph references
        paragraphs = re.findall(r'§\s*(\d+)', text)
        context["paragraph_references"] = list(set(paragraphs))
        
        # Extract court references
        courts = re.findall(r'(BGH|BVerfG|OLG|LG|AG)\s+[A-Z]', text)
        context["court_references"] = list(set(courts))
        
        return context
    
    def create_training_examples(self, documents: List[str]) -> List[Dict]:
        """Create training examples from legal documents"""
        examples = []
        
        for doc in documents:
            cleaned = self.clean_text(doc)
            context = self.extract_legal_context(cleaned)
            
            # Create instruction-response pairs
            example = {
                "instruction": "Analysiere das folgende Rechtsdokument:",
                "input": cleaned[:1000],  # Limit input length
                "output": self._generate_summary(cleaned),
                "legal_context": context
            }
            examples.append(example)
        
        return examples
    
    def _generate_summary(self, text: str) -> str:
        """Generate a basic summary (to be improved with actual summarization)"""
        sentences = text.split('. ')
        return '. '.join(sentences[:3]) + '.'

# Usage example
preprocessor = GermanLegalPreprocessor()
```

### Dataset Creation Script

```python
def create_legal_dataset(source_files: List[str], output_file: str):
    """Create a German legal training dataset"""
    
    all_examples = []
    preprocessor = GermanLegalPreprocessor()
    
    for file_path in source_files:
        print(f"Processing {file_path}...")
        
        # Read document
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Split into chunks
        chunks = [content[i:i+2000] for i in range(0, len(content), 1500)]
        
        # Process chunks
        examples = preprocessor.create_training_examples(chunks)
        all_examples.extend(examples)
    
    # Create dataset
    df = pd.DataFrame(all_examples)
    dataset = Dataset.from_pandas(df)
    
    # Save dataset
    dataset.save_to_disk(output_file)
    print(f"Dataset saved with {len(all_examples)} examples")
    
    return dataset
```

---

## LoRA/QLoRA Configuration

### QLoRA Setup (4-bit quantization)

```python
from transformers import BitsAndBytesConfig
from peft import LoraConfig, get_peft_model, TaskType

# 4-bit quantization config
bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_use_double_quant=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=torch.bfloat16
)

# Load quantized model
model = AutoModelForCausalLM.from_pretrained(
    model_name,
    quantization_config=bnb_config,
    device_map="auto",
    trust_remote_code=True
)

# LoRA configuration
lora_config = LoraConfig(
    r=16,  # Rank
    lora_alpha=32,  # Alpha parameter
    target_modules=[
        "q_proj", "v_proj", "k_proj", "o_proj",
        "gate_proj", "up_proj", "down_proj"
    ],
    lora_dropout=0.1,
    bias="none",
    task_type=TaskType.CAUSAL_LM
)

# Apply LoRA
model = get_peft_model(model, lora_config)
model.print_trainable_parameters()
```

### LoRA Training Configuration

```python
from trl import SFTTrainer

# Training arguments optimized for LoRA
training_args = TrainingArguments(
    output_dir="./german-legal-lora",
    num_train_epochs=3,
    per_device_train_batch_size=4,
    gradient_accumulation_steps=4,
    optim="paged_adamw_32bit",
    save_steps=500,
    logging_steps=25,
    learning_rate=2e-4,
    weight_decay=0.001,
    fp16=False,
    bf16=True,
    max_grad_norm=0.3,
    max_steps=-1,
    warmup_ratio=0.03,
    group_by_length=True,
    lr_scheduler_type="constant",
    report_to="wandb"
)

# SFT Trainer for LoRA
trainer = SFTTrainer(
    model=model,
    train_dataset=train_dataset,
    peft_config=lora_config,
    dataset_text_field="text",
    max_seq_length=512,
    tokenizer=tokenizer,
    args=training_args,
    packing=False,
)
```

---

## Code Examples

### Complete Colab Training Notebook

```python
# =============================================================================
# German Legal Model Training - Complete Colab Notebook
# =============================================================================

# 1. Initial Setup
!pip install -q transformers datasets peft bitsandbytes accelerate trl wandb

import torch
import pandas as pd
from datasets import Dataset, load_dataset
from transformers import (
    AutoTokenizer, AutoModelForCausalLM, 
    TrainingArguments, BitsAndBytesConfig
)
from peft import LoraConfig, get_peft_model, TaskType
from trl import SFTTrainer
import wandb

# 2. GPU Check and Memory Setup
print(f"GPU available: {torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"GPU: {torch.cuda.get_device_name(0)}")
    print(f"Memory: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB")

def clear_memory():
    import gc
    gc.collect()
    torch.cuda.empty_cache()

# 3. Model Configuration
MODEL_NAME = "microsoft/DialoGPT-medium"  # Smaller model for Colab
OUTPUT_DIR = "./german-legal-model"

# 4. Quantization Config (for larger models)
bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_use_double_quant=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=torch.bfloat16
)

# 5. Load Model and Tokenizer
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
if tokenizer.pad_token is None:
    tokenizer.pad_token = tokenizer.eos_token

model = AutoModelForCausalLM.from_pretrained(
    MODEL_NAME,
    # quantization_config=bnb_config,  # Uncomment for quantization
    torch_dtype=torch.float16,
    device_map="auto"
)

# 6. LoRA Configuration
lora_config = LoraConfig(
    r=16,
    lora_alpha=32,
    target_modules=["c_attn", "c_proj"],  # DialoGPT specific
    lora_dropout=0.1,
    bias="none",
    task_type=TaskType.CAUSAL_LM
)

model = get_peft_model(model, lora_config)
model.print_trainable_parameters()

# 7. Dataset Preparation
def prepare_dataset():
    # Sample German legal data (replace with your dataset)
    sample_data = [
        {
            "text": "Das Bürgerliche Gesetzbuch (BGB) regelt die Rechtsbeziehungen zwischen Privatpersonen. § 1 BGB definiert den Beginn der Rechtsfähigkeit."
        },
        {
            "text": "Nach § 433 BGB ist der Verkäufer verpflichtet, dem Käufer die Sache zu übergeben und das Eigentum zu verschaffen."
        }
        # Add more examples...
    ]
    
    df = pd.DataFrame(sample_data)
    return Dataset.from_pandas(df)

train_dataset = prepare_dataset()

# 8. Training Arguments
training_args = TrainingArguments(
    output_dir=OUTPUT_DIR,
    num_train_epochs=1,  # Reduced for free tier
    per_device_train_batch_size=1,
    gradient_accumulation_steps=8,
    optim="adamw_torch",
    save_steps=100,
    logging_steps=10,
    learning_rate=2e-4,
    weight_decay=0.001,
    fp16=True,
    max_grad_norm=0.3,
    warmup_ratio=0.03,
    lr_scheduler_type="cosine",
    save_total_limit=2,
    remove_unused_columns=False,
)

# 9. Initialize Trainer
trainer = SFTTrainer(
    model=model,
    train_dataset=train_dataset,
    dataset_text_field="text",
    max_seq_length=512,
    tokenizer=tokenizer,
    args=training_args,
    packing=False,
)

# 10. Start Training
print("Starting training...")
trainer.train()

# 11. Save Model
trainer.save_model()
tokenizer.save_pretrained(OUTPUT_DIR)

print("Training completed!")
```

### Dataset Loading and Preprocessing Script

```python
# =============================================================================
# Dataset Loading and Preprocessing
# =============================================================================

import json
import re
from pathlib import Path
from typing import List, Dict, Union
from datasets import Dataset
import pandas as pd

class GermanLegalDataProcessor:
    """Process German legal documents for training"""
    
    def __init__(self, max_length: int = 512):
        self.max_length = max_length
        self.legal_abbreviations = {
            "BGB": "Bürgerliches Gesetzbuch",
            "StGB": "Strafgesetzbuch",
            "HGB": "Handelsgesetzbuch",
            "GG": "Grundgesetz",
            "ZPO": "Zivilprozessordnung",
            "StPO": "Strafprozessordnung"
        }
    
    def load_documents(self, file_path: Union[str, Path]) -> List[str]:
        """Load documents from various formats"""
        file_path = Path(file_path)
        
        if file_path.suffix == '.json':
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return [item['text'] for item in data]
        
        elif file_path.suffix == '.jsonl':
            documents = []
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    data = json.loads(line)
                    documents.append(data['text'])
            return documents
        
        elif file_path.suffix == '.txt':
            with open(file_path, 'r', encoding='utf-8') as f:
                return [f.read()]
        
        else:
            raise ValueError(f"Unsupported file format: {file_path.suffix}")
    
    def preprocess_text(self, text: str) -> str:
        """Clean and preprocess German legal text"""
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Fix paragraph references
        text = re.sub(r'§\s*(\d+)', r'§ \1', text)
        
        # Normalize quotation marks
        text = re.sub(r'[""„"]', '"', text)
        
        # Remove footnote markers
        text = re.sub(r'\[\d+\]', '', text)
        
        # Clean up extra spaces
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def chunk_text(self, text: str, overlap: int = 50) -> List[str]:
        """Split text into overlapping chunks"""
        words = text.split()
        chunks = []
        
        chunk_size = self.max_length // 2  # Rough word estimate
        
        for i in range(0, len(words), chunk_size - overlap):
            chunk = ' '.join(words[i:i + chunk_size])
            if len(chunk.strip()) > 50:  # Minimum chunk size
                chunks.append(chunk)
        
        return chunks
    
    def create_training_format(self, text: str) -> Dict[str, str]:
        """Convert text to instruction-following format"""
        return {
            "instruction": "Erkläre den folgenden deutschen Rechtstext:",
            "input": text,
            "output": f"Dies ist ein Auszug aus einem deutschen Rechtsdokument: {text[:200]}..."
        }
    
    def process_dataset(self, input_files: List[str], output_file: str) -> Dataset:
        """Process multiple files into a training dataset"""
        all_examples = []
        
        for file_path in input_files:
            print(f"Processing {file_path}...")
            
            documents = self.load_documents(file_path)
            
            for doc in documents:
                # Preprocess
                clean_text = self.preprocess_text(doc)
                
                # Chunk if necessary
                if len(clean_text.split()) > self.max_length // 2:
                    chunks = self.chunk_text(clean_text)
                else:
                    chunks = [clean_text]
                
                # Create training examples
                for chunk in chunks:
                    example = self.create_training_format(chunk)
                    all_examples.append(example)
        
        # Create dataset
        df = pd.DataFrame(all_examples)
        dataset = Dataset.from_pandas(df)
        
        # Save
        dataset.save_to_disk(output_file)
        print(f"Saved {len(all_examples)} examples to {output_file}")
        
        return dataset

# Usage example
processor = GermanLegalDataProcessor(max_length=512)
dataset = processor.process_dataset(
    input_files=["legal_docs1.json", "legal_docs2.jsonl"],
    output_file="german_legal_dataset"
)
```

### Training Loop with Checkpointing

```python
# =============================================================================
# Training Loop with Checkpointing and Resuming
# =============================================================================

import os
import json
import time
from datetime import datetime
from transformers import TrainerCallback, TrainerState, TrainerControl
import wandb

class CheckpointCallback(TrainerCallback):
    """Custom callback for advanced checkpointing"""
    
    def __init__(self, save_every_n_steps: int = 100):
        self.save_every_n_steps = save_every_n_steps
        self.start_time = time.time()
    
    def on_step_end(self, args, state: TrainerState, control: TrainerControl, **kwargs):
        """Called at the end of each training step"""
        
        # Save custom checkpoint info
        if state.global_step % self.save_every_n_steps == 0:
            checkpoint_info = {
                "step": state.global_step,
                "epoch": state.epoch,
                "training_loss": state.log_history[-1].get("train_loss", 0) if state.log_history else 0,
                "learning_rate": state.log_history[-1].get("learning_rate", 0) if state.log_history else 0,
                "timestamp": datetime.now().isoformat(),
                "elapsed_time": time.time() - self.start_time
            }
            
            with open(os.path.join(args.output_dir, "checkpoint_info.json"), "w") as f:
                json.dump(checkpoint_info, f, indent=2)
        
        return control

class AdvancedTrainer:
    """Advanced trainer with memory management and resuming"""
    
    def __init__(self, model, tokenizer, train_dataset, training_args):
        self.model = model
        self.tokenizer = tokenizer
        self.train_dataset = train_dataset
        self.training_args = training_args
        self.trainer = None
    
    def setup_trainer(self):
        """Initialize the trainer with callbacks"""
        from trl import SFTTrainer
        
        # Add custom callback
        checkpoint_callback = CheckpointCallback()
        
        self.trainer = SFTTrainer(
            model=self.model,
            train_dataset=self.train_dataset,
            dataset_text_field="text",
            max_seq_length=512,
            tokenizer=self.tokenizer,
            args=self.training_args,
            packing=False,
            callbacks=[checkpoint_callback]
        )
    
    def find_last_checkpoint(self) -> str:
        """Find the most recent checkpoint"""
        output_dir = self.training_args.output_dir
        
        if not os.path.exists(output_dir):
            return None
        
        checkpoints = [d for d in os.listdir(output_dir) if d.startswith("checkpoint-")]
        if not checkpoints:
            return None
        
        # Sort by step number
        checkpoints.sort(key=lambda x: int(x.split("-")[1]))
        return os.path.join(output_dir, checkpoints[-1])
    
    def train_with_resume(self):
        """Train with automatic resuming"""
        if not self.trainer:
            self.setup_trainer()
        
        # Check for existing checkpoint
        last_checkpoint = self.find_last_checkpoint()
        
        if last_checkpoint:
            print(f"Resuming from checkpoint: {last_checkpoint}")
            
            # Load checkpoint info
            info_path = os.path.join(self.training_args.output_dir, "checkpoint_info.json")
            if os.path.exists(info_path):
                with open(info_path, "r") as f:
                    checkpoint_info = json.load(f)
                print(f"Resuming from step {checkpoint_info['step']}, epoch {checkpoint_info['epoch']}")
        
        # Start/resume training
        try:
            self.trainer.train(resume_from_checkpoint=last_checkpoint)
        except KeyboardInterrupt:
            print("Training interrupted. Saving current state...")
            self.trainer.save_model()
            raise
        except Exception as e:
            print(f"Training error: {e}")
            self.trainer.save_model()
            raise
    
    def save_final_model(self, push_to_hub: bool = False, hub_model_id: str = None):
        """Save the final trained model"""
        # Save locally
        self.trainer.save_model()
        self.tokenizer.save_pretrained(self.training_args.output_dir)
        
        # Optionally push to hub
        if push_to_hub and hub_model_id:
            self.trainer.push_to_hub(hub_model_id)
            self.tokenizer.push_to_hub(hub_model_id)
        
        print(f"Model saved to {self.training_args.output_dir}")

# Usage example
def train_german_legal_model():
    """Complete training pipeline"""
    
    # Setup (previous code for model, tokenizer, dataset)
    # ... model, tokenizer, train_dataset, training_args setup ...
    
    # Initialize advanced trainer
    advanced_trainer = AdvancedTrainer(
        model=model,
        tokenizer=tokenizer,
        train_dataset=train_dataset,
        training_args=training_args
    )
    
    # Train with auto-resume
    advanced_trainer.train_with_resume()
    
    # Save final model
    advanced_trainer.save_final_model(
        push_to_hub=True,
        hub_model_id="your-username/german-legal-model"
    )

# Run training
# train_german_legal_model()
```

---

## Model Evaluation and Validation Metrics

### German Legal Model Evaluation

```python
# =============================================================================
# Model Evaluation and Validation Metrics
# =============================================================================

import torch
from transformers import pipeline
from datasets import load_metric
import pandas as pd
from typing import List, Dict
import re

class GermanLegalEvaluator:
    """Evaluate German legal models"""
    
    def __init__(self, model_path: str, tokenizer_path: str):
        self.model_path = model_path
        self.tokenizer_path = tokenizer_path
        self.pipeline = self.load_pipeline()
        
        # German legal evaluation criteria
        self.legal_terms = [
            "BGB", "StGB", "GG", "ZPO", "StPO", "HGB",
            "Rechtsprechung", "Urteil", "Beschluss", "Verordnung"
        ]
    
    def load_pipeline(self):
        """Load the trained model as a pipeline"""
        return pipeline(
            "text-generation",
            model=self.model_path,
            tokenizer=self.tokenizer_path,
            torch_dtype=torch.float16,
            device_map="auto"
        )
    
    def evaluate_legal_knowledge(self, test_cases: List[Dict]) -> Dict:
        """Evaluate model's legal knowledge"""
        results = {
            "legal_term_recognition": 0,
            "paragraph_reference_accuracy": 0,
            "contextual_understanding": 0,
            "response_quality": []
        }
        
        for test_case in test_cases:
            prompt = test_case["prompt"]
            expected_terms = test_case.get("expected_terms", [])
            
            # Generate response
            response = self.pipeline(
                prompt,
                max_length=200,
                num_return_sequences=1,
                temperature=0.7,
                do_sample=True
            )[0]["generated_text"]
            
            # Evaluate response
            score = self.score_response(response, expected_terms)
            results["response_quality"].append(score)
        
        # Calculate averages
        results["legal_term_recognition"] = sum(r["legal_terms"] for r in results["response_quality"]) / len(results["response_quality"])
        results["paragraph_reference_accuracy"] = sum(r["paragraph_refs"] for r in results["response_quality"]) / len(results["response_quality"])
        results["contextual_understanding"] = sum(r["context"] for r in results["response_quality"]) / len(results["response_quality"])
        
        return results
    
    def score_response(self, response: str, expected_terms: List[str]) -> Dict:
        """Score a single response"""
        score = {
            "legal_terms": 0,
            "paragraph_refs": 0,
            "context": 0
        }
        
        # Check for legal terms
        found_terms = sum(1 for term in self.legal_terms if term in response)
        score["legal_terms"] = min(found_terms / max(len(expected_terms), 1), 1.0)
        
        # Check for paragraph references
        paragraph_refs = len(re.findall(r'§\s*\d+', response))
        score["paragraph_refs"] = min(paragraph_refs / 3, 1.0)  # Normalize to 0-1
        
        # Basic context score (length and coherence)
        score["context"] = min(len(response.split()) / 50, 1.0)
        
        return score
    
    def perplexity_evaluation(self, test_texts: List[str]) -> float:
        """Calculate perplexity on test texts"""
        from transformers import AutoModelForCausalLM, AutoTokenizer
        
        model = AutoModelForCausalLM.from_pretrained(self.model_path)
        tokenizer = AutoTokenizer.from_pretrained(self.tokenizer_path)
        
        total_loss = 0
        total_tokens = 0
        
        model.eval()
        with torch.no_grad():
            for text in test_texts:
                inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=512)
                outputs = model(**inputs, labels=inputs["input_ids"])
                
                loss = outputs.loss
                num_tokens = inputs["input_ids"].size(1)
                
                total_loss += loss.item() * num_tokens
                total_tokens += num_tokens
        
        avg_loss = total_loss / total_tokens
        perplexity = torch.exp(torch.tensor(avg_loss))
        
        return perplexity.item()
    
    def generate_evaluation_report(self, test_cases: List[Dict], test_texts: List[str]) -> str:
        """Generate comprehensive evaluation report"""
        
        # Evaluate legal knowledge
        legal_eval = self.evaluate_legal_knowledge(test_cases)
        
        # Calculate perplexity
        perplexity = self.perplexity_evaluation(test_texts)
        
        report = f"""
# German Legal Model Evaluation Report

## Model Information
- Model Path: {self.model_path}
- Evaluation Date: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')}

## Performance Metrics

### Legal Knowledge Assessment
- Legal Term Recognition: {legal_eval['legal_term_recognition']:.3f}
- Paragraph Reference Accuracy: {legal_eval['paragraph_reference_accuracy']:.3f}
- Contextual Understanding: {legal_eval['contextual_understanding']:.3f}

### Language Model Metrics
- Perplexity: {perplexity:.2f}

### Overall Score
- Average Performance: {(legal_eval['legal_term_recognition'] + legal_eval['paragraph_reference_accuracy'] + legal_eval['contextual_understanding']) / 3:.3f}

## Recommendations
"""
        
        if legal_eval['legal_term_recognition'] < 0.5:
            report += "- Consider adding more legal terminology to training data\n"
        
        if perplexity > 50:
            report += "- Model may benefit from additional training\n"
        
        if legal_eval['contextual_understanding'] < 0.4:
            report += "- Improve context awareness with longer training sequences\n"
        
        return report

# Example test cases
test_cases = [
    {
        "prompt": "Erkläre § 433 BGB:",
        "expected_terms": ["BGB", "Kaufvertrag", "Verkäufer", "Käufer"]
    },
    {
        "prompt": "Was regelt das Strafgesetzbuch?",
        "expected_terms": ["StGB", "Strafrecht", "Delikte"]
    }
]

test_texts = [
    "Das Bürgerliche Gesetzbuch regelt die Rechtsbeziehungen zwischen Privatpersonen.",
    "Nach § 433 BGB ist der Verkäufer zur Übergabe verpflichtet."
]

# Usage
evaluator = GermanLegalEvaluator("./german-legal-model", "./german-legal-model")
report = evaluator.generate_evaluation_report(test_cases, test_texts)
print(report)
```

---

## Export and Quantization Procedures

### Model Export and Optimization

```python
# =============================================================================
# Export and Quantization Procedures
# =============================================================================

import torch
import os
from transformers import AutoModelForCausalLM, AutoTokenizer
from pathlib import Path

class ModelExporter:
    """Export and optimize trained models"""
    
    def __init__(self, model_path: str, output_dir: str):
        self.model_path = model_path
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
    
    def export_onnx(self):
        """Export model to ONNX format"""
        try:
            from transformers.onnx import export
            
            model = AutoModelForCausalLM.from_pretrained(self.model_path)
            tokenizer = AutoTokenizer.from_pretrained(self.model_path)
            
            # Export to ONNX
            onnx_path = self.output_dir / "model.onnx"
            
            # Create dummy input
            dummy_input = tokenizer("Beispieltext", return_tensors="pt")
            
            torch.onnx.export(
                model,
                dummy_input["input_ids"],
                onnx_path,
                export_params=True,
                opset_version=11,
                do_constant_folding=True,
                input_names=['input_ids'],
                output_names=['output'],
                dynamic_axes={
                    'input_ids': {0: 'batch_size', 1: 'sequence'},
                    'output': {0: 'batch_size', 1: 'sequence'}
                }
            )
            
            print(f"ONNX model exported to {onnx_path}")
            return onnx_path
            
        except ImportError:
            print("ONNX export requires: pip install transformers[onnx]")
    
    def quantize_int8(self):
        """Quantize model to INT8"""
        from transformers import AutoModelForCausalLM
        
        # Load model
        model = AutoModelForCausalLM.from_pretrained(
            self.model_path,
            torch_dtype=torch.float16
        )
        
        # Dynamic quantization
        quantized_model = torch.quantization.quantize_dynamic(
            model,
            {torch.nn.Linear},
            dtype=torch.qint8
        )
        
        # Save quantized model
        quantized_path = self.output_dir / "quantized_int8"
        quantized_model.save_pretrained(quantized_path)
        
        print(f"INT8 quantized model saved to {quantized_path}")
        return quantized_path
    
    def export_for_deployment(self, formats: List[str] = ["pytorch", "onnx", "quantized"]):
        """Export model in multiple formats for deployment"""
        
        results = {}
        
        if "pytorch" in formats:
            # Standard PyTorch export
            model = AutoModelForCausalLM.from_pretrained(self.model_path)
            tokenizer = AutoTokenizer.from_pretrained(self.model_path)
            
            pytorch_path = self.output_dir / "pytorch"
            model.save_pretrained(pytorch_path)
            tokenizer.save_pretrained(pytorch_path)
            results["pytorch"] = pytorch_path
        
        if "onnx" in formats:
            results["onnx"] = self.export_onnx()
        
        if "quantized" in formats:
            results["quantized"] = self.quantize_int8()
        
        # Create deployment info
        deployment_info = {
            "model_name": "german-legal-model",
            "formats": results,
            "deployment_date": pd.Timestamp.now().isoformat(),
            "model_size_mb": self.get_model_size_mb(),
            "recommended_hardware": self.get_hardware_recommendations()
        }
        
        with open(self.output_dir / "deployment_info.json", "w") as f:
            json.dump(deployment_info, f, indent=2, default=str)
        
        return results
    
    def get_model_size_mb(self) -> float:
        """Calculate model size in MB"""
        total_size = 0
        for file_path in Path(self.model_path).rglob("*"):
            if file_path.is_file():
                total_size += file_path.stat().st_size
        return total_size / (1024 * 1024)
    
    def get_hardware_recommendations(self) -> Dict:
        """Get hardware recommendations based on model size"""
        size_mb = self.get_model_size_mb()
        
        if size_mb < 500:
            return {
                "min_ram": "4GB",
                "recommended_ram": "8GB",
                "gpu_required": False,
                "cpu_cores": "2+"
            }
        elif size_mb < 2000:
            return {
                "min_ram": "8GB",
                "recommended_ram": "16GB",
                "gpu_required": True,
                "gpu_memory": "6GB+",
                "cpu_cores": "4+"
            }
        else:
            return {
                "min_ram": "16GB",
                "recommended_ram": "32GB",
                "gpu_required": True,
                "gpu_memory": "12GB+",
                "cpu_cores": "8+"
            }

# Usage example
exporter = ModelExporter("./german-legal-model", "./deployment")
deployment_formats = exporter.export_for_deployment()
print("Deployment ready:", deployment_formats)
```

### Hugging Face Hub Integration

```python
def upload_to_hub(model_path: str, hub_model_id: str, private: bool = False):
    """Upload trained model to Hugging Face Hub"""
    
    from huggingface_hub import HfApi, Repository
    from transformers import AutoModelForCausalLM, AutoTokenizer
    
    # Load model and tokenizer
    model = AutoModelForCausalLM.from_pretrained(model_path)
    tokenizer = AutoTokenizer.from_pretrained(model_path)
    
    # Push to hub
    model.push_to_hub(hub_model_id, private=private)
    tokenizer.push_to_hub(hub_model_id, private=private)
    
    # Create model card
    model_card = f"""
---
language: de
tags:
- legal
- german
- law
- text-generation
license: mit
---

# German Legal Model

This model has been fine-tuned on German legal documents for legal text understanding and generation.

## Model Details
- Base Model: [base model name]
- Language: German
- Domain: Legal
- Training Method: LoRA/QLoRA fine-tuning

## Usage

```python
from transformers import AutoModelForCausalLM, AutoTokenizer

model = AutoModelForCausalLM.from_pretrained("{hub_model_id}")
tokenizer = AutoTokenizer.from_pretrained("{hub_model_id}")

# Generate legal text
input_text = "Das Bürgerliche Gesetzbuch regelt"
inputs = tokenizer(input_text, return_tensors="pt")
outputs = model.generate(**inputs, max_length=100)
print(tokenizer.decode(outputs[0]))
```

## Training Data
The model was trained on German legal documents including:
- Court decisions
- Legal codes (BGB, StGB, etc.)
- Legal commentary

## Limitations
- Specialized for German legal domain
- May not be suitable for other legal systems
- Should not be used for actual legal advice

## Citation
If you use this model, please cite:
[Your citation information]
"""
    
    # Save model card
    with open("README.md", "w", encoding="utf-8") as f:
        f.write(model_card)
    
    # Upload model card
    api = HfApi()
    api.upload_file(
        path_or_fileobj="README.md",
        path_in_repo="README.md",
        repo_id=hub_model_id,
        repo_type="model"
    )
    
    print(f"Model uploaded to: https://huggingface.co/{hub_model_id}")

# Example usage
# upload_to_hub("./german-legal-model", "your-username/german-legal-model")
```

---

## Configuration Files

### Training Configuration Template

```yaml
# training_config.yaml
model:
  name: "microsoft/DialoGPT-medium"
  quantization:
    enabled: true
    type: "4bit"
    compute_dtype: "bfloat16"

lora:
  r: 16
  alpha: 32
  dropout: 0.1
  target_modules: ["c_attn", "c_proj"]

training:
  output_dir: "./german-legal-model"
  num_epochs: 3
  batch_size: 1
  gradient_accumulation_steps: 8
  learning_rate: 2e-4
  weight_decay: 0.001
  warmup_ratio: 0.03
  lr_scheduler: "cosine"
  fp16: true
  max_grad_norm: 0.3
  save_steps: 500
  logging_steps: 25

dataset:
  max_length: 512
  text_field: "text"
  validation_split: 0.1

evaluation:
  strategy: "steps"
  eval_steps: 500
  metric_for_best_model: "eval_loss"
  load_best_model_at_end: true

logging:
  report_to: "wandb"
  project: "german-legal-models"
  run_name: "legal-model-v1"

deployment:
  push_to_hub: true
  hub_model_id: "your-username/german-legal-model"
  private: false
```

### Platform-Specific Configurations

```json
{
  "colab_config": {
    "gpu_type": "T4",
    "ram_gb": 12,
    "disk_gb": 100,
    "max_training_hours": 12,
    "recommended_batch_size": 1,
    "gradient_accumulation": 8
  },
  "kaggle_config": {
    "gpu_type": "P100",
    "ram_gb": 20,
    "disk_gb": 73,
    "max_training_hours": 9,
    "recommended_batch_size": 2,
    "gradient_accumulation": 4
  },
  "paperspace_config": {
    "gpu_type": "M4000",
    "ram_gb": 8,
    "disk_gb": 50,
    "max_training_hours": 6,
    "recommended_batch_size": 1,
    "gradient_accumulation": 16
  }
}
```

This comprehensive guide provides everything needed to train German legal models using free resources, from initial setup to deployment. Each section includes practical code examples and can be adapted based on your specific requirements and available resources.