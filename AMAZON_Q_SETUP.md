# Amazon Q Developer Integration Guide

## Why Amazon Q?

Amazon Q Developer provides **codebase-aware estimates** by:
- Understanding your actual code structure
- Learning from your development patterns
- Analyzing your tech stack and dependencies
- Providing context-specific recommendations

This leads to more accurate estimates compared to generic AI models.

---

## Setup Steps

### 1. Get Amazon Q Credentials

#### Option A: AWS Console
1. Go to [AWS Console](https://console.aws.amazon.com/)
2. Navigate to **Amazon Q Business**
3. Create or select an application
4. Note your **Application ID**
5. Create IAM credentials with Q Business permissions

#### Option B: AWS CLI
```bash
# Install AWS CLI
pip install awscli

# Configure credentials
aws configure
# Enter your AWS Access Key ID
# Enter your AWS Secret Access Key
# Enter your region (e.g., us-east-1)
```

### 2. Create Amazon Q Application

```bash
# Create Q Business application
aws qbusiness create-application \
    --display-name "Esti-Mate Estimator" \
    --description "AI-powered project estimation" \
    --region us-east-1

# Note the applicationId from the response
```

### 3. Configure IAM Permissions

Create an IAM policy with these permissions:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "qbusiness:ChatSync",
                "qbusiness:GetApplication",
                "qbusiness:ListConversations"
            ],
            "Resource": "*"
        }
    ]
}
```

Attach this policy to your IAM user or role.

### 4. Update .env File

```env
# AI Provider Selection
AI_PROVIDER=amazon_q

# Amazon Q Developer Configuration
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your_access_key_here
AWS_SECRET_ACCESS_KEY=your_secret_key_here
AMAZON_Q_APP_ID=your_app_id_here
```

### 5. Install Dependencies

```bash
pip install boto3 botocore
```

### 6. Test Connection

```bash
python -c "import boto3; client = boto3.client('qbusiness', region_name='us-east-1'); print('Amazon Q connected!')"
```

---

## Configuration Options

### Switch Between Providers

**Use Amazon Q:**
```env
AI_PROVIDER=amazon_q
```

**Use Azure OpenAI:**
```env
AI_PROVIDER=azure_openai
```

### Hybrid Approach

You can keep both configured and switch as needed:

```env
# Azure OpenAI (Fallback)
AZURE_OPENAI_ENDPOINT=https://your-endpoint.openai.azure.com/
AZURE_OPENAI_API_KEY=your-azure-key

# Amazon Q (Primary)
AI_PROVIDER=amazon_q
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AMAZON_Q_APP_ID=your_app_id
```

The system will:
1. Try Amazon Q first
2. Fall back to Azure OpenAI if Q fails
3. Use rule-based estimation if both fail

---

## Amazon Q Features for Estimation

### 1. Codebase Context

Amazon Q can analyze your repository:

```python
# In your code
codebase_context = """
Tech Stack: React Native 0.76, TypeScript, Redux
Dependencies: 150+ npm packages
Architecture: Microservices with REST APIs
Testing: Jest, React Testing Library
"""

estimation = ai_estimator.estimate_with_ai(
    description="Add user authentication",
    jira_data=jira_data,
    codebase_context=codebase_context
)
```

### 2. Historical Learning

Amazon Q learns from your team's patterns:
- Average time for similar features
- Common blockers and delays
- Team velocity and capacity

### 3. Tech Stack Awareness

Q understands your specific technologies:
- React Native version-specific issues
- iOS/Android platform differences
- Third-party library compatibility

---

## Cost Comparison

### Azure OpenAI (GPT-5)
- ~$0.03 per 1K tokens
- ~$0.06 per 1K output tokens
- Estimated: $0.10-0.20 per estimation

### Amazon Q Business
- $20/user/month (flat rate)
- Unlimited API calls
- Better for high-volume usage

**Recommendation:** If you're making 100+ estimations/month, Amazon Q is more cost-effective.

---

## Troubleshooting

### Error: "AccessDeniedException"
**Solution:** Check IAM permissions. Ensure your user has `qbusiness:ChatSync` permission.

### Error: "ApplicationNotFoundException"
**Solution:** Verify your `AMAZON_Q_APP_ID` is correct.

### Error: "InvalidRegionException"
**Solution:** Amazon Q is available in specific regions. Try `us-east-1` or `us-west-2`.

### Amazon Q returns no results
**Solution:** System automatically falls back to Azure OpenAI or rule-based estimation.

---

## Best Practices

### 1. Provide Codebase Context

Always include relevant codebase information:
```python
context = f"""
Repository: {repo_name}
Tech Stack: {tech_stack}
Team Size: {team_size}
Sprint Length: {sprint_length}
"""
```

### 2. Use JIRA Historical Data

Amazon Q learns better with historical data:
- Status transitions
- Time tracking
- Linked issues
- Comments and discussions

### 3. Regular Updates

Update your Amazon Q application with:
- New dependencies
- Architecture changes
- Team velocity metrics

### 4. Monitor Accuracy

Track estimation accuracy:
```bash
# View learning dashboard
http://localhost:5000/learning-dashboard
```

---

## Security Considerations

### 1. Credential Management

**Never commit credentials to Git:**
```bash
# Add to .gitignore
.env
*.pem
*.key
```

### 2. Use IAM Roles (Recommended)

For production, use IAM roles instead of access keys:
```python
# No credentials needed - uses instance role
client = boto3.client('qbusiness', region_name='us-east-1')
```

### 3. Rotate Keys Regularly

```bash
# Rotate access keys every 90 days
aws iam create-access-key --user-name your-user
aws iam delete-access-key --access-key-id OLD_KEY --user-name your-user
```

---

## Advanced Configuration

### Custom Prompts

Customize estimation prompts for your domain:

```python
# In amazon_q_estimator.py
context += """
**Company-Specific Guidelines:**
- All features require security review: +8 hours
- Code review process: +4 hours
- Documentation requirements: +2 hours per feature
"""
```

### Integration with CI/CD

Trigger estimations automatically:

```bash
# In your CI pipeline
python estimate_from_pr.py --pr-number 123
```

### Slack Integration

Get estimates in Slack:

```python
# slack_bot.py
@app.command("/estimate")
def estimate_command(ack, command):
    jira_ticket = command['text']
    estimation = ai_estimator.estimate_with_ai(jira_ticket)
    ack(f"Estimated: {estimation['total_hours']} hours")
```

---

## Migration from Azure OpenAI

### Step 1: Keep Both Configured
```env
AI_PROVIDER=amazon_q  # Switch to Q
# Keep Azure as fallback
AZURE_OPENAI_ENDPOINT=...
AZURE_OPENAI_API_KEY=...
```

### Step 2: Test in Parallel

Run estimations with both:
```python
# Compare results
azure_estimate = ai_estimator.estimate_with_ai(desc, provider='azure')
q_estimate = ai_estimator.estimate_with_ai(desc, provider='amazon_q')
```

### Step 3: Gradual Rollout

- Week 1: 10% of estimates use Amazon Q
- Week 2: 50% use Amazon Q
- Week 3: 100% use Amazon Q

---

## Support

### AWS Support
- [Amazon Q Documentation](https://docs.aws.amazon.com/amazonq/)
- [AWS Support Center](https://console.aws.amazon.com/support/)

### Community
- GitHub Issues: [Esti-Mate Issues](https://github.com/rithik1007/Esti-Mate/issues)
- AWS Forums: [Amazon Q Forum](https://repost.aws/tags/TAl-R3_6aTQqKKKxC_D_Ew5g/amazon-q)

---

## Summary

✅ **Amazon Q Advantages:**
- Codebase-aware estimates
- Learns from your team's patterns
- Better for high-volume usage
- Flat-rate pricing

✅ **Setup Time:** ~15 minutes

✅ **Cost:** $20/user/month (unlimited API calls)

✅ **Fallback:** Automatically uses Azure OpenAI if Q fails

**Ready to switch?** Update your `.env` file and restart the app!
