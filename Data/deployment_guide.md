# 🇩🇪 German Legal AI - Complete Deployment Guide

## 📋 Table of Contents

1. [Training Phase (Google Colab)](#training-phase)
2. [Model Preparation](#model-preparation)
3. [Server Deployment (AX102)](#server-deployment)
4. [Testing & Validation](#testing--validation)
5. [Production Optimization](#production-optimization)
6. [Monitoring & Maintenance](#monitoring--maintenance)

---

## 🚀 Training Phase (Google Colab)

### Step 1: Dataset Preparation

```bash
# On your local machine, prepare the dataset
python dataset_preparation.py --sample-data --output-dir ./dataset

# Upload the dataset to Google Drive or directly to Colab
```

### Step 2: Google Colab Training

1. **Open the training notebook**: `german_legal_training_colab.ipynb`
2. **Select GPU runtime**: Runtime → Change runtime type → GPU (A100 recommended)
3. **Execute all cells** in sequence
4. **Monitor training progress** through the logs
5. **Download the trained model** files when complete

### Expected Training Time
- **DiscoLM 7B with LoRA**: 2-4 hours on A100
- **Dataset size**: 1,000+ examples recommended
- **Memory usage**: ~15GB GPU memory with quantization

---

## 🏗️ Model Preparation

### Step 3: Download and Organize Models

After training in Colab, you'll have:
```
german-legal-model.zip
├── disco-german-legal-7b/           # LoRA fine-tuned model
│   ├── adapter_config.json
│   ├── adapter_model.bin
│   └── tokenizer files...
├── disco-german-legal-7b-gptq/      # Quantized model
│   ├── model.safetensors
│   ├── quantize_config.json
│   └── config files...
└── deployment_config.json
```

### Step 4: Transfer to AX102 Server

```bash
# On AX102 server
cd /opt/german-legal-ai
wget [your-colab-download-link]/german-legal-model.zip
unzip german-legal-model.zip
```

---

## 🖥️ Server Deployment (AX102)

### System Requirements Verification
- **CPU**: Ryzen 9 7950X3D ✅
- **RAM**: 128GB ✅  
- **Storage**: 2×1.92TB NVMe ✅
- **OS**: Ubuntu 22.04 LTS (recommended)

### Step 5: Docker Environment Setup

```bash
# Install Docker and Docker Compose
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Clone deployment files
git clone [your-repo] /opt/german-legal-ai
cd /opt/german-legal-ai
```

### Step 6: Configure Environment

```bash
# Create environment file
cat > .env << EOF
# Model Configuration
MODEL_PATH=/models/disco-german-legal-7b
QUANTIZED_MODEL_PATH=/models/disco-german-legal-7b-gptq
USE_QUANTIZED=true

# Performance Settings
TORCH_NUM_THREADS=28
OMP_NUM_THREADS=28
MKL_NUM_THREADS=28

# Redis Configuration
REDIS_HOST=redis
REDIS_PORT=6379

# API Configuration
MAX_CONTEXT_LENGTH=2048
BATCH_SIZE=4
TEMPERATURE=0.7
TOP_P=0.9
EOF
```

### Step 7: Launch Services

```bash
# Start the complete stack
docker-compose up -d

# Verify services are running
docker-compose ps

# Check logs
docker-compose logs -f german-legal-ai
```

### Alternative Deployment Options

#### Option A: Simple Ollama Deployment
```bash
# Quick start with Ollama
docker-compose up -d ollama-server
docker exec -it ollama-german-legal ollama pull disco-lm-german-7b
```

#### Option B: High-Performance vLLM
```bash
# For maximum performance (if you have GPU later)
docker-compose --profile vllm up -d
```

---

## 🧪 Testing & Validation

### Step 8: Health Checks

```bash
# Check service health
curl http://localhost/health

# Expected response:
{
  "status": "healthy",
  "model_loaded": true,
  "system_info": {
    "cpu_percent": 25.0,
    "memory_percent": 15.2,
    "memory_available_gb": 108.5,
    "torch_threads": 28
  }
}
```

### Step 9: Model Testing

```bash
# Test German legal processing
curl -X POST http://localhost/api/generate \
  -H "Content-Type: application/json" \
  -d '{
    "instruction": "Analysiere die rechtlichen Aspekte einer Kündigung während der Probezeit.",
    "input_text": "Ein Arbeitnehmer wurde nach 8 Monaten Probezeit gekündigt.",
    "max_length": 512,
    "temperature": 0.7
  }'
```

### Step 10: Performance Benchmarking

```bash
# Install testing tools
pip install locust requests

# Run performance test
python performance_test.py --host http://localhost --users 10 --spawn-rate 2 --run-time 5m
```

---

## ⚡ Production Optimization

### Step 11: Memory Optimization

```bash
# Configure huge pages for better performance
echo 'vm.nr_hugepages=65536' >> /etc/sysctl.conf
echo 'vm.swappiness=10' >> /etc/sysctl.conf
sysctl -p
```

### Step 12: CPU Optimization for Ryzen 9 7950X3D

```bash
# Set CPU governor to performance
echo performance | tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor

# Disable CPU frequency scaling
echo 1 > /sys/devices/system/cpu/intel_pstate/no_turbo  # If Intel
# Or for AMD:
echo 0 > /sys/devices/system/cpu/cpufreq/boost
```

### Step 13: Load Balancing Configuration

```bash
# Configure Nginx for optimal performance
# (nginx.conf is already optimized in the repo)

# Test Nginx configuration
docker exec german-legal-nginx nginx -t

# Reload if needed
docker exec german-legal-nginx nginx -s reload
```

---

## 📊 Monitoring & Maintenance

### Step 14: Set Up Monitoring

Access monitoring dashboards:
- **Grafana**: http://localhost:3000 (admin/admin123)
- **Prometheus**: http://localhost:9090
- **Model metrics**: http://localhost/metrics

### Step 15: Log Management

```bash
# Set up log rotation
cat > /etc/logrotate.d/german-legal-ai << EOF
/opt/german-legal-ai/logs/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    create 644 root root
    postrotate
        docker-compose restart german-legal-ai
    endscript
}
EOF
```

### Step 16: Auto-scaling Setup

```bash
# Monitor resource usage
docker stats german-legal-ai

# Scale based on CPU/Memory usage
# If CPU > 80% consistently:
docker-compose up -d --scale german-legal-ai=2
```

---

## 🔧 Performance Tuning Guide

### Expected Performance on AX102

| Model Configuration | Tokens/Second | Memory Usage | Response Time |
|-------------------|---------------|---------------|---------------|
| DiscoLM 7B (Q5_K_M) | 15-25 | 8GB | 2-5 seconds |
| DiscoLM 7B (Q8_0) | 12-20 | 12GB | 3-6 seconds |
| SauerkrautLM 7B (Q5_K_M) | 15-25 | 8GB | 2-5 seconds |
| Mixtral 8x7B (Q4_K_M) | 8-15 | 32GB | 5-10 seconds |

### Optimization Tips

1. **Use Q5_K_M quantization** for best balance of quality/speed
2. **Set batch_size=4** for optimal throughput
3. **Enable model caching** with Redis
4. **Use connection pooling** for high-concurrency scenarios
5. **Monitor CPU temperature** - the Ryzen 9 7950X3D runs hot under sustained load

---

## 🚨 Troubleshooting

### Common Issues

#### Model Loading Fails
```bash
# Check model files exist
ls -la models/disco-german-legal-7b/

# Verify permissions
chown -R 1000:1000 models/

# Check logs
docker-compose logs german-legal-ai
```

#### Out of Memory Errors
```bash
# Reduce batch size
export BATCH_SIZE=2

# Use more aggressive quantization
export USE_QUANTIZED=true

# Check available memory
free -h
```

#### Slow Response Times
```bash
# Check CPU usage
htop

# Verify thread configuration
docker exec german-legal-ai printenv | grep THREAD

# Monitor model performance
curl http://localhost/metrics
```

---

## 📈 Scaling for Production

### Horizontal Scaling
```bash
# Run multiple model instances
docker-compose up -d --scale german-legal-ai=3

# Configure load balancer
# (nginx.conf already includes load balancing)
```

### Vertical Scaling
```bash
# Increase resource limits
# Edit docker-compose.yml:
deploy:
  resources:
    limits:
      memory: 64G    # Increase from 32G
      cpus: '30'     # Use more cores
```

---

## 🔐 Security Considerations

### Step 17: Security Hardening

```bash
# Enable firewall
ufw enable
ufw allow 80
ufw allow 443
ufw allow 22  # SSH only

# Use SSL certificates (Let's Encrypt)
certbot --nginx -d your-domain.com

# Configure rate limiting (already in nginx.conf)
# Monitor for abuse
tail -f /var/log/nginx/access.log | grep -E "429|503"
```

---

## 📞 Support & Maintenance

### Daily Maintenance
- Check service health: `docker-compose ps`
- Monitor resource usage: `docker stats`
- Review logs: `docker-compose logs --tail=100`

### Weekly Maintenance
- Update model weights if retrained
- Backup configuration and logs
- Performance benchmarking

### Monthly Maintenance
- Update Docker images
- Security patches
- Capacity planning review

---

## 🎯 Success Metrics

Your deployment is successful when:
- ✅ Health endpoint returns "healthy"
- ✅ Model generates coherent German legal responses
- ✅ Response time < 10 seconds for typical queries
- ✅ Memory usage stable < 50% of available RAM
- ✅ No service crashes for 24+ hours
- ✅ Monitoring dashboards show green metrics

## 📚 Additional Resources

- **Model Hub**: [DiscoLM German Models](https://huggingface.co/DiscoResearch)
- **Documentation**: [Transformers German Models](https://huggingface.co/docs/transformers)
- **Performance Tuning**: [Optimizing Inference on CPU](https://huggingface.co/docs/transformers/performance)
- **Docker Best Practices**: [Production Docker Deployments](https://docs.docker.com/develop/dev-best-practices/)

---

**🚀 Ready to deploy your German Legal AI system!**