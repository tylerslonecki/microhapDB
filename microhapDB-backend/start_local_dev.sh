#!/bin/bash
# Script to start the local development environment with or without ngrok

# Check if --local flag is passed
LOCAL_MODE=false
for arg in "$@"; do
  if [ "$arg" == "--local" ]; then
    LOCAL_MODE=true
  fi
done

# Function to set up local development without ngrok
setup_local_dev() {
    echo "🔧 Setting up local development mode without ngrok..."
    
    if grep -q "ORCID_REDIRECT_URI=" src/.env; then
        sed -i '' "s|ORCID_REDIRECT_URI=.*|ORCID_REDIRECT_URI=http://localhost:8000/auth/callback|g" src/.env
    else
        echo "ORCID_REDIRECT_URI=http://localhost:8000/auth/callback" >> src/.env
    fi
    
    # Update frontend to use localhost
    cat > ../microhapDB-frontend/.env.development.local << EOL
VUE_APP_BACKEND_URL=http://localhost:8000
EOL

    echo "✅ Using localhost for development"
}

# If local mode is requested, set up for local development
if [ "$LOCAL_MODE" = true ]; then
    setup_local_dev
    echo "🚀 Starting FastAPI server in local mode..."
    uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
    exit 0
fi

# Check if ngrok is running
if ! curl -s --head http://localhost:4040 > /dev/null; then
    echo "⚠️  Ngrok is not running. Starting local development without ngrok..."
    echo "ℹ️  If you want to use ngrok, open a new terminal and run: ngrok http 8000"
    
    setup_local_dev
    
    echo "🚀 Starting FastAPI server..."
    uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
    exit 0
fi

# Try different patterns for ngrok URLs
echo "🔍 Detecting ngrok URL..."
NGROK_URL=$(curl -s http://localhost:4040/api/tunnels | grep -o "https://[a-zA-Z0-9.-]*\.ngrok-free\.app" || curl -s http://localhost:4040/api/tunnels | grep -o "https://[a-zA-Z0-9.-]*\.ngrok\.io")

if [ -z "$NGROK_URL" ]; then
    echo "⚠️  Could not detect ngrok URL format automatically."
    echo "Please enter your ngrok URL (e.g., https://abcd1234.ngrok-free.app):"
    read NGROK_URL
    
    if [ -z "$NGROK_URL" ]; then
        echo "❌ No URL provided. Using localhost instead."
        setup_local_dev
        echo "🚀 Starting FastAPI server..."
        uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
        exit 0
    fi
fi

echo "✅ Using ngrok URL: $NGROK_URL"

# Update .env file with the ngrok URL
echo "📝 Updating .env file with ngrok URL..."
if grep -q "ORCID_REDIRECT_URI=" src/.env; then
    sed -i '' "s|ORCID_REDIRECT_URI=.*|ORCID_REDIRECT_URI=${NGROK_URL}/auth/callback|g" src/.env
else
    echo "ORCID_REDIRECT_URI=${NGROK_URL}/auth/callback" >> src/.env
fi

# Update frontend config
echo "📝 Updating frontend environment file..."
cat > ../microhapDB-frontend/.env.development.local << EOL
VUE_APP_BACKEND_URL=${NGROK_URL}
EOL

echo "🔧 Don't forget to update your ORCID application settings with:"
echo "    - Website URL: ${NGROK_URL}"
echo "    - Redirect URI: ${NGROK_URL}/auth/callback"

echo "🚀 Starting FastAPI server..."
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000 