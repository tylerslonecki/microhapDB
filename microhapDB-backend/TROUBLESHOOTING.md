# Troubleshooting Guide for ORCID Authentication

## Common Issues and Solutions

### ERR_NGROK_3200: The endpoint is offline

This error occurs when your ngrok tunnel is not running or is misconfigured.

**Solutions:**

1. **Check if ngrok is running**:
   ```bash
   curl -s --head http://localhost:4040
   ```
   If this fails, ngrok isn't running. Start it with:
   ```bash
   ngrok http 8000
   ```

2. **Get the correct ngrok URL**:
   When ngrok starts, it displays a URL like `https://abcd1234.ngrok-free.app`. Use this URL in your configuration:
   - Update `.env` with `ORCID_REDIRECT_URI=https://abcd1234.ngrok-free.app/auth/callback`
   - Update frontend with `VUE_APP_BACKEND_URL=https://abcd1234.ngrok-free.app`

3. **Restart the application**:
   Once ngrok is running and you've updated the URLs, restart both the backend and frontend.

### ORCID Authentication Errors

If you're having trouble with ORCID authentication:

1. **Check ORCID Sandbox Application Configuration**:
   - Go to https://sandbox.orcid.org/developer-tools
   - Ensure your application's Website URL and Redirect URI exactly match your ngrok URL
   - Client ID and Client Secret are correctly set in your `.env` file

2. **Verify Environment Variables**:
   Make sure these variables are correctly set in `microhapDB-backend/src/.env`:
   ```
   ORCID_CLIENT_ID=your-sandbox-client-id
   ORCID_CLIENT_SECRET=your-sandbox-client-secret
   ORCID_REDIRECT_URI=https://your-ngrok-url.ngrok-free.app/auth/callback
   ORCID_AUTH_URL=https://sandbox.orcid.org/oauth/authorize
   ORCID_TOKEN_URL=https://sandbox.orcid.org/oauth/token
   ORCID_API_URL=https://sandbox.orcid.org/v3.0
   ```

3. **Check Backend Logs**:
   Look for errors in the FastAPI logs related to ORCID token exchange or user info retrieval.

4. **Check Browser Console**:
   Open your browser's developer tools and check the console for any errors during the authentication process.

### Developing Without ngrok

If you want to develop without ngrok (for basic testing):

1. Run the startup script with the `--local` flag:
   ```bash
   ./start_local_dev.sh --local
   ```

2. Or manually update your configuration:
   ```
   # In src/.env
   ORCID_REDIRECT_URI=http://localhost:8000/auth/callback
   
   # In frontend/.env.development.local
   VUE_APP_BACKEND_URL=http://localhost:8000
   ```

Note that ORCID won't accept localhost URLs in production, but this setup works for basic local development without authentication.

## Advanced Debugging

### Test API Endpoints Directly

You can test the ORCID API endpoints directly to verify credentials:

```bash
# Test token URL
curl -X POST -d "client_id=YOUR_CLIENT_ID&client_secret=YOUR_CLIENT_SECRET&grant_type=client_credentials&scope=/read-public" -H "Accept: application/json" https://sandbox.orcid.org/oauth/token
```

### Inspect Cookies

Authentication issues can sometimes be caused by cookie problems:

1. Open browser developer tools
2. Go to the Application/Storage tab
3. Check if the `access_token` cookie is being set after authentication
4. Verify the cookie domain and path are correct

### Check CORS Issues

If you're having CORS problems:

1. Open browser developer tools
2. Look for CORS errors in the console
3. Verify the backend CORS configuration includes your frontend URL 