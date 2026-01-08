# Quick Fix: Virtual Environment Issue

## Problem
Your `.venv` was pointing to an old path (`/Users/gabdomingo/Documents/apify-scraper/.venv`), causing the "externally-managed-environment" error.

## Solution

I've recreated your virtual environment. Now do this:

### 1. Activate the Virtual Environment

```bash
source .venv/bin/activate
```

You should see `(.venv)` in your prompt.

### 2. Install Dependencies

**Use `pip` (not `pip3`)** when in the venv:

```bash
pip install -r requirements.txt
```

### 3. Verify Installation

```bash
pip list | grep fastapi
```

Should show `fastapi` installed.

### 4. Start the Server

```bash
uvicorn app:app --reload
```

## Why This Happened

- `pip3` points to system Python (even in venv)
- `pip` points to venv Python (correct)
- Your old `.venv` had broken paths

## Always Use

- ✅ `pip` (not `pip3`) when in venv
- ✅ `python` (not `python3`) when in venv
- ✅ Make sure `(.venv)` shows in your prompt
