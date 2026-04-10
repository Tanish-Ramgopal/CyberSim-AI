# How to Run Docker Container as Server - Step by Step

## What This Command Does

```bash
docker run -d -p 7860:7860 \
  -e API_BASE_URL="https://api.openai.com/v1" \
  -e MODEL_NAME="gpt-4o-mini" \
  -e HF_TOKEN="sk_..." \
  --name cybersim-server \
  cybersim:latest
```

**Breaking it down:**

| Part | Meaning |
|------|---------|
| `docker run` | Start a new container |
| `-d` | Run in background (detached mode) |
| `-p 7860:7860` | Forward port 7860 from container to your computer |
| `-e API_BASE_URL="..."` | Set environment variable for API endpoint |
| `-e MODEL_NAME="..."` | Set environment variable for model name |
| `-e HF_TOKEN="..."` | Set environment variable for API key |
| `--name cybersim-server` | Give the container a name (optional but useful) |
| `cybersim:latest` | Use the image you built |

---

## Step-by-Step Instructions

### **Step 1: Get Your API Key**

You need an actual API key (not `sk_...`):

**Option 1: OpenAI API Key**
1. Go to https://platform.openai.com/api-keys
2. Create new API key
3. Copy the key (looks like: `sk_live_...` or `sk_test_...`)

**Option 2: Together.ai API Key (Cheaper)**
1. Go to https://api.together.xyz
2. Create free account
3. Get API key

**Option 3: Hugging Face Token**
1. Go to https://huggingface.co/settings/tokens
2. Create read token
3. Copy token

### **Step 2: Open PowerShell or Command Prompt**

On your Windows machine, open:
- **PowerShell** (recommended)
- OR **Command Prompt (cmd)**

### **Step 3: Navigate to Your Project**

```bash
cd "C:\Users\Tanish Ramgopal\Documents\Tanish\Meta Hackathon 2026"
```

### **Step 4: Run the Docker Command**

**Example 1: With OpenAI API Key**

```bash
docker run -d -p 7860:7860 `
  -e API_BASE_URL="https://api.openai.com/v1" `
  -e MODEL_NAME="gpt-4o-mini" `
  -e HF_TOKEN="sk_live_1234567890abcdef" `
  --name cybersim-server `
  cybersim:latest
```

**Replace:** `sk_live_1234567890abcdef` with your actual API key

---

**Example 2: With Together.ai API Key**

```bash
docker run -d -p 7860:7860 `
  -e API_BASE_URL="https://api.together.xyz/v1" `
  -e MODEL_NAME="meta-llama/Llama-2-70b-chat-hf" `
  -e HF_TOKEN="abc123xyz789" `
  --name cybersim-server `
  cybersim:latest
```

**Replace:** `abc123xyz789` with your actual API key

---

**Example 3: With Hugging Face Inference API**

```bash
docker run -d -p 7860:7860 `
  -e API_BASE_URL="https://api-inference.huggingface.co/v1" `
  -e MODEL_NAME="meta-llama/Llama-2-70b-chat-hf" `
  -e HF_TOKEN="hf_abc123xyz789" `
  --name cybersim-server `
  cybersim:latest
```

**Replace:** `hf_abc123xyz789` with your actual HF token

---

### **Step 5: Verify Container Started**

After running the command, you should see something like:

```
a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6
```

This is the container ID. If you see this, the container started successfully! ✅

### **Step 6: View the Logs**

Wait 5 seconds, then run:

```bash
docker logs cybersim-server
```

**Expected output:**
```
INFO:     Uvicorn running on http://0.0.0.0:7860
```

OR if there's an error, you'll see it here.

---

## Common Issues & Fixes

### ❌ Error: "docker: command not found"
**Solution:** Docker Desktop is not installed or not in PATH
- Install Docker Desktop for Windows
- Restart PowerShell/CMD

### ❌ Error: "Port 7860 is already allocated"
**Solution:** Another container is using port 7860
```bash
# Kill the existing container
docker stop cybersim-server
docker rm cybersim-server

# Then run the new one
docker run -d -p 7860:7860 ... cybersim:latest
```

### ❌ Error: "image not found: cybersim:latest"
**Solution:** Image wasn't built yet
```bash
# Build it first
docker build -t cybersim:latest .
```

### ❌ Error: "API key invalid"
**Solution:** You used `sk_...` instead of actual key
- Get real API key from your provider
- Replace in command with actual value

---

## After Container Starts

### Check if it's Running
```bash
docker ps
```

You should see `cybersim-server` in the list.

### View Live Logs
```bash
docker logs -f cybersim-server
```

(Press Ctrl+C to stop viewing logs)

### Access the Server

Open browser and go to:
```
http://localhost:7860
```

You should see the FastAPI server interface.

### Run Inference from Browser

1. Go to `http://localhost:7860/docs` (Swagger UI)
2. Call endpoints through web interface

### Run Inference from Command Line

```bash
curl -X GET "http://localhost:7860/health"
```

Should return: `{"status":"ok"}`

---

## Stop the Container

### Stop Running Container
```bash
docker stop cybersim-server
```

### Remove Container (if no longer needed)
```bash
docker rm cybersim-server
```

### Stop All Containers
```bash
docker stop $(docker ps -q)
```

---

## Quick Copy-Paste Examples

### With OpenAI (Copy & Paste)
```powershell
docker run -d -p 7860:7860 `
  -e API_BASE_URL="https://api.openai.com/v1" `
  -e MODEL_NAME="gpt-4o-mini" `
  -e HF_TOKEN="YOUR_OPENAI_KEY_HERE" `
  --name cybersim-server `
  cybersim:latest
```

### With Together.ai (Copy & Paste)
```powershell
docker run -d -p 7860:7860 `
  -e API_BASE_URL="https://api.together.xyz/v1" `
  -e MODEL_NAME="meta-llama/Llama-2-70b-chat-hf" `
  -e HF_TOKEN="YOUR_TOGETHER_KEY_HERE" `
  --name cybersim-server `
  cybersim:latest
```

### With HF Inference (Copy & Paste)
```powershell
docker run -d -p 7860:7860 `
  -e API_BASE_URL="https://api-inference.huggingface.co/v1" `
  -e MODEL_NAME="meta-llama/Llama-2-70b-chat-hf" `
  -e HF_TOKEN="hf_YOUR_HF_TOKEN_HERE" `
  --name cybersim-server `
  cybersim:latest
```

---

## Useful Docker Commands

```bash
# List running containers
docker ps

# List all containers (including stopped)
docker ps -a

# View container logs
docker logs cybersim-server

# Follow logs (live)
docker logs -f cybersim-server

# Stop container
docker stop cybersim-server

# Start stopped container
docker start cybersim-server

# Remove container
docker rm cybersim-server

# Execute command in running container
docker exec cybersim-server python pre_submission_checklist.py

# Interactive shell in container
docker exec -it cybersim-server bash

# View container stats (CPU, memory)
docker stats cybersim-server

# Restart container
docker restart cybersim-server
```

---

## Real Example (Step by Step)

Let's say you have an OpenAI API key: `sk_live_abc123xyz`

### Step 1: Open PowerShell
Windows PowerShell → Click to open

### Step 2: Navigate to project
```powershell
cd "C:\Users\Tanish Ramgopal\Documents\Tanish\Meta Hackathon 2026"
```

### Step 3: Run the container
```powershell
docker run -d -p 7860:7860 `
  -e API_BASE_URL="https://api.openai.com/v1" `
  -e MODEL_NAME="gpt-4o-mini" `
  -e HF_TOKEN="sk_live_abc123xyz" `
  --name cybersim-server `
  cybersim:latest
```

### Step 4: You should see container ID
```
a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6
```

### Step 5: Check logs
```powershell
docker logs cybersim-server
```

### Step 6: You should see
```
INFO:     Uvicorn running on http://0.0.0.0:7860
```

### Step 7: Open browser
Go to: `http://localhost:7860`

**DONE!** ✅ Your container is running!

---

## Troubleshooting Checklist

- [ ] Docker Desktop installed and running?
- [ ] Container image `cybersim:latest` exists? (`docker images | findstr cybersim`)
- [ ] Valid API key (not `sk_...` placeholder)?
- [ ] Port 7860 not already in use?
- [ ] PowerShell/CMD running as admin?
- [ ] Internet connection working?

If all yes → Container should start! 🎉
