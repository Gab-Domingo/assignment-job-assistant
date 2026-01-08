# 🚀 Start Here - Quick Guide

## The Problem You Had

You were running `uvicorn` **outside** the virtual environment, so Python couldn't find `google.genai`.

## ✅ Solution: Always Activate Venv First

### Option 1: Use the Start Script (Easiest)

```bash
./start_server.sh
```

### Option 2: Manual Activation

**In your terminal, run these commands:**

```bash
# 1. Navigate to project
cd /Users/gabdomingo/Documents/job-assistant

# 2. Activate virtual environment
source .venv/bin/activate

# You should see (.venv) in your prompt now!

# 3. Start server
uvicorn app:app --reload
```

## ✅ Verify It's Working

1. **Check your prompt** - Should show `(.venv)`
2. **Check which Python** - Run `which python` (should point to `.venv/bin/python`)
3. **Server should start** - You'll see:
   ```
   INFO:     Uvicorn running on http://127.0.0.1:8000
   ```

## 🧪 Test the API

Once server is running:
- Open: http://localhost:8000/docs
- Test endpoints in the browser!

## ⚠️ Common Mistakes

❌ **Don't do this:**
```bash
uvicorn app:app --reload  # Without activating venv first
```

✅ **Do this:**
```bash
source .venv/bin/activate  # Activate first!
uvicorn app:app --reload
```

## 💡 Pro Tip

Add this to your `~/.zshrc` or `~/.bashrc` to auto-activate:
```bash
# Auto-activate venv when entering directory
cd() {
    builtin cd "$@"
    if [[ -f .venv/bin/activate ]]; then
        source .venv/bin/activate
    fi
}
```
