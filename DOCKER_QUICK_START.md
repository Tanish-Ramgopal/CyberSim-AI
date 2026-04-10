# Docker Container - Quick Start Visual Guide

## The Simplest Way (Copy & Paste)

### 1️⃣ Open PowerShell
Click Windows icon → Type "powershell" → Click Windows PowerShell

### 2️⃣ Navigate to Your Project
```powershell
cd "C:\Users\Tanish Ramgopal\Documents\Tanish\Meta Hackathon 2026"
```

### 3️⃣ Choose Your API Provider & Copy Command

#### **OPTION A: OpenAI (Most Popular)**

Go get your key here: https://platform.openai.com/api-keys

Then copy & paste:
```powershell
docker run -d -p 7860:7860 `
  -e API_BASE_URL="https://api.openai.com/v1" `
  -e MODEL_NAME="gpt-4o-mini" `
  -e HF_TOKEN="sk_live_PASTE_YOUR_KEY_HERE" `
  --name cybersim-server `
  cybersim:latest
```

**Replace:** `sk_live_PASTE_YOUR_KEY_HERE` with your actual OpenAI key

---

#### **OPTION B: Together.ai (Cheaper)**

Go get your free key here: https://api.together.xyz

Then copy & paste:
```powershell
docker run -d -p 7860:7860 `
  -e API_BASE_URL="https://api.together.xyz/v1" `
  -e MODEL_NAME="meta-llama/Llama-2-70b-chat-hf" `
  -e HF_TOKEN="PASTE_YOUR_KEY_HERE" `
  --name cybersim-server `
  cybersim:latest
```

**Replace:** `PASTE_YOUR_KEY_HERE` with your actual Together key

---

#### **OPTION C: Hugging Face Inference**

Go get your token here: https://huggingface.co/settings/tokens

Then copy & paste:
```powershell
docker run -d -p 7860:7860 `
  -e API_BASE_URL="https://api-inference.huggingface.co/v1" `
  -e MODEL_NAME="meta-llama/Llama-2-70b-chat-hf" `
  -e HF_TOKEN="hf_PASTE_YOUR_TOKEN_HERE" `
  --name cybersim-server `
  cybersim:latest
```

**Replace:** `hf_PASTE_YOUR_TOKEN_HERE` with your actual HF token

---

### 4️⃣ Press Enter in PowerShell

You'll see something like:
```
a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6
```

**This means it worked!** ✅

### 5️⃣ Check if Running

```powershell
docker logs cybersim-server
```

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:7860
```

### 6️⃣ Open in Browser

Go to: `http://localhost:7860`

**DONE!** 🎉 Your container is running!

---

## What if it Doesn't Work?

### ❌ "docker: command not found"
→ Docker Desktop is not installed  
→ **Fix:** Download and install Docker Desktop for Windows

### ❌ "Port 7860 is already allocated"
→ Another container is already using port 7860  
→ **Fix:** Run this and try again:
```powershell
docker stop cybersim-server
docker rm cybersim-server
```

### ❌ "image not found: cybersim:latest"
→ Docker image wasn't built yet  
→ **Fix:** First build it:
```powershell
docker build -t cybersim:latest .
```

### ❌ "API key not found" or "401 Unauthorized"
→ Your API key is wrong or invalid  
→ **Fix:** Get a real key from your provider and try again

### ❌ Container starts but errors in logs
Run:
```powershell
docker logs -f cybersim-server
```

This shows you the actual error. Share that error for help!

---

## After it's Running

### View Live Logs (Ongoing Activity)
```powershell
docker logs -f cybersim-server
```

Press `Ctrl+C` to stop watching logs

### Stop the Container
```powershell
docker stop cybersim-server
```

### Remove the Container
```powershell
docker rm cybersim-server
```

### Restart the Container
```powershell
docker restart cybersim-server
```

---

## Access Your Server

### In Browser
- Open: `http://localhost:7860`
- API docs: `http://localhost:7860/docs`

### From Command Line
```powershell
# Test if server is running
curl http://localhost:7860/health

# Should return: {"status":"ok"}
```

---

## What's Running?

Your Docker container is running:
- **FastAPI server** on port 7860
- **Inference script** available to call
- **LLM integration** with your API key
- **All your project files**

Everything needed for the hackathon! ✅

---

## Common Tasks

| Task | Command |
|------|---------|
| **View running containers** | `docker ps` |
| **View all containers** | `docker ps -a` |
| **View logs** | `docker logs cybersim-server` |
| **Follow logs (live)** | `docker logs -f cybersim-server` |
| **Stop container** | `docker stop cybersim-server` |
| **Start container** | `docker start cybersim-server` |
| **Remove container** | `docker rm cybersim-server` |
| **View container resources** | `docker stats cybersim-server` |
| **Enter container shell** | `docker exec -it cybersim-server bash` |

---

## Ready to Deploy?

Once your local container is running perfectly:

1. **Push to GitHub** (already done ✅)
2. **Create HF Space** at https://huggingface.co/spaces
3. **Link to your GitHub repo**
4. **HF will build automatically**
5. **Submit to hackathon**

**That's it!** 🚀
