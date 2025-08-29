#!/usr/bin/env python3
"""
🇩🇪 German Legal AI - VS Code Local Training
Runs locally in VS Code with Jupyter extension
"""

import subprocess
import sys
import os
import time
from datetime import datetime
import warnings
warnings.filterwarnings("ignore")

print("🇩🇪 German Legal AI - VS Code Local Training")
print("=" * 60)

def install_packages():
    """Install required packages with conflict resolution."""
    print("📦 Installing packages (this may take a few minutes)...")
    
    # Step 1: Uninstall conflicting packages first
    print("🧹 Cleaning up existing packages...")
    cleanup_packages = ["transformers", "datasets", "accelerate", "peft", "bitsandbytes", "torch", "torchvision", "torchaudio"]
    
    for package in cleanup_packages:
        try:
            subprocess.run([sys.executable, "-m", "pip", "uninstall", "-y", package], 
                         capture_output=True, check=False)
        except:
            pass
    
    # Step 2: Install NumPy first (compatible version)
    print("📊 Installing NumPy...")
    subprocess.run([sys.executable, "-m", "pip", "install", "numpy==1.24.3"], check=True)
    
    # Step 3: Install PyTorch (CPU version for local development)
    print("🔥 Installing PyTorch (CPU)...")
    subprocess.run([sys.executable, "-m", "pip", "install", "torch==2.1.0", "torchvision==0.16.0", "torchaudio==2.1.0", "--index-url", "https://download.pytorch.org/whl/cpu"], check=True)
    
    # Step 4: Install ML packages with compatible versions
    ml_packages = [
        "transformers==4.36.0",  # Updated version that includes Mixtral
        "datasets==2.14.6",
        "accelerate==0.24.1",
        "peft==0.7.1",
        "huggingface_hub==0.19.4",
        "pandas==1.5.3",
        "scikit-learn",
        "tqdm"
    ]
    
    for package in ml_packages:
        print(f"📦 Installing {package}...")
        subprocess.run([sys.executable, "-m", "pip", "install", package], check=True)
        time.sleep(1)
    
    print("✅ All packages installed successfully!")

def check_environment():
    """Check if all packages are working."""
    try:
        import torch
        import numpy as np
        from transformers import AutoTokenizer, AutoModelForCausalLM, TrainingArguments, Trainer, DataCollatorForLanguageModeling
        from peft import LoraConfig, get_peft_model, TaskType
        from datasets import Dataset
        import pandas as pd
        
        print(f"✅ NumPy: {np.__version__}")
        print(f"✅ PyTorch: {torch.__version__}")
        print(f"✅ CUDA Available: {torch.cuda.is_available()}")
        
        if torch.cuda.is_available():
            print(f"✅ GPU: {torch.cuda.get_device_name(0)}")
            print(f"✅ GPU Memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f}GB")
        else:
            print("💻 Running on CPU (suitable for development/testing)")
        
        return True
        
    except Exception as e:
        print(f"❌ Environment check failed: {e}")
        return False

def create_german_legal_dataset():
    """Create the German legal training dataset."""
    import pandas as pd
    from datasets import Dataset
    
    print("📚 Creating German legal dataset...")
    
    # Expanded German legal examples
    german_legal_data = [
        {
            "instruction": "Analysiere die rechtlichen Probleme bei einer überhöhten Mietkaution.",
            "input": "Der Vermieter verlangt eine Kaution von 5 Monatsmieten bei einer Wohnung mit 1.200 Euro Monatsmiete.",
            "output": "Die geforderte Kaution von 5 Monatsmieten (6.000 Euro) verstößt gegen § 551 BGB. Nach deutschem Mietrecht ist die Kaution auf maximal 3 Monatsmieten begrenzt. Die rechtlich zulässige Höchstkaution beträgt daher 3.600 Euro. Der Mieter kann die Zahlung der überschüssigen 2.400 Euro verweigern und bei bereits gezahlter Überschreitung die Rückzahlung verlangen. Diese Regelung dient dem Mieterschutz und verhindert übermäßige finanzielle Belastungen."
        },
        {
            "instruction": "Bewerte die Rechtmäßigkeit einer Kündigung in der verlängerten Probezeit.",
            "input": "Ein Arbeitnehmer wird nach 8 Monaten gekündigt. Im Arbeitsvertrag ist eine Probezeit von 12 Monaten vereinbart.",
            "output": "Die vereinbarte Probezeit von 12 Monaten ist nach § 622 Abs. 3 BGB unzulässig, da die gesetzliche Höchstdauer von 6 Monaten überschritten wird. Die Kündigung nach 8 Monaten erfolgte außerhalb der zulässigen Probezeit. Es gelten daher die regulären Kündigungsfristen nach § 622 BGB. Die Kündigung könnte unwirksam sein, wenn die ordentliche Kündigungsfrist nicht eingehalten wurde. Der Arbeitnehmer sollte rechtliche Schritte prüfen."
        },
        {
            "instruction": "Erkläre die Gewährleistungsrechte beim Gebrauchtwagenkauf mit versteckten Mängeln.",
            "input": "Ein Käufer entdeckt nach 3 Wochen einen nicht offenbarten Unfallschaden am gekauften Gebrauchtwagen für 15.000 Euro.",
            "output": "Der Käufer hat umfassende Gewährleistungsrechte nach §§ 437 ff. BGB. Bei einem nicht offenbarten Unfallschaden liegt ein erheblicher Sachmangel vor. Der Käufer kann zunächst Nacherfüllung verlangen (Reparatur oder mangelfreie Ersatzlieferung). Nach erfolglosem Ablauf einer angemessenen Frist stehen Minderung des Kaufpreises oder Rücktritt vom Vertrag zur Wahl. Bei arglistiger Täuschung durch den Verkäufer ist zusätzlich eine Anfechtung nach § 123 BGB möglich, wodurch Schadensersatzansprüche entstehen können."
        },
        {
            "instruction": "Analysiere die Geschäftsführerhaftung bei Insolvenzverschleppung in einer GmbH.",
            "input": "Ein GmbH-Geschäftsführer hat trotz erkennbarer Überschuldung seit 2 Monaten weitere Verbindlichkeiten von 50.000 Euro eingegangen, ohne einen Insolvenzantrag zu stellen.",
            "output": "Der Geschäftsführer hat schwerwiegend gegen seine Pflichten nach §§ 15a, 64 InsO verstoßen. Bei Zahlungsunfähigkeit oder Überschuldung muss unverzüglich, spätestens nach drei Wochen, ein Insolvenzantrag gestellt werden. Durch das Eingehen weiterer Verbindlichkeiten macht er sich nach § 15a Abs. 4 InsO persönlich schadensersatzpflichtig gegenüber den neuen Gläubigern in Höhe von 50.000 Euro. Zusätzlich droht eine Haftung nach § 43 GmbHG wegen Verletzung der Geschäftsführerpflichten sowie strafrechtliche Verfolgung wegen Insolvenzverschleppung nach § 15a InsO."
        },
        {
            "instruction": "Bewerte einen Nachbarschaftsstreit wegen nächtlicher Lärmbelästigung.",
            "input": "Nachbar A spielt täglich von 22:00 bis 24:00 Uhr laute Musik mit 70 dB. Nachbar B kann nicht schlafen und hat bereits mehrfach gebeten aufzuhören.",
            "output": "Nachbar B hat begründete Ansprüche nach § 1004 BGB (Beseitigungs- und Unterlassungsanspruch) wegen Beeinträchtigung seines Eigentums. Nach den üblichen Hausordnungen und der Rechtsprechung beginnt die Nachtruhe um 22:00 Uhr. Laute Musik mit 70 dB nach 22:00 Uhr stellt eine unzumutbare Störung dar, die über das nach § 906 BGB hinzunehmende Maß hinausgeht. Trotz der Bitten wurde die Störung fortgesetzt. Nachbar B kann die sofortige Unterlassung der nächtlichen Ruhestörung verlangen und bei Fortdauer gerichtlichen Schutz durch einstweilige Verfügung suchen. Zusätzlich sind mietrechtliche Konsequenzen möglich."
        },
        {
            "instruction": "Erkläre die rechtlichen Grundlagen und Pflichten bei einem Kaufvertrag nach BGB.",
            "input": "Ein Unternehmer möchte einen Kaufvertrag für Büromöbel im Wert von 25.000 Euro abschließen. Welche rechtlichen Aspekte sind zu beachten?",
            "output": "Ein Kaufvertrag nach §§ 433 ff. BGB erfordert: 1) Einigung über die Kaufsache (genaue Spezifikation der Büromöbel), 2) Einigung über den Kaufpreis von 25.000 Euro, 3) Zwei übereinstimmende Willenserklärungen (Angebot und Annahme). Der Verkäufer verpflichtet sich zur Übereignung und mangelfreien Übergabe, der Käufer zur Zahlung und Abnahme. Wichtige Aspekte: Gewährleistung (§§ 437 ff. BGB) für 2 Jahre, Gefahrübergang (§ 446 BGB), Lieferzeit, eventuelle Rücktrittsrechte und AGB-Kontrolle bei Verwendung von Geschäftsbedingungen."
        },
        {
            "instruction": "Analysiere die Rechtslage bei einer fristlosen Kündigung wegen Arbeitszeitbetrug.",
            "input": "Ein Arbeitnehmer hat über 3 Monate systematisch seine Arbeitszeit um täglich 2 Stunden verkürzt, obwohl er Vollzeit bezahlt wird. Der Arbeitgeber möchte fristlos kündigen.",
            "output": "Eine fristlose Kündigung nach § 626 BGB ist hier grundsätzlich möglich, da systematischer Arbeitszeitbetrug einen wichtigen Grund darstellt. Voraussetzungen sind erfüllt: 1) Schwere Pflichtverletzung des Arbeitnehmers durch vorsätzliche Täuschung, 2) Unzumutbarkeit der Fortsetzung des Arbeitsverhältnisses für den Arbeitgeber, 3) Interessenabwägung fällt zugunsten des Arbeitgebers aus, 4) Zwei-Wochen-Frist nach § 626 Abs. 2 BGB ab Kenntnis muss eingehalten werden. Der systematische Betrug über 3 Monate rechtfertigt die sofortige Beendigung ohne Abmahnung. Zusätzlich kann Schadensersatz wegen der zu Unrecht gezahlten Vergütung verlangt werden."
        },
        {
            "instruction": "Erkläre die Verjährungsfristen verschiedener zivilrechtlicher Ansprüche.",
            "input": "Nach welchen Fristen verjähren Ansprüche aus Kaufverträgen, Delikten und Bereicherung?",
            "output": "Die Verjährungsfristen im deutschen Zivilrecht sind wie folgt geregelt: Die regelmäßige Verjährungsfrist beträgt nach § 195 BGB drei Jahre ab Ende des Jahres der Entstehung und Kenntnis des Anspruchs. Gewährleistungsansprüche beim Kauf verjähren nach § 438 BGB bei beweglichen Sachen in zwei Jahren, bei Bauwerken in fünf Jahren. Schadensersatzansprüche aus unerlaubter Handlung (Delikt) verjähren nach § 852 BGB in drei Jahren ab Kenntnis von Schaden und Schädiger, spätestens nach 30 Jahren. Herausgabeansprüche aus Eigentum sind nach § 197 BGB erst nach 30 Jahren verjährt. Bereicherungsansprüche unterliegen der dreijährigen Verjährungsfrist des § 195 BGB."
        }
    ]
    
    def format_instruction_following(example):
        """Format examples for German instruction-following training."""
        if example.get('input', '').strip():
            text = f"### Anweisung:\n{example['instruction']}\n\n### Eingabe:\n{example['input']}\n\n### Antwort:\n{example['output']}<|endoftext|>"
        else:
            text = f"### Anweisung:\n{example['instruction']}\n\n### Antwort:\n{example['output']}<|endoftext|>"
        return {"text": text}
    
    # Create dataset
    df = pd.DataFrame(german_legal_data)
    dataset = Dataset.from_pandas(df)
    dataset = dataset.map(format_instruction_following)
    
    # Split for training and validation
    dataset_split = dataset.train_test_split(test_size=0.2, seed=42)
    train_dataset = dataset_split['train']
    eval_dataset = dataset_split['test']
    
    print(f"✅ Dataset created: {len(train_dataset)} training, {len(eval_dataset)} validation examples")
    print(f"📝 Sample text preview:")
    print(train_dataset[0]['text'][:400] + "...")
    
    return train_dataset, eval_dataset

def load_model_and_tokenizer():
    """Load a suitable German model and tokenizer."""
    import torch
    from transformers import AutoTokenizer, AutoModelForCausalLM
    
    print("🤖 Loading model and tokenizer...")
    
    # Use a reliable, smaller German model for local training
    model_options = [
        'microsoft/DialoGPT-medium',  # Fallback - works reliably
        'dbmdz/german-gpt2',         # German-specific GPT-2
        'malteos/gpt2-wechsel-german' # Another German GPT-2
    ]
    
    model_name = None
    tokenizer = None
    
    for option in model_options:
        try:
            print(f"Trying {option}...")
            tokenizer = AutoTokenizer.from_pretrained(option)
            model_name = option
            print(f"✅ Successfully loaded tokenizer: {model_name}")
            break
        except Exception as e:
            print(f"⚠️ Failed to load {option}: {str(e)[:50]}...")
            continue
    
    if not model_name:
        raise Exception("Could not load any suitable model")
    
    # Configure tokenizer
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = "right"
    
    # Load model (CPU version for local development)
    print(f"📥 Loading model: {model_name}")
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        torch_dtype=torch.float32,  # Use float32 for CPU
        low_cpu_mem_usage=True,
        trust_remote_code=True
    )
    
    # Enable gradient checkpointing for memory efficiency
    if hasattr(model, 'gradient_checkpointing_enable'):
        model.gradient_checkpointing_enable()
    
    print(f"✅ Model loaded successfully!")
    print(f"🔢 Parameters: {model.num_parameters():,}")
    
    return model, tokenizer, model_name

def setup_lora_training(model, model_name):
    """Configure LoRA for efficient fine-tuning."""
    from peft import LoraConfig, get_peft_model, TaskType
    
    print("🎛️ Setting up LoRA configuration...")
    
    # Determine target modules based on model architecture
    if "gpt2" in model_name.lower() or "dialo" in model_name.lower():
        target_modules = ["c_attn", "c_proj", "c_fc"]
        print("🔧 Using GPT-2 style modules")
    else:
        # Default transformer modules
        target_modules = ["q_proj", "v_proj", "k_proj", "o_proj"]
        print("🔧 Using standard transformer modules")
    
    # LoRA configuration - conservative settings for stable training
    lora_config = LoraConfig(
        task_type=TaskType.CAUSAL_LM,
        r=16,                    # LoRA rank
        lora_alpha=32,           # LoRA scaling parameter
        lora_dropout=0.1,        # Dropout for regularization
        target_modules=target_modules,
        bias="none",
    )
    
    # Apply LoRA to the model
    model = get_peft_model(model, lora_config)
    
    # Print trainable parameter statistics
    def print_trainable_parameters(model):
        trainable_params = 0
        all_params = 0
        for _, param in model.named_parameters():
            all_params += param.numel()
            if param.requires_grad:
                trainable_params += param.numel()
        
        trainable_percentage = 100 * trainable_params / all_params
        print(f"🎯 Trainable parameters: {trainable_params:,}")
        print(f"🔢 All parameters: {all_params:,}")
        print(f"📊 Trainable percentage: {trainable_percentage:.2f}%")
    
    print_trainable_parameters(model)
    return model

def train_german_legal_model(model, tokenizer, train_dataset, eval_dataset):
    """Train the German legal AI model."""
    import torch
    from transformers import TrainingArguments, Trainer, DataCollatorForLanguageModeling
    
    print("🏋️ Setting up training configuration...")
    
    # Tokenization function
    def tokenize_function(examples):
        return tokenizer(
            examples["text"],
            truncation=True,
            padding=False,
            max_length=512,  # Reduced for local training
            return_overflowing_tokens=False,
        )
    
    # Tokenize datasets
    print("🔤 Tokenizing training data...")
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
    
    print(f"✅ Tokenization complete: {len(tokenized_train)} train, {len(tokenized_eval)} eval")
    
    # Training configuration optimized for local CPU/GPU
    output_dir = "./german-legal-model"
    training_args = TrainingArguments(
        output_dir=output_dir,
        overwrite_output_dir=True,
        
        # Training parameters
        num_train_epochs=3,                    # More epochs for better learning
        per_device_train_batch_size=2,        # Small batch for local training
        per_device_eval_batch_size=2,
        gradient_accumulation_steps=4,        # Effective batch size: 8
        learning_rate=5e-5,
        lr_scheduler_type="cosine",
        warmup_ratio=0.1,
        weight_decay=0.01,
        
        # Memory and performance
        fp16=torch.cuda.is_available(),       # Use fp16 only if GPU available
        gradient_checkpointing=True,
        dataloader_pin_memory=False,
        
        # Logging and evaluation
        logging_steps=10,
        eval_steps=25,
        evaluation_strategy="steps",
        save_steps=50,
        save_total_limit=3,
        load_best_model_at_end=True,
        metric_for_best_model="eval_loss",
        greater_is_better=False,
        
        # Other settings
        remove_unused_columns=False,
        report_to=None,  # Disable wandb/tensorboard
        run_name=f"german-legal-{datetime.now().strftime('%Y%m%d-%H%M')}",
        max_grad_norm=1.0,  # Gradient clipping
    )
    
    # Data collator for language modeling
    data_collator = DataCollatorForLanguageModeling(
        tokenizer=tokenizer,
        mlm=False,  # Causal language modeling, not masked
    )
    
    # Initialize trainer
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=tokenized_train,
        eval_dataset=tokenized_eval,
        data_collator=data_collator,
        tokenizer=tokenizer,
    )
    
    # Start training
    print(f"🚀 Starting training...")
    print(f"⏱️ Estimated time: {len(tokenized_train) * 3 // 8} minutes")
    
    start_time = time.time()
    
    try:
        # Clear memory cache if CUDA is available
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        
        # Train the model
        training_result = trainer.train()
        
        # Calculate training time
        training_time = time.time() - start_time
        
        print(f"\n✅ Training completed successfully!")
        print(f"⏱️ Training time: {training_time/60:.1f} minutes")
        print(f"📊 Final training loss: {training_result.training_loss:.4f}")
        
        # Save the model
        trainer.save_model()
        tokenizer.save_pretrained(output_dir)
        
        print(f"💾 Model saved to: {output_dir}")
        
        return trainer, output_dir
        
    except Exception as e:
        print(f"❌ Training failed: {str(e)}")
        
        # Try to save partial progress
        try:
            partial_dir = f"{output_dir}-partial"
            trainer.save_model(partial_dir)
            tokenizer.save_pretrained(partial_dir)
            print(f"💾 Partial model saved to: {partial_dir}")
        except:
            pass
        
        raise e

def test_trained_model(model, tokenizer):
    """Test the trained German legal AI model."""
    import torch
    
    print("🧪 Testing the trained model...")
    
    def generate_legal_response(instruction, input_text="", max_new_tokens=200):
        """Generate a response for a German legal question."""
        # Format the prompt
        if input_text.strip():
            prompt = f"### Anweisung:\n{instruction}\n\n### Eingabe:\n{input_text}\n\n### Antwort:\n"
        else:
            prompt = f"### Anweisung:\n{instruction}\n\n### Antwort:\n"
        
        # Tokenize the prompt
        inputs = tokenizer(prompt, return_tensors="pt")
        
        # Move to same device as model
        if torch.cuda.is_available() and next(model.parameters()).is_cuda:
            inputs = inputs.to("cuda")
        
        # Generate response
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                temperature=0.7,
                do_sample=True,
                top_p=0.9,
                repetition_penalty=1.1,
                pad_token_id=tokenizer.eos_token_id,
                eos_token_id=tokenizer.eos_token_id,
            )
        
        # Decode the response
        full_response = tokenizer.decode(outputs[0], skip_special_tokens=True)
        response = full_response[len(prompt):].strip()
        
        return response
    
    # Test cases covering various German legal scenarios
    test_cases = [
        {
            "instruction": "Erkläre die rechtlichen Probleme bei einer überhöhten Mietkaution.",
            "input": "Ein Vermieter fordert 4 Monatsmieten als Kaution für eine 900 Euro Wohnung."
        },
        {
            "instruction": "Bewerte eine Kündigung während der Probezeit.",
            "input": "Arbeitnehmer wird nach 10 Monaten gekündigt, Probezeit war auf 12 Monate vereinbart."
        },
        {
            "instruction": "Was sind die wichtigsten Rechte eines Käufers bei einem mangelhaften Auto?",
            "input": ""
        },
        {
            "instruction": "Analysiere einen Nachbarschaftsstreit wegen Lärmbelästigung.",
            "input": "Nachbar spielt jeden Abend ab 23 Uhr laute Musik für 2 Stunden."
        }
    ]
    
    print("\n" + "="*60)
    print("🔍 GERMAN LEGAL AI MODEL TEST RESULTS")
    print("="*60)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🔍 Test {i}:")
        print(f"Anweisung: {test_case['instruction']}")
        if test_case['input']:
            print(f"Eingabe: {test_case['input']}")
        
        try:
            response = generate_legal_response(test_case['instruction'], test_case['input'])
            print(f"\n📝 Antwort: {response[:400]}{'...' if len(response) > 400 else ''}")
        except Exception as e:
            print(f"\n❌ Error generating response: {str(e)[:100]}...")
        
        print("-" * 60)
    
    print("\n✅ Model testing completed!")

def create_deployment_package(output_dir, model_name):
    """Create a deployment package for the trained model."""
    import json
    import zipfile
    import shutil
    
    print("📦 Creating deployment package...")
    
    if not os.path.exists(output_dir):
        print(f"❌ Model directory {output_dir} not found")
        return None
    
    # Create export directory
    export_dir = "german-legal-deployment"
    if os.path.exists(export_dir):
        shutil.rmtree(export_dir)
    
    os.makedirs(export_dir)
    
    # Copy model files
    shutil.copytree(output_dir, f"{export_dir}/model")
    
    # Create configuration file
    config = {
        "model_info": {
            "name": "German Legal AI Assistant",
            "base_model": model_name,
            "type": "causal-lm-lora",
            "version": "1.0.0",
            "training_date": datetime.now().isoformat(),
            "language": "German",
            "domain": "Legal"
        },
        "training_config": {
            "epochs": 3,
            "batch_size": 2,
            "learning_rate": 5e-5,
            "lora_r": 16,
            "lora_alpha": 32,
            "max_length": 512
        },
        "inference_config": {
            "max_new_tokens": 256,
            "temperature": 0.7,
            "top_p": 0.9,
            "repetition_penalty": 1.1
        },
        "usage_instructions": {
            "prompt_format": "### Anweisung:\\n{instruction}\\n\\n### Eingabe:\\n{input}\\n\\n### Antwort:\\n",
            "example": "### Anweisung:\\nErkläre die rechtlichen Aspekte einer Mietkaution.\\n\\n### Antwort:\\n"
        }
    }
    
    with open(f"{export_dir}/config.json", "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    
    # Create README file
    readme_content = f"""# German Legal AI Model

## Overview
This is a fine-tuned German Legal AI assistant trained on German legal scenarios.

**Model Information:**
- Base Model: {model_name}
- Training Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}
- Language: German
- Domain: Legal advice and analysis

## Usage

### Loading the Model
```python
from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import PeftModel

# Load base model
base_model = AutoModelForCausalLM.from_pretrained("{model_name}")
tokenizer = AutoTokenizer.from_pretrained("./model")

# Load fine-tuned model
model = PeftModel.from_pretrained(base_model, "./model")
```

### Inference
```python
def generate_legal_advice(instruction, input_text=""):
    prompt = f"### Anweisung:\\n{{instruction}}\\n\\n### Eingabe:\\n{{input_text}}\\n\\n### Antwort:\\n"
    inputs = tokenizer(prompt, return_tensors="pt")
    outputs = model.generate(**inputs, max_new_tokens=256)
    return tokenizer.decode(outputs[0], skip_special_tokens=True)
```

## Deployment on AX102 Server
1. Extract this package to your server
2. Install required dependencies: transformers, peft, torch
3. Use the provided configuration for optimal performance
4. Integrate with your existing Docker setup

## Legal Disclaimer
This AI model provides general legal information for educational purposes only.
It should not be considered as professional legal advice.
Always consult with qualified legal professionals for specific legal matters.
"""
    
    with open(f"{export_dir}/README.md", "w", encoding="utf-8") as f:
        f.write(readme_content)
    
    # Create ZIP file
    timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
    zip_filename = f"german-legal-ai-{timestamp}.zip"
    
    with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(export_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, export_dir)
                zipf.write(file_path, arcname)
    
    print(f"✅ Deployment package created: {zip_filename}")
    print(f"📁 Contents:")
    print(f"   📂 model/ - Trained model files")
    print(f"   📄 config.json - Configuration and metadata")
    print(f"   📖 README.md - Usage instructions")
    
    return zip_filename

def main():
    """Main training pipeline for German Legal AI."""
    total_start_time = time.time()
    
    try:
        print("🚀 Starting German Legal AI Training Pipeline")
        print(f"📅 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Step 1: Install required packages
        print("\n" + "="*60)
        install_packages()
        
        # Step 2: Verify environment
        print("\n" + "="*60)
        print("🔍 Verifying environment...")
        if not check_environment():
            print("❌ Environment verification failed. Please check the installation.")
            return
        
        # Step 3: Create training dataset
        print("\n" + "="*60)
        train_dataset, eval_dataset = create_german_legal_dataset()
        
        # Step 4: Load model and tokenizer
        print("\n" + "="*60)
        model, tokenizer, model_name = load_model_and_tokenizer()
        
        # Step 5: Setup LoRA training
        print("\n" + "="*60)
        model = setup_lora_training(model, model_name)
        
        # Step 6: Train the model
        print("\n" + "="*60)
        trainer, output_dir = train_german_legal_model(model, tokenizer, train_dataset, eval_dataset)
        
        # Step 7: Test the trained model
        print("\n" + "="*60)
        test_trained_model(model, tokenizer)
        
        # Step 8: Create deployment package
        print("\n" + "="*60)
        zip_filename = create_deployment_package(output_dir, model_name)
        
        # Final summary
        total_time = time.time() - total_start_time
        print("\n" + "="*60)
        print("🎉 GERMAN LEGAL AI TRAINING COMPLETED SUCCESSFULLY!")
        print("="*60)
        print(f"⏱️ Total time: {total_time/60:.1f} minutes")
        print(f"📦 Deployment package: {zip_filename}")
        print(f"📁 Model directory: {output_dir}")
        print(f"🚀 Ready for deployment on your AX102 server!")
        
        print(f"\n📋 Next steps:")
        print(f"1. 📥 Download/copy {zip_filename} to your AX102 server")
        print(f"2. 📂 Extract the package to /opt/german-legal-ai/models/")
        print(f"3. 🔧 Update your Docker configuration to use the new model")
        print(f"4. 🚀 Start your services with: ./start.sh")
        
    except Exception as e:
        print(f"\n❌ Training failed with error: {str(e)}")
        print(f"💡 Check the error message above and try again")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()