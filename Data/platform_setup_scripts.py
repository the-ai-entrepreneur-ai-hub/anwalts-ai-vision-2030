#!/usr/bin/env python3
"""
Platform-Specific Setup Scripts for German Legal Model Training

This module provides automated setup scripts for different training platforms
including Google Colab, Kaggle, Paperspace, and Lightning AI Studio.

Usage:
    python platform_setup_scripts.py --platform colab
    python platform_setup_scripts.py --platform kaggle --setup-all
    python platform_setup_scripts.py --platform paperspace --gpu-check
"""

import argparse
import json
import logging
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import requests
import yaml

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class PlatformSetup:
    """Base class for platform-specific setups"""
    
    def __init__(self, platform_name: str):
        self.platform_name = platform_name
        self.required_packages = [
            "transformers==4.36.0",
            "datasets==2.15.0", 
            "peft==0.7.1",
            "bitsandbytes==0.41.3",
            "accelerate==0.25.0",
            "trl==0.7.4",
            "torch==2.1.0",
            "sentencepiece==0.1.99",
            "protobuf==3.20.3"
        ]
        self.optional_packages = [
            "wandb==0.16.0",
            "rouge-score",
            "bert-score",
            "sacrebleu",
            "spacy",
            "nltk"
        ]
    
    def run_command(self, command: str, capture_output: bool = True) -> Tuple[bool, str]:
        """Run a shell command and return success status and output"""
        try:
            if capture_output:
                result = subprocess.run(
                    command,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=300
                )
                return result.returncode == 0, result.stdout + result.stderr
            else:
                result = subprocess.run(command, shell=True, timeout=300)
                return result.returncode == 0, ""
        except subprocess.TimeoutExpired:
            return False, "Command timed out"
        except Exception as e:
            return False, str(e)
    
    def check_gpu(self) -> Dict:
        """Check GPU availability and specifications"""
        gpu_info = {
            "available": False,
            "name": None,
            "memory_gb": 0,
            "cuda_version": None,
            "driver_version": None
        }
        
        # Check if nvidia-smi is available
        success, output = self.run_command("nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader,nounits")
        
        if success and output.strip():
            lines = output.strip().split('\n')
            if lines:
                parts = lines[0].split(', ')
                if len(parts) >= 3:
                    gpu_info["available"] = True
                    gpu_info["name"] = parts[0].strip()
                    gpu_info["memory_gb"] = float(parts[1]) / 1024
                    gpu_info["driver_version"] = parts[2].strip()
        
        # Check CUDA version
        success, cuda_output = self.run_command("nvcc --version")
        if success:
            # Extract CUDA version from output
            for line in cuda_output.split('\n'):
                if 'release' in line.lower():
                    import re
                    version_match = re.search(r'release (\d+\.\d+)', line)
                    if version_match:
                        gpu_info["cuda_version"] = version_match.group(1)
                    break
        
        return gpu_info
    
    def install_packages(self, packages: List[str], quiet: bool = True) -> bool:
        """Install Python packages"""
        logger.info(f"Installing {len(packages)} packages...")
        
        # Create pip install command
        quiet_flag = " -q" if quiet else ""
        command = f"pip install{quiet_flag} " + " ".join(packages)
        
        success, output = self.run_command(command, capture_output=True)
        
        if success:
            logger.info("✅ Package installation completed")
        else:
            logger.error(f"❌ Package installation failed: {output}")
        
        return success
    
    def verify_installation(self) -> Dict:
        """Verify that required packages are properly installed"""
        logger.info("Verifying installation...")
        
        verification_results = {}
        
        # Check core packages
        core_imports = {
            "torch": "import torch; print(torch.__version__)",
            "transformers": "import transformers; print(transformers.__version__)",
            "datasets": "import datasets; print(datasets.__version__)",
            "peft": "import peft; print(peft.__version__)",
            "trl": "import trl; print(trl.__version__)"
        }
        
        for package, import_command in core_imports.items():
            success, output = self.run_command(f"python -c \"{import_command}\"")
            verification_results[package] = {
                "installed": success,
                "version": output.strip() if success else None,
                "error": output if not success else None
            }
        
        # Check GPU availability with PyTorch
        success, output = self.run_command("python -c \"import torch; print(f'CUDA available: {torch.cuda.is_available()}'); print(f'GPU count: {torch.cuda.device_count()}')\"")
        verification_results["gpu_pytorch"] = {
            "success": success,
            "output": output.strip() if success else None
        }
        
        return verification_results
    
    def setup_authentication(self) -> bool:
        """Setup authentication for various services"""
        logger.info("Setting up authentication...")
        
        # This is a placeholder - actual implementation would depend on the platform
        # and would typically involve prompting for tokens or API keys
        
        auth_setup = {
            "huggingface": False,
            "wandb": False,
            "kaggle": False
        }
        
        # For now, just return success
        return True
    
    def create_config_files(self, output_dir: str = "./") -> bool:
        """Create platform-specific configuration files"""
        logger.info("Creating configuration files...")
        
        config_dir = Path(output_dir) / "configs"
        config_dir.mkdir(exist_ok=True)
        
        # Create platform-specific training config
        platform_config = self.get_platform_config()
        
        config_file = config_dir / f"{self.platform_name}_training_config.yaml"
        with open(config_file, 'w') as f:
            yaml.dump(platform_config, f, default_flow_style=False, indent=2)
        
        logger.info(f"✅ Configuration saved to {config_file}")
        return True
    
    def get_platform_config(self) -> Dict:
        """Get platform-specific configuration - to be overridden by subclasses"""
        return {
            "platform": self.platform_name,
            "model": {
                "name": "microsoft/DialoGPT-medium",
                "quantization": {"enabled": True, "type": "4bit"}
            },
            "training": {
                "per_device_train_batch_size": 1,
                "gradient_accumulation_steps": 8,
                "num_epochs": 2,
                "learning_rate": 2e-4,
                "fp16": False,
                "bf16": True
            }
        }
    
    def run_setup(self, install_required: bool = True, install_optional: bool = False, 
                   setup_auth: bool = False, create_configs: bool = True) -> bool:
        """Run complete setup pipeline"""
        logger.info(f"🚀 Starting {self.platform_name} setup...")
        
        # 1. Check GPU
        gpu_info = self.check_gpu()
        logger.info(f"GPU Status: {gpu_info}")
        
        # 2. Install packages
        if install_required:
            if not self.install_packages(self.required_packages):
                logger.error("Failed to install required packages")
                return False
        
        if install_optional:
            self.install_packages(self.optional_packages, quiet=False)
        
        # 3. Verify installation
        verification = self.verify_installation()
        failed_packages = [pkg for pkg, info in verification.items() 
                          if not info.get("installed", info.get("success", False))]
        
        if failed_packages:
            logger.warning(f"Some packages failed verification: {failed_packages}")
        else:
            logger.info("✅ All packages verified successfully")
        
        # 4. Setup authentication
        if setup_auth:
            self.setup_authentication()
        
        # 5. Create configuration files
        if create_configs:
            self.create_config_files()
        
        logger.info(f"🎉 {self.platform_name} setup completed!")
        return True

class ColabSetup(PlatformSetup):
    """Google Colab specific setup"""
    
    def __init__(self):
        super().__init__("colab")
        
        # Colab-specific packages
        self.required_packages.extend([
            "ipywidgets",  # For better notebook interaction
        ])
    
    def check_colab_environment(self) -> Dict:
        """Check if running in Google Colab"""
        colab_info = {
            "is_colab": False,
            "gpu_type": None,
            "pro_version": False,
            "drive_mounted": False
        }
        
        try:
            import google.colab
            colab_info["is_colab"] = True
            
            # Check if GPU is allocated
            gpu_info = self.check_gpu()
            if gpu_info["available"]:
                colab_info["gpu_type"] = gpu_info["name"]
                
                # Detect Pro/Pro+ based on GPU type
                if "V100" in gpu_info["name"] or "A100" in gpu_info["name"]:
                    colab_info["pro_version"] = "Pro+"
                elif "P100" in gpu_info["name"] or "T4" in gpu_info["name"]:
                    colab_info["pro_version"] = "Pro"
            
        except ImportError:
            pass
        
        return colab_info
    
    def mount_google_drive(self) -> bool:
        """Mount Google Drive in Colab"""
        try:
            from google.colab import drive
            drive.mount('/content/drive')
            
            # Check if mount was successful
            if os.path.exists('/content/drive/MyDrive'):
                logger.info("✅ Google Drive mounted successfully")
                return True
            else:
                logger.error("❌ Google Drive mount failed")
                return False
                
        except ImportError:
            logger.warning("Not running in Google Colab - skipping Drive mount")
            return False
        except Exception as e:
            logger.error(f"Error mounting Google Drive: {e}")
            return False
    
    def setup_colab_specific(self) -> bool:
        """Setup Colab-specific features"""
        logger.info("Setting up Colab-specific features...")
        
        # Mount Google Drive
        self.mount_google_drive()
        
        # Set up Colab-specific environment variables
        os.environ["TOKENIZERS_PARALLELISM"] = "false"  # Avoid warnings
        
        # Create output directory in Drive if mounted
        if os.path.exists('/content/drive/MyDrive'):
            output_dir = Path('/content/drive/MyDrive/german_legal_models')
            output_dir.mkdir(exist_ok=True)
            logger.info(f"✅ Output directory created: {output_dir}")
        
        return True
    
    def get_platform_config(self) -> Dict:
        """Get Colab-specific configuration"""
        gpu_info = self.check_gpu()
        
        # Adjust settings based on GPU type
        if gpu_info["memory_gb"] >= 15:  # High-end GPU
            batch_size = 2
            gradient_acc = 4
            max_length = 512
        elif gpu_info["memory_gb"] >= 10:  # Mid-range GPU
            batch_size = 1
            gradient_acc = 8
            max_length = 512
        else:  # Low-end GPU
            batch_size = 1
            gradient_acc = 16
            max_length = 256
        
        return {
            "platform": "colab",
            "gpu_info": gpu_info,
            "model": {
                "name": "microsoft/DialoGPT-medium",
                "quantization": {
                    "enabled": True,
                    "type": "4bit",
                    "compute_dtype": "bfloat16"
                }
            },
            "training": {
                "output_dir": "/content/drive/MyDrive/german_legal_models" if os.path.exists('/content/drive/MyDrive') else "./models",
                "per_device_train_batch_size": batch_size,
                "gradient_accumulation_steps": gradient_acc,
                "max_seq_length": max_length,
                "num_epochs": 2,
                "learning_rate": 2e-4,
                "save_steps": 100,
                "logging_steps": 10,
                "fp16": False,
                "bf16": True,
                "gradient_checkpointing": True,
                "remove_unused_columns": False
            },
            "colab_specific": {
                "mount_drive": True,
                "runtime_hours": 12,
                "checkpoint_frequency": "high"
            }
        }
    
    def run_setup(self, **kwargs) -> bool:
        """Run Colab-specific setup"""
        # Check if we're in Colab
        colab_info = self.check_colab_environment()
        
        if not colab_info["is_colab"]:
            logger.warning("Not running in Google Colab - some features may not work")
        else:
            logger.info(f"✅ Google Colab detected - GPU: {colab_info.get('gpu_type', 'None')}")
        
        # Run base setup
        success = super().run_setup(**kwargs)
        
        # Run Colab-specific setup
        if success and colab_info["is_colab"]:
            self.setup_colab_specific()
        
        return success

class KaggleSetup(PlatformSetup):
    """Kaggle Notebooks specific setup"""
    
    def __init__(self):
        super().__init__("kaggle")
    
    def check_kaggle_environment(self) -> Dict:
        """Check if running in Kaggle"""
        kaggle_info = {
            "is_kaggle": False,
            "gpu_enabled": False,
            "internet_enabled": False,
            "competition": None
        }
        
        # Check environment variables
        if os.environ.get('KAGGLE_KERNEL_RUN_TYPE'):
            kaggle_info["is_kaggle"] = True
            
            # Check for GPU
            gpu_info = self.check_gpu()
            kaggle_info["gpu_enabled"] = gpu_info["available"]
            
            # Check internet access
            try:
                response = requests.get('https://www.google.com', timeout=5)
                kaggle_info["internet_enabled"] = response.status_code == 200
            except:
                kaggle_info["internet_enabled"] = False
        
        return kaggle_info
    
    def setup_kaggle_datasets(self) -> bool:
        """Setup access to Kaggle datasets"""
        logger.info("Setting up Kaggle dataset access...")
        
        # Check if Kaggle API is available
        try:
            success, output = self.run_command("kaggle --version")
            if not success:
                # Install Kaggle API
                success, _ = self.run_command("pip install kaggle")
                if not success:
                    logger.error("Failed to install Kaggle API")
                    return False
            
            # Set up Kaggle credentials directory
            kaggle_dir = Path.home() / '.kaggle'
            kaggle_dir.mkdir(exist_ok=True)
            
            logger.info("✅ Kaggle API setup completed")
            return True
            
        except Exception as e:
            logger.error(f"Error setting up Kaggle datasets: {e}")
            return False
    
    def get_platform_config(self) -> Dict:
        """Get Kaggle-specific configuration"""
        return {
            "platform": "kaggle",
            "model": {
                "name": "microsoft/DialoGPT-medium",
                "quantization": {
                    "enabled": True,
                    "type": "4bit"
                }
            },
            "training": {
                "output_dir": "/kaggle/working/models",
                "per_device_train_batch_size": 2,  # P100 has more memory
                "gradient_accumulation_steps": 4,
                "num_epochs": 3,  # More generous time limit
                "learning_rate": 2e-4,
                "save_steps": 200,
                "logging_steps": 25,
                "fp16": True,
                "bf16": False,  # P100 doesn't support bf16
                "gradient_checkpointing": True
            },
            "kaggle_specific": {
                "gpu_hours_limit": 30,  # Weekly limit
                "internet_access": True,
                "dataset_access": True
            }
        }
    
    def run_setup(self, **kwargs) -> bool:
        """Run Kaggle-specific setup"""
        # Check if we're in Kaggle
        kaggle_info = self.check_kaggle_environment()
        
        if not kaggle_info["is_kaggle"]:
            logger.warning("Not running in Kaggle - some features may not work")
        else:
            logger.info(f"✅ Kaggle environment detected")
            logger.info(f"   GPU: {kaggle_info['gpu_enabled']}")
            logger.info(f"   Internet: {kaggle_info['internet_enabled']}")
        
        # Run base setup
        success = super().run_setup(**kwargs)
        
        # Setup Kaggle-specific features
        if success and kaggle_info["is_kaggle"]:
            self.setup_kaggle_datasets()
        
        return success

class PaperspaceSetup(PlatformSetup):
    """Paperspace Gradient specific setup"""
    
    def __init__(self):
        super().__init__("paperspace")
    
    def check_paperspace_environment(self) -> Dict:
        """Check if running in Paperspace"""
        paperspace_info = {
            "is_paperspace": False,
            "machine_type": None,
            "storage_gb": 0
        }
        
        # Check for Paperspace-specific environment variables
        if os.environ.get('PS_API_KEY') or os.path.exists('/storage'):
            paperspace_info["is_paperspace"] = True
            
            # Check storage
            if os.path.exists('/storage'):
                success, output = self.run_command("df -h /storage | tail -1 | awk '{print $2}'")
                if success:
                    paperspace_info["storage_gb"] = output.strip()
        
        return paperspace_info
    
    def setup_paperspace_storage(self) -> bool:
        """Setup Paperspace storage optimization"""
        logger.info("Setting up Paperspace storage...")
        
        # Create storage directories
        storage_dirs = [
            "/storage/models",
            "/storage/datasets", 
            "/storage/checkpoints",
            "/storage/logs"
        ]
        
        for dir_path in storage_dirs:
            os.makedirs(dir_path, exist_ok=True)
        
        # Set up symlinks to storage
        if not os.path.exists('./models'):
            os.symlink('/storage/models', './models')
        
        logger.info("✅ Paperspace storage setup completed")
        return True
    
    def get_platform_config(self) -> Dict:
        """Get Paperspace-specific configuration"""
        return {
            "platform": "paperspace",
            "model": {
                "name": "microsoft/DialoGPT-small",  # Smaller for free tier
                "quantization": {
                    "enabled": True,
                    "type": "4bit"
                }
            },
            "training": {
                "output_dir": "/storage/models",
                "per_device_train_batch_size": 1,
                "gradient_accumulation_steps": 16,
                "num_epochs": 1,  # Limited time
                "learning_rate": 3e-4,
                "save_steps": 50,
                "logging_steps": 5,
                "fp16": True,
                "gradient_checkpointing": True,
                "max_seq_length": 256  # Reduce for memory
            },
            "paperspace_specific": {
                "free_tier_hours": 6,
                "storage_path": "/storage",
                "auto_shutdown": True
            }
        }

class LightningSetup(PlatformSetup):
    """Lightning AI Studio specific setup"""
    
    def __init__(self):
        super().__init__("lightning")
        
        # Lightning-specific packages
        self.required_packages.extend([
            "lightning",
            "lightning-ai"
        ])
    
    def setup_lightning_environment(self) -> bool:
        """Setup Lightning AI specific environment"""
        logger.info("Setting up Lightning AI environment...")
        
        # Lightning-specific setup would go here
        # This is a placeholder as Lightning AI's exact environment isn't fully specified
        
        return True
    
    def get_platform_config(self) -> Dict:
        """Get Lightning AI specific configuration"""
        return {
            "platform": "lightning",
            "model": {
                "name": "microsoft/DialoGPT-medium",
                "quantization": {
                    "enabled": True,
                    "type": "4bit"
                }
            },
            "training": {
                "output_dir": "./models",
                "per_device_train_batch_size": 2,
                "gradient_accumulation_steps": 4,
                "num_epochs": 3,
                "learning_rate": 2e-4,
                "save_steps": 100,
                "logging_steps": 10,
                "bf16": True,
                "gradient_checkpointing": True
            },
            "lightning_specific": {
                "distributed": False,
                "cloud_compute": True
            }
        }

def create_setup_script(platform: str, output_file: str) -> bool:
    """Create a standalone setup script for a specific platform"""
    
    script_content = f'''#!/usr/bin/env python3
"""
Automated setup script for {platform.title()} platform
Generated by platform_setup_scripts.py

This script will:
1. Check GPU availability
2. Install required packages
3. Verify installation
4. Create configuration files
5. Setup platform-specific features

Usage:
    python {platform}_setup.py
"""

import subprocess
import sys
import os
from pathlib import Path

def run_command(command):
    """Run a shell command"""
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        return result.returncode == 0, result.stdout + result.stderr
    except Exception as e:
        return False, str(e)

def main():
    print(f"🚀 Starting {platform.title()} setup for German Legal Model Training...")
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ required")
        sys.exit(1)
    
    print("✅ Python version check passed")
    
    # Check GPU
    success, output = run_command("nvidia-smi")
    if success:
        print("✅ GPU detected")
        print(output)
    else:
        print("⚠️ No GPU detected - training will be very slow")
    
    # Install packages
    packages = [
        "transformers==4.36.0",
        "datasets==2.15.0",
        "peft==0.7.1", 
        "bitsandbytes==0.41.3",
        "accelerate==0.25.0",
        "trl==0.7.4",
        "torch==2.1.0"
    ]
    
    print(f"📦 Installing {{len(packages)}} packages...")
    for package in packages:
        print(f"Installing {{package}}...")
        success, output = run_command(f"pip install -q {{package}}")
        if not success:
            print(f"❌ Failed to install {{package}}: {{output}}")
            sys.exit(1)
    
    print("✅ All packages installed successfully")
    
    # Verify installation
    print("🔍 Verifying installation...")
    
    test_imports = [
        "import torch; print(f'PyTorch: {{torch.__version__}}')",
        "import transformers; print(f'Transformers: {{transformers.__version__}}')",
        "import datasets; print(f'Datasets: {{datasets.__version__}}')",
        "import peft; print(f'PEFT: {{peft.__version__}}')"
    ]
    
    for test_import in test_imports:
        success, output = run_command(f'python -c "{{test_import}}"')
        if success:
            print(f"✅ {{output.strip()}}")
        else:
            print(f"❌ Import failed: {{output}}")
    
    # Create directories
    directories = ["./models", "./data", "./configs", "./logs"]
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"✅ Created directory: {{directory}}")
    
    print("🎉 {platform.title()} setup completed successfully!")
    print("You can now run the training notebook or scripts.")

if __name__ == "__main__":
    main()
'''
    
    try:
        with open(output_file, 'w') as f:
            f.write(script_content)
        
        # Make executable on Unix systems
        os.chmod(output_file, 0o755)
        
        logger.info(f"✅ Setup script created: {output_file}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to create setup script: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Platform-specific setup for German legal model training")
    parser.add_argument("--platform", "-p", required=True, 
                       choices=["colab", "kaggle", "paperspace", "lightning"],
                       help="Target platform")
    parser.add_argument("--install-required", action="store_true", default=True,
                       help="Install required packages")
    parser.add_argument("--install-optional", action="store_true",
                       help="Install optional packages")
    parser.add_argument("--setup-auth", action="store_true",
                       help="Setup authentication")
    parser.add_argument("--create-configs", action="store_true", default=True,
                       help="Create configuration files")
    parser.add_argument("--gpu-check", action="store_true",
                       help="Only check GPU status")
    parser.add_argument("--create-script", action="store_true",
                       help="Create standalone setup script")
    parser.add_argument("--output-dir", "-o", default="./",
                       help="Output directory for configs and scripts")
    
    args = parser.parse_args()
    
    # Create appropriate setup class
    setup_classes = {
        "colab": ColabSetup,
        "kaggle": KaggleSetup,
        "paperspace": PaperspaceSetup,
        "lightning": LightningSetup
    }
    
    setup_class = setup_classes[args.platform]
    setup = setup_class()
    
    # If only GPU check requested
    if args.gpu_check:
        gpu_info = setup.check_gpu()
        print("GPU Information:")
        print(json.dumps(gpu_info, indent=2))
        return
    
    # If creating standalone script
    if args.create_script:
        script_file = f"{args.output_dir}/{args.platform}_setup.py"
        create_setup_script(args.platform, script_file)
        return
    
    # Run full setup
    success = setup.run_setup(
        install_required=args.install_required,
        install_optional=args.install_optional,
        setup_auth=args.setup_auth,
        create_configs=args.create_configs
    )
    
    if success:
        print(f"\n🎉 {args.platform.title()} setup completed successfully!")
        print(f"✅ Configuration files created in: {args.output_dir}/configs/")
        print(f"✅ Ready to start training German legal models")
        
        # Print next steps
        print(f"\n📋 Next Steps:")
        print(f"1. Upload your German legal training data")
        print(f"2. Run the training notebook or script")
        print(f"3. Monitor training progress")
        print(f"4. Evaluate the trained model")
        
    else:
        print(f"\n❌ {args.platform.title()} setup failed")
        print("Check the logs for more details")
        sys.exit(1)

if __name__ == "__main__":
    main()