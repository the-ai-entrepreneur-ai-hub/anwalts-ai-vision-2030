#!/usr/bin/env python3
"""
 German Legal AI - Python 3.12 Compatible Trainer
Fixed for Windows Python 3.12 environment
"""

import subprocess
import sys
import os
import time
from datetime import datetime
import warnings
warnings.filterwarnings("ignore")

print("German Legal AI - Python 3.12 Compatible Trainer")
print("=" * 60)

def upgrade_pip_and_tools():
    """Upgrade pip and build tools first."""
    print(" Upgrading pip and build tools...")
    
    try:
        # Upgrade pip
        subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "pip"], check=True)
        print(" Pip upgraded")
        
        # Install/upgrade build tools
        subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "setuptools", "wheel"], check=True)
        print(" Build tools upgraded")
        
        # Fix setuptools compatibility
        subprocess.run([sys.executable, "-m", "pip", "install", "setuptools<70.0.0"], check=True)
        print(" Setuptools compatibility fixed")
        
        return True
        
    except Exception as e:
        print(f" Upgrade warning: {e}")
        return True  # Continue anyway

def install_packages_python312():
    """Install packages compatible with Python 3.12."""
    print(" Installing Python 3.12 compatible packages...")
    
    # First upgrade pip and tools
    upgrade_pip_and_tools()
    
    # Install packages in specific order for Python 3.12
    packages_order = [
        # Core dependencies first
        ["numpy>=1.24.0"],
        
        # PyTorch (CPU version for compatibility)
        ["torch", "torchvision", "torchaudio", "--index-url", "https://download.pytorch.org/whl/cpu"],
        
        # ML libraries
        ["transformers>=4.36.0"],
        ["datasets>=2.14.0"],
        ["accelerate>=0.24.0"],
        ["peft>=0.7.0"],
        ["huggingface_hub>=0.19.0"],
        
        # Utility libraries
        ["pandas>=1.5.0"],
        ["scikit-learn"],
        ["tqdm"],
        ["requests"]
    ]
    
    for package_group in packages_order:
        package_name = package_group[0].split('>=')[0].split('==')[0]
        print(f" Installing {package_name}...")
        
        try:
            cmd = [sys.executable, "-m", "pip", "install"] + package_group
            result = subprocess.run(cmd, capture_output=True, text=True, check=False)
            
            if result.returncode == 0:
                print(f" {package_name} installed successfully")
            else:
                print(f" {package_name} installation had warnings (continuing...)")
                
        except Exception as e:
            print(f" {package_name} installation issue: {str(e)[:50]}...")
            continue
        
        time.sleep(1)
    
    print(" Package installation completed!")

def check_environment():
    """Check if all required packages are available."""
    try:
        import torch
        import numpy as np
        from transformers import AutoTokenizer, AutoModelForCausalLM, TrainingArguments, Trainer, DataCollatorForLanguageModeling
        from datasets import Dataset
        import pandas as pd
        
        print(f" NumPy: {np.__version__}")
        print(f" PyTorch: {torch.__version__}")
        print(f" Python: {sys.version.split()[0]}")
        
        # Check for GPU but don't require it
        cuda_available = torch.cuda.is_available()
        print(f" CUDA Available: {cuda_available}")
        
        if cuda_available:
            print(f" GPU: {torch.cuda.get_device_name(0)}")
        else:
            print(" Running on CPU (perfectly fine for this training)")
        
        return True
        
    except ImportError as e:
        print(f" Missing package: {e}")
        return False
    except Exception as e:
        print(f" Environment check failed: {e}")
        return False

def load_massive_german_dataset():
    """Load the massive German legal dataset (7,997 samples)."""
    import pandas as pd
    import json
    from datasets import Dataset
    
    print(" Loading massive German legal dataset...")
    
    def load_jsonl(file_path):
        """Load JSONL file."""
        data = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        data.append(json.loads(line))
            return data
        except Exception as e:
            print(f" Error loading {file_path}: {e}")
            return []
    
    def format_for_training(example):
        """Format examples for instruction training."""
        # Check if already formatted (massive dataset format)
        if 'text' in example and example['text'].strip():
            # Already formatted - just add end token if missing
            text = example['text']
            if not text.endswith('<|endoftext|>') and not text.endswith('</s>'):
                text += '<|endoftext|>'
            return {"text": text}
        
        # Format from instruction/input/output fields (fallback format)
        if example.get('input', '').strip():
            text = f"### Anweisung:\n{example['instruction']}\n\n### Eingabe:\n{example['input']}\n\n### Antwort:\n{example['output']}<|endoftext|>"
        else:
            text = f"### Anweisung:\n{example['instruction']}\n\n### Antwort:\n{example['output']}<|endoftext|>"
        return {"text": text}
    
    # Load the massive dataset
    base_path = "./massive_legal_data"
    train_data = load_jsonl(f"{base_path}/train.jsonl")
    test_data = load_jsonl(f"{base_path}/validation.jsonl")  # Use validation as test
    
    if not train_data:
        print(" Failed to load massive dataset, falling back to small dataset...")
        # Fallback to small dataset
        train_data = [
            {
                "instruction": "Erklre die Rechtslage bei berhhter Mietkaution.",
                "input": "Vermieter fordert 4 Monatsmieten als Kaution.",
                "output": "Nach  551 BGB ist die Mietkaution auf maximal 3 Monatsmieten begrenzt. Eine hhere Kaution ist unzulssig und der Mieter kann die Rckzahlung des berschusses verlangen."
            },
            {
                "instruction": "Was sind die Rechte bei einem mangelhaften Gebrauchtwagen?",
                "input": "Versteckter Unfallschaden nach 3 Wochen entdeckt.",
                "output": "Bei versteckten Mngeln hat der Kufer Gewhrleistungsrechte nach  437 BGB: Nacherfllung, Minderung oder Rcktritt. Bei arglistiger Tuschung zustzlich Anfechtung nach  123 BGB."
            }
        ]
        test_data = train_data[:1]  # Use first example for test
    
    # Create datasets
    train_dataset = Dataset.from_list(train_data).map(format_for_training)
    test_dataset = Dataset.from_list(test_data).map(format_for_training)
    
    print(f" Dataset loaded: {len(train_dataset)} train, {len(test_dataset)} test examples")
    return train_dataset, test_dataset

def load_simple_model():
    """Load a simple, reliable model."""
    from transformers import AutoTokenizer, AutoModelForCausalLM
    import torch
    
    print(" Loading model...")
    
    # Use German GPT-2 - Fast, CPU-friendly, German-optimized
    model_name = "dbmdz/german-gpt2"
    
    try:
        # Load tokenizer
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token
        tokenizer.padding_side = "right"
        
        # Load model - BLOOM-based German model, no Flash Attention needed
        model = AutoModelForCausalLM.from_pretrained(
            model_name,
            torch_dtype=torch.float32,  # Use float32 for CPU compatibility
            trust_remote_code=True  # Required for some models
        )
        
        print(f" Model loaded: {model_name}")
        print(f" Parameters: {model.num_parameters():,}")
        
        return model, tokenizer, model_name
        
    except Exception as e:
        print(f" Model loading failed: {e}")
        raise e

def setup_simple_lora(model):
    """Setup simple LoRA training."""
    try:
        from peft import LoraConfig, get_peft_model, TaskType
        
        print(" Setting up LoRA...")
        
        # Simple LoRA config for GPT-2
        lora_config = LoraConfig(
            task_type=TaskType.CAUSAL_LM,
            r=8,                    # Small rank for stability
            lora_alpha=16,          # Conservative alpha
            lora_dropout=0.1,
            target_modules=["c_attn", "c_proj", "attn", "self_attention"],  # GPT-2 and BLOOM modules
            bias="none",
        )
        
        # Apply LoRA
        model = get_peft_model(model, lora_config)
        
        # Count trainable parameters
        trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
        total = sum(p.numel() for p in model.parameters())
        
        print(f" LoRA applied: {trainable:,} trainable ({100*trainable/total:.2f}%)")
        return model
        
    except ImportError:
        print(" PEFT not available, training full model (will be slower)")
        return model
    except Exception as e:
        print(f" LoRA setup failed: {e}, continuing without LoRA")
        return model

def train_simple_model(model, tokenizer, train_dataset, eval_dataset, model_name):
    """Train the model with simple, stable configuration."""
    from transformers import TrainingArguments, Trainer, DataCollatorForLanguageModeling
    import torch
    
    print(" Setting up training...")
    
    # Tokenize function
    def tokenize_function(examples):
        return tokenizer(
            examples["text"],
            truncation=True,
            padding=False,
            max_length=256,  # Keep it short for stability
            return_overflowing_tokens=False,
        )
    
    # Tokenize datasets
    print(" Tokenizing data...")
    tokenized_train = train_dataset.map(
        tokenize_function,
        batched=True,
        remove_columns=train_dataset.column_names,
    )
    
    tokenized_eval = eval_dataset.map(
        tokenize_function,
        batched=True,
        remove_columns=eval_dataset.column_names,
    )
    
    # Simple training configuration
    output_dir = "./german-legal-model"
    training_args = TrainingArguments(
        output_dir=output_dir,
        overwrite_output_dir=True,
        
        # Conservative training settings
        num_train_epochs=2,
        per_device_train_batch_size=1,
        gradient_accumulation_steps=4,
        learning_rate=5e-5,
        weight_decay=0.01,
        
        # Memory settings
        fp16=False,  # Disable fp16 for CPU compatibility
        dataloader_pin_memory=False,
        
        # Logging
        logging_steps=1,
        eval_steps=2,
        eval_strategy="steps",  # Fixed: was evaluation_strategy
        save_steps=4,
        save_total_limit=2,
        
        # Disable external services
        remove_unused_columns=False,
        report_to=None,
        
        # Stability
        max_grad_norm=1.0,
    )
    
    # Data collator
    data_collator = DataCollatorForLanguageModeling(
        tokenizer=tokenizer,
        mlm=False,
    )
    
    # Create trainer
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=tokenized_train,
        eval_dataset=tokenized_eval,
        data_collator=data_collator,
        tokenizer=tokenizer,
    )
    
    # Train
    print(" Starting training...")
    start_time = time.time()
    
    try:
        training_result = trainer.train()
        
        training_time = time.time() - start_time
        print(f" Training completed in {training_time/60:.1f} minutes")
        
        # Save model
        trainer.save_model()
        tokenizer.save_pretrained(output_dir)
        
        print(f" Model saved to: {output_dir}")
        return trainer, output_dir
        
    except Exception as e:
        print(f" Training failed: {e}")
        raise e

def test_simple_model(model, tokenizer):
    """Test the trained model."""
    import torch
    
    print(" Testing model...")
    
    def generate_response(instruction, input_text=""):
        prompt = f"### Anweisung:\n{instruction}\n\n"
        if input_text:
            prompt += f"### Eingabe:\n{input_text}\n\n"
        prompt += "### Antwort:\n"
        
        inputs = tokenizer(prompt, return_tensors="pt")
        
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=100,
                temperature=0.7,
                do_sample=True,
                top_p=0.9,
                pad_token_id=tokenizer.eos_token_id,
            )
        
        response = tokenizer.decode(outputs[0], skip_special_tokens=True)
        return response[len(prompt):].strip()
    
    # Simple tests
    tests = [
        ("Erklre Mietkaution-Probleme.", "Vermieter will 4 Monatsmieten."),
        ("Was sind Kufer-Rechte bei Mngeln?", ""),
    ]
    
    print("\n" + "="*50)
    for i, (instruction, input_text) in enumerate(tests, 1):
        print(f"\n Test {i}: {instruction}")
        if input_text:
            print(f"Input: {input_text}")
        
        try:
            response = generate_response(instruction, input_text)
            print(f"Response: {response[:150]}...")
        except Exception as e:
            print(f"Error: {str(e)[:50]}...")
    
    print(f"\n Testing completed!")

def create_simple_package(output_dir, model_name):
    """Create deployment package."""
    import zipfile
    import json
    
    print(" Creating deployment package...")
    
    if not os.path.exists(output_dir):
        print(f" Model directory not found: {output_dir}")
        return None
    
    # Create simple config
    config = {
        "model_name": "German Legal AI",
        "base_model": model_name,
        "version": "1.0",
        "date": datetime.now().isoformat(),
        "usage": "### Anweisung:\n{instruction}\n\n### Antwort:\n"
    }
    
    with open(f"{output_dir}/config.json", "w") as f:
        json.dump(config, f, indent=2)
    
    # Create ZIP
    timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
    zip_name = f"german-legal-ai-{timestamp}.zip"
    
    with zipfile.ZipFile(zip_name, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(output_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, output_dir)
                zipf.write(file_path, arcname)
    
    print(f" Package created: {zip_name}")
    return zip_name

def main():
    """Main training function."""
    print(f"Starting at {datetime.now()}")
    start_time = time.time()
    
    try:
        # Step 1: Install packages
        print("\n" + "="*60)
        install_packages_python312()
        
        # Step 2: Check environment
        print("\n" + "="*60)
        if not check_environment():
            print(" Environment check failed")
            return
        
        # Step 3: Create dataset
        print("\n" + "="*60)
        train_data, eval_data = load_massive_german_dataset()
        
        # Step 4: Load model
        print("\n" + "="*60)
        model, tokenizer, model_name = load_simple_model()
        
        # Step 5: Setup LoRA (optional)
        print("\n" + "="*60)
        model = setup_simple_lora(model)
        
        # Step 6: Train
        print("\n" + "="*60)
        trainer, output_dir = train_simple_model(model, tokenizer, train_data, eval_data, model_name)
        
        # Step 7: Test
        print("\n" + "="*60)
        test_simple_model(model, tokenizer)
        
        # Step 8: Package
        print("\n" + "="*60)
        zip_file = create_simple_package(output_dir, model_name)
        
        # Summary
        total_time = time.time() - start_time
        print(f"\n" + "="*60)
        print(" SUCCESS! German Legal AI Training Completed")
        print("="*60)
        print(f" Total time: {total_time/60:.1f} minutes")
        print(f" Package: {zip_file}")
        print(f" Model: {output_dir}")
        print("\n Ready for deployment on your AX102 server!")
        
    except Exception as e:
        print(f"\n Training failed: {e}")
        print(" Try running with administrator privileges")

if __name__ == "__main__":
    main()