# GitHub Secrets Configuration

To enable CI/CD, you need to configure the following secrets in your GitHub repository settings.

## Required Secrets

Go to your repository on GitHub → Settings → Secrets and variables → Actions → New repository secret

### 1. **SERVER_HOST**
- Value: `155.138.211.71`
- Description: Your Vultr server IP address

### 2. **SERVER_USER**
- Value: `root` (or your SSH username)
- Description: SSH username for server access

### 3. **SERVER_PORT**
- Value: `22` (or your custom SSH port)
- Description: SSH port number

### 4. **SERVER_SSH_KEY**
- Value: Your private SSH key (entire content including headers)
- Description: Private key for SSH authentication
- How to get it:
  ```bash
  cat ~/.ssh/id_rsa  # or your key file
  ```
- Format:
  ```
  -----BEGIN RSA PRIVATE KEY-----
  [your key content]
  -----END RSA PRIVATE KEY-----
  ```

### 5. **SLACK_WEBHOOK** (Optional)
- Value: Your Slack webhook URL
- Description: For deployment notifications
- Get from: https://slack.com/apps/A0F7XDUAZ-incoming-webhooks

## How to Add Secrets

1. Go to: `https://github.com/[your-username]/[your-repo]/settings/secrets/actions`
2. Click "New repository secret"
3. Enter the secret name (exactly as shown above)
4. Paste the secret value
5. Click "Add secret"

## Security Notes

- Never commit secrets to your repository
- GitHub secrets are encrypted and only exposed to workflows
- Use deploy keys or machine users for production
- Rotate SSH keys periodically

## Testing the Workflow

After adding all secrets:

1. Make a small change to your code
2. Commit and push to main branch
3. Check Actions tab in GitHub to see the deployment progress

## Manual Deployment

You can also trigger deployment manually:
1. Go to Actions tab
2. Select "Deploy to Production" workflow
3. Click "Run workflow" → "Run workflow"