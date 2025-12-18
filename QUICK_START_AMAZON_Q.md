# Quick Start: Switch to Amazon Q

## 🚀 3-Minute Setup

### Step 1: Get Your Amazon Q Credentials

1. **AWS Console:** https://console.aws.amazon.com/
2. **Navigate to:** Amazon Q Business
3. **Create Application** (if you don't have one)
4. **Copy:** Application ID

### Step 2: Get AWS Access Keys

1. **IAM Console:** https://console.aws.amazon.com/iam/
2. **Users** → Your User → **Security Credentials**
3. **Create Access Key** → Copy both:
   - Access Key ID
   - Secret Access Key

### Step 3: Update .env File

Open `.env` and update:

```env
# Switch to Amazon Q
AI_PROVIDER=amazon_q

# Add your credentials
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
AMAZON_Q_APP_ID=your-app-id-here
```

### Step 4: Restart Flask

```bash
# Stop current app (Ctrl+C)
python app.py
```

### Step 5: Test

Visit: http://localhost:5000

Try an estimation - you should see:
```
DEBUG - Using Amazon Q for estimation
DEBUG - Calling Amazon Q for estimation...
```

---

## ✅ Benefits You'll See

### 1. Codebase-Aware Estimates
Amazon Q understands YOUR code:
- Your tech stack
- Your dependencies
- Your patterns

### 2. Better Accuracy
Learns from:
- Your JIRA history
- Your team's velocity
- Your actual time spent

### 3. Cost-Effective
- $20/user/month flat rate
- Unlimited API calls
- No per-token charges

---

## 🔄 Fallback System

Don't worry! If Amazon Q fails, the system automatically:
1. Tries Azure OpenAI (if configured)
2. Falls back to rule-based estimation
3. Never fails completely

---

## 🎯 What Amazon Q Sees

When you estimate a JIRA ticket, Amazon Q receives:

```
Task: Add user authentication with OAuth2
JIRA: PROJ-123 (Story, High Priority)
Status History: 
  - Backlog → Analysis (16h)
  - Analysis → In Progress (48h)
Linked Issues: 3 dependencies
Tech Stack: React Native, TypeScript, Redux
```

Amazon Q then provides:
- Realistic hours based on YOUR codebase
- Risk factors specific to YOUR tech stack
- Confidence based on YOUR historical data

---

## 📊 Compare Results

Want to see the difference? Keep both configured:

```env
AI_PROVIDER=amazon_q  # Primary

# Keep Azure as comparison
AZURE_OPENAI_ENDPOINT=...
AZURE_OPENAI_API_KEY=...
```

Then check console logs to see both estimates!

---

## 🆘 Troubleshooting

### "AccessDeniedException"
**Fix:** Add IAM permissions:
```json
{
  "Effect": "Allow",
  "Action": ["qbusiness:ChatSync"],
  "Resource": "*"
}
```

### "ApplicationNotFoundException"
**Fix:** Double-check your `AMAZON_Q_APP_ID`

### Amazon Q not responding
**Fix:** System automatically falls back to Azure OpenAI

---

## 📚 Full Documentation

See `AMAZON_Q_SETUP.md` for:
- Detailed setup instructions
- IAM policy templates
- Advanced configuration
- Security best practices
- Cost analysis

---

## 🎉 You're Ready!

Amazon Q will now provide **codebase-aware, team-specific estimates** that improve over time!

**Questions?** Check the full guide: `AMAZON_Q_SETUP.md`
