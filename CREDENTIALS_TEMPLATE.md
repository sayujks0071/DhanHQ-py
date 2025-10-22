# 🔐 AI Trading Bot Credentials Setup

## Required Credentials

You need to edit the `.env` file with your actual credentials. Here's what you need:

### 1. DhanHQ Credentials
- **DHAN_CLIENT_ID**: Your DhanHQ client ID
- **DHAN_ACCESS_TOKEN**: Your DhanHQ access token

### 2. Google AI Studio Credentials  
- **AI_STUDIO_API_KEY**: Your Google AI Studio API key

## How to Edit the .env File

### Option 1: Using a Text Editor
```bash
# Open the .env file in your preferred editor
code .env          # VS Code
vim .env           # Vim
nano .env          # Nano
```

### Option 2: Using Command Line
```bash
# Replace the placeholder values with your actual credentials
sed -i '' 's/your_client_id_here/YOUR_ACTUAL_CLIENT_ID/g' .env
sed -i '' 's/your_access_token_here/YOUR_ACTUAL_ACCESS_TOKEN/g' .env
sed -i '' 's/your_ai_studio_api_key_here/YOUR_ACTUAL_AI_API_KEY/g' .env
```

### Option 3: Manual Edit
Open `.env` file and replace these lines:

```bash
# Change this:
DHAN_CLIENT_ID=your_client_id_here
DHAN_ACCESS_TOKEN=your_access_token_here
AI_STUDIO_API_KEY=your_ai_studio_api_key_here

# To this (with your actual values):
DHAN_CLIENT_ID=your_actual_client_id
DHAN_ACCESS_TOKEN=your_actual_access_token
AI_STUDIO_API_KEY=your_actual_ai_studio_api_key
```

## Where to Get Your Credentials

### DhanHQ Credentials
1. Go to [DhanHQ Developer Portal](https://api.dhan.co/v2/)
2. Sign up/Login to your account
3. Generate your Client ID and Access Token
4. Copy the credentials to your .env file

### Google AI Studio API Key
1. Go to [Google AI Studio](https://aistudio.google.com/)
2. Sign in with your Google account
3. Create a new API key
4. Copy the API key to your .env file

## Test Your Credentials

After updating your credentials, test them:

```bash
python configure_credentials.py test
```

## Security Notes

- Never commit the .env file to version control
- Keep your credentials secure and private
- The .env file has been set to secure permissions (600)
- Consider using environment variables in production

## Next Steps

Once your credentials are configured:

1. **Test the setup:**
   ```bash
   python configure_credentials.py test
   ```

2. **Run the AI trading bot:**
   ```bash
   python run_ai_trading.py
   ```

3. **For production deployment:**
   ```bash
   docker-compose up -d
   ```

