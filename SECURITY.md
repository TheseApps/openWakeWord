# Security Guidelines for openWakeWord

## 🔐 API Key Management

### Never Hardcode Keys!

This project uses a secure secrets management system. **NEVER** put API keys directly in code.

### How to Add Your API Keys

1. **Open the `.secrets` file** in the project root
2. **Add your keys** in the format:
   ```
   PICOVOICE_ACCESS_KEY=your_actual_key_here
   SERVICE_NAME_KEY=another_key_here
   ```
3. **Save the file** - it's automatically ignored by Git

### Using Keys in Code

```python
# ✅ CORRECT - Secure pattern
from utils.secrets import get_required_secret
api_key = get_required_secret("SERVICE_NAME_KEY")

# ❌ WRONG - Never do this!
api_key = "sk-abc123def456..."  # EXPOSED IN CODE!
```

### Available Keys

| Key Name | Service | Where to Get |
|----------|---------|--------------|
| `PICOVOICE_ACCESS_KEY` | Picovoice Wake Words | https://console.picovoice.ai/ |
| `OPENAI_API_KEY` | OpenAI GPT | https://platform.openai.com/ |
| `GOOGLE_API_KEY` | Google Cloud | https://console.cloud.google.com/ |

### Security Checklist

- [ ] `.secrets` file exists
- [ ] `.secrets` is in `.gitignore`
- [ ] No keys in code files
- [ ] All scripts use `utils.secrets`
- [ ] Clear error messages for missing keys

## 🛡️ Additional Security Rules

### Audio Privacy
- Audio recordings in `saved_clips/` contain voice data
- Don't commit audio files to Git
- Get consent before recording

### Web Security
- Always validate WebSocket inputs
- Use HTTPS in production
- Sanitize filenames from uploads

### Key Rotation
- Change API keys every 90 days
- Update `.secrets` file when keys change
- Never share your `.secrets` file

## 🚨 If You Accidentally Commit a Key

1. **Immediately revoke the key** in the service's console
2. **Remove from Git history**:
   ```bash
   git filter-branch --force --index-filter \
     "git rm --cached --ignore-unmatch .secrets" \
     --prune-empty --tag-name-filter cat -- --all
   ```
3. **Force push** to remote (coordinate with team)
4. **Generate new keys** and update `.secrets`

## 📝 Cursor IDE Integration

The `.cursorrules` file enforces these security patterns:
- Cursor will remind you to use secure patterns
- It won't suggest hardcoded keys
- It will guide you to use `utils.secrets`

## 🔍 Quick Security Audit

Run this to check for exposed keys:
```bash
# Search for potential keys in code
grep -r "api_key\|access_key\|secret" --include="*.py" --exclude-dir=".venv*"

# Verify .secrets is ignored
git check-ignore .secrets
```

---

**Remember**: Security is everyone's responsibility. When in doubt, ask!
