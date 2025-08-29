# 🚀 AnwaltsAI - Together API Setup Guide

Your AnwaltsAI app is **already integrated** with Together API! Follow these steps to get it running.

## ✅ What's Already Done

Your app includes:
- ✅ Together API integration (`backend/ai_service.py`)
- ✅ German legal system prompts
- ✅ Document generation endpoints
- ✅ Cost tracking and model selection
- ✅ Professional email generation
- ✅ Legal clause creation
- ✅ Frontend API client ready

## 🔑 Step 1: Get Together API Key

1. Go to **https://api.together.xyz/**
2. **Sign up** or **log in**
3. **Create API key** from dashboard
4. **Copy the key** (starts with something like `abcd1234...`)

## 📝 Step 2: Configure Environment

**Option A: Create .env file (Recommended)**
```bash
# Navigate to backend folder
cd backend

# Create .env file with your API key
echo TOGETHER_API_KEY=your_actual_api_key_here > .env
echo DEFAULT_AI_MODEL=deepseek-ai/DeepSeek-V3 >> .env
```

**Option B: Set Windows Environment Variable**
```cmd
set TOGETHER_API_KEY=your_actual_api_key_here
```

## 🧪 Step 3: Test API Connection

Run the test script:
```bash
# From Law Firm Vision 2030 folder
python test_together_api.py
```

Expected output:
```
✅ API Key found: abcd1234...
✅ Completion successful
✅ Document generation successful
✅ Email generation successful
🎉 Your AnwaltsAI app is ready to use Together API
```

## 🚀 Step 4: Start Your App

**Quick Start (Automated):**
```bash
# Double-click or run:
start_anwalts_ai.bat
```

**Manual Start:**
```bash
# Terminal 1: Start backend
cd backend
python main.py

# Terminal 2: Open frontend
start Client/anwalts_ai_enhanced.html
```

## 🎯 Step 5: Test in Browser

1. **Open**: http://localhost:5001 (or frontend HTML file)
2. **Login** with your credentials
3. **Generate Document**: 
   - Type: "Erstelle einen Mietvertrag für Max Mustermann"
   - Click "Generate"
   - Watch AI create German legal document!

## 📊 Available AI Models

Your app supports these models:

### 🥇 **Recommended for German Legal Work**
- **DeepSeek-V3** (`deepseek-ai/DeepSeek-V3`)
  - Best for complex German legal reasoning
  - Cost: $0.27 input, $1.10 output per 1M tokens
  - Context: 64K tokens

### 🥈 **Alternatives**
- **Llama 3.1 70B** (`meta-llama/Llama-3.1-70B-Instruct-Turbo`)
  - Good balance of cost/performance
  - Cost: $0.88 per 1M tokens
  
- **Llama 3.1 8B** (`meta-llama/Llama-3.1-8B-Instruct-Turbo`)
  - Fastest and cheapest
  - Cost: $0.18 per 1M tokens

## 🛠️ Advanced Configuration

### Change Default Model
Edit `backend/.env`:
```
DEFAULT_AI_MODEL=meta-llama/Llama-3.1-70B-Instruct-Turbo
```

### API Endpoints Available
- `POST /api/ai/generate-document` - Full document generation
- `POST /api/ai/generate-document-simple` - Quick generation
- `POST /api/ai/generate-email` - Email responses
- `POST /api/ai/generate-clause` - Legal clauses

### Cost Monitoring
Each API call returns cost estimates:
```json
{
  "content": "Generated text...",
  "tokens_used": 1500,
  "cost_estimate": 0.002,
  "generation_time_ms": 3000,
  "model_used": "deepseek-ai/DeepSeek-V3"
}
```

## ❌ Troubleshooting

### "API Key not found"
- Check `.env` file exists in `backend/` folder
- Verify API key is correct (no extra spaces)
- Try setting system environment variable

### "Connection failed"
- Check internet connection
- Verify API key is valid on Together website
- Try different model in case one is down

### "Model not found"
- Check model name spelling
- Try default model: `deepseek-ai/DeepSeek-V3`
- Check Together API documentation for available models

### Frontend not connecting
- Backend must be running on port 5001
- Check browser console for errors
- Verify CORS settings in `main.py`

## 🔮 Future Migration to Your DeepSeek Model

When your trained German Legal BERT is ready:

1. **Deploy model** to Together API (when available)
2. **Update** `DEFAULT_AI_MODEL` to your model ID
3. **No code changes needed** - same API interface!

## 📈 Production Tips

- **Monitor costs** via Together dashboard
- **Set usage limits** to avoid overage
- **Use caching** for repeated queries
- **Log API calls** for debugging
- **Backup important generations**

## 🎉 Success!

Your AnwaltsAI app now has **professional German legal AI** capabilities:
- ✅ Document generation (Verträge, Briefe, etc.)
- ✅ Email responses (professional legal correspondence) 
- ✅ Legal clauses (rechtssichere Klauseln)
- ✅ Cost tracking and optimization
- ✅ Multiple model options

**Ready for production use!** 🚀