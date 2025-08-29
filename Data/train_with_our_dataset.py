#!/usr/bin/env python3
"""
German Legal AI - Training with OUR Prepared Dataset
Uses the 9,997 sample dataset we prepared earlier
"""

import subprocess
import sys
import os
import time
from datetime import datetime
import warnings
warnings.filterwarnings("ignore")

print("German Legal AI - Training with OUR 9,997 Sample Dataset")
print("=" * 60)

def install_minimal_packages():
    """Install only essential packages."""
    print("Installing essential packages...")
    
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "pip"], check=False)
        
        essential_packages = [
            "torch",
            "transformers==4.36.0",
            "datasets==2.14.0", 
            "accelerate==0.24.0",
            "peft==0.7.0",
            "numpy",
            "pandas",
            "tqdm"
        ]
        
        for package in essential_packages:
            print(f"Installing {package}...")
            subprocess.run([sys.executable, "-m", "pip", "install", package], check=False)
        
        print("Essential packages installed")
        return True
        
    except Exception as e:
        print(f"Installation warning: {e}")
        return True

def load_our_prepared_dataset():
    """Load the dataset we prepared with 9,997 samples."""
    import pandas as pd
    from datasets import Dataset
    
    print("Loading OUR prepared German legal dataset...")
    
    # Check which dataset format is available
    dataset_paths = [
        "exported_datasets/parquet/train.parquet",
        "exported_datasets/csv/train.csv", 
        "massive_legal_data/train.jsonl",
        "final_expanded_data/train.jsonl"
    ]
    
    train_data = None
    eval_data = None
    test_data = None
    
    # Try to load from parquet first (most efficient)
    for path in dataset_paths:
        if os.path.exists(path):
            print(f"Found dataset: {path}")
            
            try:
                if path.endswith('.parquet'):
                    train_df = pd.read_parquet(path)
                    
                    # Load validation and test if available
                    val_path = path.replace('train.parquet', 'validation.parquet')
                    test_path = path.replace('train.parquet', 'test.parquet')
                    
                    if os.path.exists(val_path):
                        eval_df = pd.read_parquet(val_path)
                        print(f"Found validation: {val_path}")
                    else:
                        # Split training data
                        split_idx = int(len(train_df) * 0.85)
                        eval_df = train_df[split_idx:].reset_index(drop=True)
                        train_df = train_df[:split_idx].reset_index(drop=True)
                        print("Created validation split from training data")
                    
                    if os.path.exists(test_path):
                        test_df = pd.read_parquet(test_path)
                        print(f"Found test: {test_path}")
                    
                elif path.endswith('.csv'):
                    train_df = pd.read_csv(path)
                    
                    val_path = path.replace('train.csv', 'validation.csv')
                    if os.path.exists(val_path):
                        eval_df = pd.read_csv(val_path)
                    else:
                        split_idx = int(len(train_df) * 0.85)
                        eval_df = train_df[split_idx:].reset_index(drop=True)
                        train_df = train_df[:split_idx].reset_index(drop=True)
                
                elif path.endswith('.jsonl'):
                    import json
                    
                    # Load JSONL
                    train_data_list = []
                    with open(path, 'r', encoding='utf-8') as f:
                        for line in f:
                            train_data_list.append(json.loads(line))
                    
                    train_df = pd.DataFrame(train_data_list)
                    
                    # Try to load validation
                    val_path = path.replace('train.jsonl', 'validation.jsonl')
                    if os.path.exists(val_path):
                        eval_data_list = []
                        with open(val_path, 'r', encoding='utf-8') as f:
                            for line in f:
                                eval_data_list.append(json.loads(line))
                        eval_df = pd.DataFrame(eval_data_list)
                    else:
                        split_idx = int(len(train_df) * 0.85)
                        eval_df = train_df[split_idx:].reset_index(drop=True)
                        train_df = train_df[:split_idx].reset_index(drop=True)
                
                break
                
            except Exception as e:
                print(f"Failed to load {path}: {e}")
                continue
    
    if train_df is None:
        raise FileNotFoundError("Could not find any prepared dataset files!")
    
    print(f"Dataset loaded successfully!")
    print(f"Training samples: {len(train_df)}")
    print(f"Validation samples: {len(eval_df)}")
    
    # Show dataset info
    print(f"\nDataset columns: {list(train_df.columns)}")
    
    # Check if we have the right format
    if 'text' not in train_df.columns:
        # Format the dataset for training
        def format_row(row):
            if 'instruction' in row and 'output' in row:
                if pd.notna(row.get('input', '')) and str(row.get('input', '')).strip():
                    text = f"### Anweisung:\n{row['instruction']}\n\n### Eingabe:\n{row['input']}\n\n### Antwort:\n{row['output']}<|endoftext|>"
                else:
                    text = f"### Anweisung:\n{row['instruction']}\n\n### Antwort:\n{row['output']}<|endoftext|>"
                return text
            return None
        
        print("Formatting dataset for instruction training...")
        train_df['text'] = train_df.apply(format_row, axis=1)
        eval_df['text'] = eval_df.apply(format_row, axis=1)
        
        # Remove rows with no text
        train_df = train_df.dropna(subset=['text']).reset_index(drop=True)
        eval_df = eval_df.dropna(subset=['text']).reset_index(drop=True)
    
    # Convert to HuggingFace datasets
    train_dataset = Dataset.from_pandas(train_df[['text']])
    eval_dataset = Dataset.from_pandas(eval_df[['text']])
    
    # Show sample
    print(f"\nSample training text:")
    print(f"{train_dataset[0]['text'][:300]}...")
    
    print(f"\nFinal dataset ready:")
    print(f"Training: {len(train_dataset)} samples")
    print(f"Validation: {len(eval_dataset)} samples")
    
    return train_dataset, eval_dataset

def train_with_our_data(model, tokenizer, train_dataset, eval_dataset, model_name):
    """Train with our comprehensive dataset."""
    from transformers import TrainingArguments, Trainer, DataCollatorForLanguageModeling
    import torch
    
    print("Setting up training with OUR comprehensive dataset...")
    
    def tokenize_function(examples):
        return tokenizer(
            examples["text"],
            truncation=True,
            padding=False,
            max_length=512,
            return_overflowing_tokens=False,
        )
    
    # Tokenize datasets
    print("Tokenizing OUR dataset...")
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
    
    print(f"Tokenization complete: {len(tokenized_train)} train, {len(tokenized_eval)} eval")
    
    # Calculate optimal training parameters based on dataset size
    dataset_size = len(tokenized_train)
    if dataset_size > 5000:
        # Large dataset - use fewer epochs but more steps per epoch
        num_epochs = 3
        eval_steps = 500
        save_steps = 1000
        logging_steps = 100
    elif dataset_size > 1000:
        # Medium dataset
        num_epochs = 4
        eval_steps = 200
        save_steps = 400
        logging_steps = 50
    else:
        # Small dataset - more epochs
        num_epochs = 6
        eval_steps = 50
        save_steps = 100
        logging_steps = 20
    
    print(f"Optimized for dataset size {dataset_size}: {num_epochs} epochs")
    
    # Training configuration optimized for our dataset
    output_dir = "./german-legal-model-our-data"
    training_args = TrainingArguments(
        output_dir=output_dir,
        overwrite_output_dir=True,
        
        # Optimized for our dataset size
        num_train_epochs=num_epochs,
        per_device_train_batch_size=4,
        gradient_accumulation_steps=4,
        learning_rate=2e-5,
        lr_scheduler_type="cosine",
        warmup_ratio=0.1,
        weight_decay=0.01,
        
        # Memory settings
        fp16=False,
        gradient_checkpointing=True,
        dataloader_pin_memory=False,
        
        # Logging and evaluation
        logging_steps=logging_steps,
        eval_steps=eval_steps,
        eval_strategy="steps",
        save_steps=save_steps,
        save_total_limit=3,
        load_best_model_at_end=True,
        metric_for_best_model="eval_loss",
        greater_is_better=False,
        
        # Other settings
        remove_unused_columns=False,
        report_to=None,
        max_grad_norm=1.0,
        dataloader_num_workers=0,
        prediction_loss_only=True,
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
    
    # Calculate training time estimate
    total_steps = (len(tokenized_train) * num_epochs) // (training_args.per_device_train_batch_size * training_args.gradient_accumulation_steps)
    estimated_time = total_steps * 0.8  # More realistic estimate
    
    print(f"Starting training with OUR {dataset_size} sample dataset...")
    print(f"Total training steps: {total_steps}")
    print(f"Estimated time: {estimated_time/60:.1f} minutes")
    print(f"This will PROPERLY train on our comprehensive German legal data!")
    
    start_time = time.time()
    
    try:
        training_result = trainer.train()
        
        training_time = time.time() - start_time
        print(f"\nTraining completed with OUR dataset!")
        print(f"Actual training time: {training_time/60:.1f} minutes")
        print(f"Final training loss: {training_result.training_loss:.4f}")
        print(f"Total training steps: {training_result.global_step}")
        print(f"Model trained on {dataset_size} German legal examples!")
        
        # Save model
        trainer.save_model()
        tokenizer.save_pretrained(output_dir)
        
        print(f"Model saved to: {output_dir}")
        return trainer, output_dir
        
    except Exception as e:
        print(f"Training failed: {e}")
        raise e

def test_our_trained_model(model, tokenizer):
    """Test the model trained on our dataset."""
    import torch
    
    print("Testing model trained on OUR comprehensive dataset...")
    
    def generate_legal_response(instruction, input_text=""):
        prompt = f"### Anweisung:\n{instruction}\n\n"
        if input_text:
            prompt += f"### Eingabe:\n{input_text}\n\n"
        prompt += "### Antwort:\n"
        
        inputs = tokenizer(prompt, return_tensors="pt")
        
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=250,
                temperature=0.7,
                do_sample=True,
                top_p=0.9,
                repetition_penalty=1.1,
                pad_token_id=tokenizer.eos_token_id,
                eos_token_id=tokenizer.eos_token_id,
            )
        
        response = tokenizer.decode(outputs[0], skip_special_tokens=True)
        response_start = response.find("### Antwort:\n") + len("### Antwort:\n")
        return response[response_start:].strip()
    
    # Test cases covering our dataset domains
    test_cases = [
        {
            "instruction": "Erklaere die rechtlichen Probleme bei einer ueberhoehten Mietkaution.",
            "input": "Ein Vermieter verlangt 4 Monatsmieten als Kaution fuer eine Wohnung.",
            "expected_domain": "Buergerliches Recht"
        },
        {
            "instruction": "Was sind die Folgen von Diebstahl nach deutschem Strafrecht?",
            "input": "Ein Mitarbeiter stiehlt 500 Euro aus der Kasse.",
            "expected_domain": "Strafrecht"
        },
        {
            "instruction": "Erklaere die Kuendigungsschutzbestimmungen im deutschen Arbeitsrecht.",
            "input": "Ein Arbeitgeber moechte einen langjaehrigen Mitarbeiter kuendigen.",
            "expected_domain": "Arbeitsrecht"
        },
        {
            "instruction": "Was regelt das Grundgesetz zur Meinungsfreiheit?",
            "input": "Darf man oeffentlich seine politische Meinung aeussern?",
            "expected_domain": "Verfassungsrecht"
        },
        {
            "instruction": "Erklaere das Verwaltungsverfahren bei Baugenehmigungen.",
            "input": "Welche Schritte sind fuer eine Baugenehmigung erforderlich?",
            "expected_domain": "Verwaltungsrecht"
        }
    ]
    
    print("\n" + "="*80)
    print("TESTING MODEL TRAINED ON OUR 9,997 SAMPLE DATASET")
    print("="*80)
    
    successful_responses = 0
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\nTest {i} ({test_case['expected_domain']}):")
        print(f"Anweisung: {test_case['instruction']}")
        if test_case['input']:
            print(f"Eingabe: {test_case['input']}")
        
        try:
            response = generate_legal_response(test_case['instruction'], test_case['input'])
            print(f"\n Antwort: {response}")
            
            # Quality assessment
            quality_indicators = ['§', 'BGB', 'StGB', 'GG', 'Artikel', 'Absatz', 'Recht', 'Gesetz']
            legal_refs = sum(1 for indicator in quality_indicators if indicator in response)
            
            if len(response) > 100 and legal_refs >= 2:
                print(" Response quality: EXCELLENT (detailed with legal references)")
                successful_responses += 1
            elif len(response) > 50 and legal_refs >= 1:
                print(" Response quality: GOOD (adequate with some legal content)")
                successful_responses += 1
            elif len(response) > 20:
                print("️ Response quality: FAIR (basic response)")
            else:
                print(" Response quality: POOR (too short or irrelevant)")
                
        except Exception as e:
            print(f"\n Error: {str(e)[:100]}...")
        
        print("-" * 80)
    
    success_rate = (successful_responses / len(test_cases)) * 100
    print(f"\n OVERALL TEST RESULTS:")
    print(f" Successful responses: {successful_responses}/{len(test_cases)} ({success_rate:.1f}%)")
    
    if success_rate >= 80:
        print(" EXCELLENT! Model shows strong German legal knowledge")
    elif success_rate >= 60:
        print(" GOOD! Model demonstrates decent legal understanding")
    elif success_rate >= 40:
        print("️ FAIR! Model has basic legal knowledge but needs improvement")
    else:
        print(" POOR! Model requires more training or better data")
    
    print(f"\n Testing completed on model trained with OUR {len(test_cases)} domain dataset!")

def main():
    """Main function using our prepared dataset."""
    print(f"Starting training with OUR prepared dataset at {datetime.now()}")
    start_time = time.time()
    
    try:
        # Step 1: Install packages
        print("\n" + "="*60)
        install_minimal_packages()
        
        # Step 2: Import modules
        print("\n" + "="*60)
        print(" Loading required modules...")
        import torch
        from transformers import AutoTokenizer, AutoModelForCausalLM
        from peft import LoraConfig, get_peft_model, TaskType
        
        print(f" PyTorch: {torch.__version__}")
        print(" Using CPU for stable training")
        
        # Step 3: Load OUR prepared dataset
        print("\n" + "="*60)
        train_data, eval_data = load_our_prepared_dataset()
        
        # Step 4: Load model
        print("\n" + "="*60)
        print(" Loading GPT-2 model...")
        model_name = "gpt2"
        
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token
        tokenizer.padding_side = "right"
        
        model = AutoModelForCausalLM.from_pretrained(
            model_name,
            torch_dtype=torch.float32,
        )
        
        print(f" Model loaded: {model_name}")
        print(f" Parameters: {model.num_parameters():,}")
        
        # Step 5: Setup LoRA
        print("\n" + "="*60)
        print("️ Setting up LoRA...")
        
        lora_config = LoraConfig(
            task_type=TaskType.CAUSAL_LM,
            r=16,
            lora_alpha=32,
            lora_dropout=0.1,
            target_modules=["c_attn", "c_proj", "c_fc"],
            bias="none",
        )
        
        model = get_peft_model(model, lora_config)
        
        trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
        total = sum(p.numel() for p in model.parameters())
        print(f" LoRA applied: {trainable:,} trainable ({100*trainable/total:.2f}%)")
        
        # Step 6: Train with our data
        print("\n" + "="*60)
        trainer, output_dir = train_with_our_data(model, tokenizer, train_data, eval_data, model_name)
        
        # Step 7: Test with our domains
        print("\n" + "="*60)
        test_our_trained_model(model, tokenizer)
        
        # Step 8: Create deployment package
        print("\n" + "="*60)
        print(" Creating deployment package...")
        
        import zipfile
        import json
        
        timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
        zip_name = f"german-legal-ai-OUR-DATASET-{timestamp}.zip"
        
        # Create comprehensive config
        config = {
            "model_name": "German Legal AI - Trained on OUR Dataset",
            "base_model": model_name,
            "version": "3.0",
            "training_date": datetime.now().isoformat(),
            "dataset_info": {
                "source": "Our prepared comprehensive German legal dataset",
                "training_examples": len(train_data),
                "validation_examples": len(eval_data),
                "total_examples": len(train_data) + len(eval_data),
                "domains": ["Bürgerliches Recht", "Strafrecht", "Arbeitsrecht", "Verfassungsrecht", "Verwaltungsrecht"]
            },
            "training_config": {
                "epochs": "3-6 (optimized based on dataset size)",
                "batch_size": 4,
                "learning_rate": "2e-5",
                "lora_rank": 16
            },
            "notes": "Trained on our comprehensive 9,997 sample German legal dataset covering all major legal domains"
        }
        
        with open(f"{output_dir}/config.json", "w", encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        
        # Create ZIP
        with zipfile.ZipFile(zip_name, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(output_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, output_dir)
                    zipf.write(file_path, arcname)
        
        # Final summary
        total_time = time.time() - start_time
        print(f"\n" + "="*60)
        print(" SUCCESS! German Legal AI trained on OUR DATASET!")
        print("="*60)
        print(f" Total time: {total_time/60:.1f} minutes")
        print(f" Package: {zip_name}")
        print(f" Model: {output_dir}")
        print(f" OUR dataset size: {len(train_data)} training samples")
        print(f" Trained on OUR comprehensive German legal knowledge!")
        print(f" This model uses YOUR prepared 9,997 sample dataset!")
        print("\n Ready for deployment on your AX102 server!")
        
    except Exception as e:
        print(f"\n Training failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()