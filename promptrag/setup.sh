#!/bin/bash
# setup.sh

echo "🚀 Setting up Prompt Engineering Academy..."

# Create directory structure
mkdir -p logs uploads static

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Copy environment template
if [ ! -f .env ]; then
    cp .env.example .env
    echo "⚠️  Please update .env file with your configuration"
fi

# Create MongoDB data directory
mkdir -p data/db

echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env file with your configuration"
echo "2. Start MongoDB: docker-compose up -d mongodb"
echo "3. Run the app: python main.py"
echo "4. Or use: docker-compose up --build"
