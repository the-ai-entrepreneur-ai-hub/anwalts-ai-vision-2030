# 🌐 Strato.de DNS Setup for Portal-Anwalts.AI

## 📋 Strato DNS Configuration

You're in the right place! Here's exactly what to enter in your Strato DNS management:

### **🎯 A Record #1 (Main Domain)**
```
Name/Host: @ (or leave empty)
Type: A
Value/Target: 148.251.195.222
TTL: 3600 (or default)
```

### **🎯 A Record #2 (WWW Subdomain)**  
```
Name/Host: www
Type: A
Value/Target: 148.251.195.222
TTL: 3600 (or default)
```

## 📝 Step-by-Step in Strato Interface

1. **A Record for Root Domain:**
   - Field "Name" or "Host": Leave empty or enter `@`
   - Field "Points to" or "Target": `148.251.195.222`
   - Record Type: A
   - Click "Save" or "Add"

2. **A Record for WWW:**
   - Field "Name" or "Host": `www`
   - Field "Points to" or "Target": `148.251.195.222`  
   - Record Type: A
   - Click "Save" or "Add"

## ⏰ Propagation Time
- **Strato**: Usually 15-30 minutes
- **Global**: Up to 2-4 hours maximum

## ✅ Verification Commands

After saving in Strato, test with:
```bash
# Test root domain
nslookup portal-anwalts.ai

# Test www subdomain  
nslookup www.portal-anwalts.ai

# Both should return: 148.251.195.222
```

## 🔧 Alternative Verification

Use online tools while waiting:
- https://dnschecker.org
- https://whatsmydns.net
- Search for "portal-anwalts.ai"

## 🎯 Expected Results

Once DNS propagates:
```
portal-anwalts.ai → 148.251.195.222 ✅
www.portal-anwalts.ai → 148.251.195.222 ✅
```

## 🚀 After DNS Works

1. **Test HTTP**: Visit `http://portal-anwalts.ai` 
2. **Setup SSL**: Run on server: `certbot --nginx -d portal-anwalts.ai -d www.portal-anwalts.ai`
3. **Test HTTPS**: Visit `https://portal-anwalts.ai`

Your AnwaltsAI app with enhanced registration will be live! 🎉