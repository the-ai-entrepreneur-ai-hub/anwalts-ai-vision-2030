# 🇩🇪 German Legal AI - Single Cell Trainer (Copy this entire cell to Colab)

import subprocess
import sys
import os
import time
from datetime import datetime

print("🇩🇪 German Legal AI - Single Cell Training")
print("=" * 50)

# Step 1: Install packages
print("📦 Installing packages...")
packages = [
    "numpy==1.24.3",
    "torch==2.1.0 torchvision==0.16.0 torchaudio==2.1.0 --index-url https://download.pytorch.org/whl/cu121",
    "transformers==4.35.2",
    "datasets==2.14.6", 
    "accelerate==0.24.1",
    "peft==0.6.2",
    "bitsandbytes==0.41.2.post2",
    "huggingface_hub==0.17.3",
    "pandas==1.5.3"
]

for package in packages:
    print(f"Installing {package.split('==')[0]}...")
    result = subprocess.run([sys.executable, "-m", "pip", "install", "-q"] + package.split(), 
                          capture_output=True, text=True)

print("✅ Packages installed")

# Step 2: Import and check environment
import torch
import numpy as np
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig, TrainingArguments, Trainer, DataCollatorForLanguageModeling
from peft import LoraConfig, get_peft_model, TaskType
from datasets import Dataset
import pandas as pd
import json
import zipfile

print(f"✅ NumPy: {np.__version__}")
print(f"✅ PyTorch: {torch.__version__}")
print(f"✅ CUDA: {torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"✅ GPU: {torch.cuda.get_device_name(0)}")

# Step 3: Login to HuggingFace (if needed)
from huggingface_hub import notebook_login
print("🔐 Please log in to HuggingFace (press Enter if already logged in):")
try:
    notebook_login()
except:
    print("⚠️ Login skipped - using public models only")

# Step 4: Create German legal dataset
print("📊 Creating German legal dataset...")
data = [
    {
        "instruction": "Analysiere die rechtlichen Probleme bei einer überhöhten Mietkaution.",
        "input": "Der Vermieter verlangt eine Kaution von 5 Monatsmieten bei einer Wohnung mit 1.200 Euro Monatsmiete.",
        "output": "Die geforderte Kaution von 5 Monatsmieten (6.000 Euro) verstößt gegen § 551 BGB. Nach deutschem Mietrecht ist die Kaution auf maximal 3 Monatsmieten begrenzt. Die rechtlich zulässige Höchstkaution beträgt daher 3.600 Euro. Der Mieter kann die Zahlung der überschüssigen 2.400 Euro verweigern."
    },
    {
        "instruction": "Bewerte die Rechtmäßigkeit einer Kündigung in der Probezeit.",
        "input": "Ein Arbeitnehmer wird nach 8 Monaten gekündigt. Im Arbeitsvertrag ist eine Probezeit von 12 Monaten vereinbart.",
        "output": "Die vereinbarte Probezeit von 12 Monaten ist nach § 622 Abs. 3 BGB unzulässig, da die gesetzliche Höchstdauer von 6 Monaten überschritten wird. Die Kündigung nach 8 Monaten erfolgte außerhalb der zulässigen Probezeit und könnte unwirksam sein."
    },
    {
        "instruction": "Erkläre die Gewährleistungsrechte beim Gebrauchtwagenkauf.",
        "input": "Ein Käufer entdeckt nach 3 Wochen einen nicht offenbarten Unfallschaden am gekauften Gebrauchtwagen.",
        "output": "Der Käufer hat Gewährleistungsrechte nach §§ 437 ff. BGB. Bei einem nicht offenbarten Unfallschaden liegt ein Sachmangel vor. Der Käufer kann zunächst Nacherfüllung verlangen, dann Minderung oder Rücktritt wählen. Bei arglistiger Täuschung ist eine Anfechtung nach § 123 BGB möglich."
    },
    {
        "instruction": "Analysiere die Haftung eines GmbH-Geschäftsführers bei Insolvenzverschleppung.",
        "input": "Ein Geschäftsführer hat trotz Überschuldung weitere Verbindlichkeiten eingegangen.",
        "output": "Der Geschäftsführer hat seine Pflichten nach §§ 15a, 64 InsO verletzt. Bei Überschuldung muss unverzüglich ein Insolvenzantrag gestellt werden. Er macht sich nach § 15a Abs. 4 InsO schadensersatzpflichtig und riskiert strafrechtliche Verfolgung wegen Insolvenzverschleppung."
    },
    {
        "instruction": "Bewerte einen Nachbarschaftsstreit wegen Lärmbelästigung.",
        "input": "Nachbar A spielt täglich von 22:00 bis 24:00 Uhr laute Musik. Nachbar B fühlt sich gestört.",
        "output": "Nachbar B hat Ansprüche nach § 1004 BGB. Nach üblichen Hausordnungen beginnt die Nachtruhe um 22:00 Uhr. Laute Musik danach stellt eine unzumutbare Störung dar, die über das nach § 906 BGB hinzunehmende Maß hinausgeht. Nachbar B kann Unterlassung verlangen."
    },
    {
        "instruction": "Erkläre die rechtlichen Grundlagen eines Kaufvertrags nach BGB.",
        "input": "Welche wesentlichen Elemente muss ein Kaufvertrag enthalten?",
        "output": "Ein Kaufvertrag nach §§ 433 ff. BGB benötigt: 1) Einigung über die Kaufsache, 2) Einigung über den Kaufpreis, 3) Zwei übereinstimmende Willenserklärungen. Der Verkäufer verpflichtet sich zur Übereignung, der Käufer zur Zahlung. Wichtige Aspekte sind Gewährleistung und Gefahrübergang."
    }
]

def format_instruction(example):
    if example.get('input', '').strip():
        text = f"### Anweisung:\n{example['instruction']}\n\n### Eingabe:\n{example['input']}\n\n### Antwort:\n{example['output']}<|endoftext|>"
    else:
        text = f"### Anweisung:\n{example['instruction']}\n\n### Antwort:\n{example['output']}<|endoftext|>"
    return {"text": text}

df = pd.DataFrame(data)
dataset = Dataset.from_pandas(df)
dataset = dataset.map(format_instruction)
dataset = dataset.train_test_split(test_size=0.2, seed=42)
train_dataset, eval_dataset = dataset['train'], dataset['test']

print(f"✅ Dataset: {len(train_dataset)} train, {len(eval_dataset)} test")

# Step 5: Load model
print("🤖 Loading model...")
model_candidates = ['microsoft/DialoGPT-medium', 'DiscoResearch/DiscoLM_German_7b_v1']

model_name = None
for candidate in model_candidates:
    try:
        tokenizer = AutoTokenizer.from_pretrained(candidate)
        model_name = candidate
        print(f"✅ Using: {model_name}")
        break
    except:
        continue

if tokenizer.pad_token is None:
    tokenizer.pad_token = tokenizer.eos_token
tokenizer.padding_side = "right"

quantization_config = BitsAndBytesConfig(load_in_8bit=True, llm_int8_threshold=6.0)
model = AutoModelForCausalLM.from_pretrained(
    model_name,
    quantization_config=quantization_config,
    device_map="auto",
    trust_remote_code=True,
    torch_dtype=torch.float16
)
model.gradient_checkpointing_enable()

print(f"✅ Model loaded: {model.num_parameters():,} parameters")

# Step 6: Apply LoRA
print("🎛️ Applying LoRA...")
target_modules = ["c_attn", "c_proj"] if "DialoGPT" in model_name else ["q_proj", "v_proj", "k_proj", "o_proj"]

lora_config = LoraConfig(
    r=8, lora_alpha=16, target_modules=target_modules,
    lora_dropout=0.1, bias="none", task_type=TaskType.CAUSAL_LM
)
model = get_peft_model(model, lora_config)

trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
total = sum(p.numel() for p in model.parameters())
print(f"✅ LoRA: {trainable:,} trainable ({100*trainable/total:.2f}%)")

# Step 7: Prepare training
print("🔤 Tokenizing...")
def tokenize_function(examples):
    return tokenizer(examples["text"], truncation=True, padding=False, max_length=1024)

tokenized_train = train_dataset.map(tokenize_function, batched=True, remove_columns=train_dataset.column_names)
tokenized_eval = eval_dataset.map(tokenize_function, batched=True, remove_columns=eval_dataset.column_names)

output_dir = "./german-legal-model"
training_args = TrainingArguments(
    output_dir=output_dir, overwrite_output_dir=True, num_train_epochs=2,
    per_device_train_batch_size=1, gradient_accumulation_steps=8,
    learning_rate=5e-5, fp16=True, gradient_checkpointing=True,
    logging_steps=5, eval_steps=10, evaluation_strategy="steps",
    save_steps=20, save_total_limit=2, remove_unused_columns=False, report_to=None
)

data_collator = DataCollatorForLanguageModeling(tokenizer=tokenizer, mlm=False)
trainer = Trainer(
    model=model, args=training_args, train_dataset=tokenized_train,
    eval_dataset=tokenized_eval, data_collator=data_collator, tokenizer=tokenizer
)

# Step 8: Train
print("🏋️ Starting training...")
torch.cuda.empty_cache()
start_time = time.time()

try:
    training_result = trainer.train()
    training_time = time.time() - start_time
    
    print(f"✅ Training completed in {training_time/60:.1f} minutes")
    print(f"📊 Final loss: {training_result.training_loss:.4f}")
    
    trainer.save_model()
    tokenizer.save_pretrained(output_dir)
    
except Exception as e:
    print(f"❌ Training failed: {str(e)}")
    try:
        trainer.save_model(f"{output_dir}-partial")
        print("💾 Partial model saved")
    except:
        pass

# Step 9: Test model
print("🧪 Testing model...")
def generate_response(instruction, input_text=""):
    if input_text.strip():
        prompt = f"### Anweisung:\n{instruction}\n\n### Eingabe:\n{input_text}\n\n### Antwort:\n"
    else:
        prompt = f"### Anweisung:\n{instruction}\n\n### Antwort:\n"
    
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    with torch.no_grad():
        outputs = model.generate(**inputs, max_new_tokens=150, temperature=0.7, do_sample=True, top_p=0.9)
    
    response = tokenizer.decode(outputs[0], skip_special_tokens=True)
    return response[len(prompt):].strip()

tests = [
    ("Erkläre rechtliche Probleme bei überhöhter Mietkaution.", "Vermieter fordert 4 Monatsmieten."),
    ("Was sind Käuferrechte bei mangelhaftem Auto?", ""),
    ("Bewerte Kündigung in Probezeit.", "Nach 10 Monaten, bei 12 Monaten Probezeit.")
]

for i, (instruction, input_text) in enumerate(tests, 1):
    print(f"\n🔍 Test {i}: {instruction[:40]}...")
    try:
        response = generate_response(instruction, input_text)
        print(f"📝 Response: {response[:150]}...")
    except Exception as e:
        print(f"❌ Test failed: {str(e)[:50]}...")

# Step 10: Create deployment package
print("📦 Creating deployment package...")
config = {
    "model_info": {"name": "German Legal AI", "base_model": model_name, "version": "1.0", "training_date": datetime.now().isoformat()},
    "inference_config": {"max_new_tokens": 256, "temperature": 0.7, "top_p": 0.9}
}

with open(f"{output_dir}/config.json", "w") as f:
    json.dump(config, f, indent=2)

zip_name = f"german-legal-ai-{datetime.now().strftime('%Y%m%d-%H%M')}.zip"
with zipfile.ZipFile(zip_name, 'w', zipfile.ZIP_DEFLATED) as zipf:
    for root, dirs, files in os.walk(output_dir):
        for file in files:
            file_path = os.path.join(root, file)
            arcname = os.path.relpath(file_path, output_dir)
            zipf.write(file_path, arcname)

print(f"\n🎉 German Legal AI training completed!")
print(f"📦 Download: {zip_name}")
print(f"🚀 Ready for deployment on AX102!")
print(f"⏱️ Total time: {(time.time() - start_time)/60:.1f} minutes")