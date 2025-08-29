#!/bin/bash
# Setup Backend Database and API for Portal-Anwalts.AI

echo "🔧 Setting up Backend Database and API..."

# Step 1: Setup PostgreSQL Database
echo "📊 Creating PostgreSQL database and user..."
su - postgres -c "createdb anwalts_ai_prod" 2>/dev/null || echo "Database may already exist"
su - postgres -c "createuser anwalts_user" 2>/dev/null || echo "User may already exist"
su - postgres -c "psql -c \"ALTER USER anwalts_user WITH PASSWORD 'secure_password';\""
su - postgres -c "psql -c \"GRANT ALL PRIVILEGES ON DATABASE anwalts_ai_prod TO anwalts_user;\""

echo "✅ Database setup complete"

# Step 2: Install Python dependencies
echo "🐍 Installing Python dependencies..."
cd /var/www/portal-anwalts.ai/backend
pip3 install fastapi uvicorn pydantic sqlalchemy psycopg2-binary python-jose passlib python-multipart httpx python-dotenv

echo "✅ Dependencies installed"

# Step 3: Create environment file if missing
echo "⚙️ Setting up environment..."
if [ ! -f .env ]; then
    cat > .env << 'EOF'
DATABASE_URL=postgresql://anwalts_user:secure_password@localhost/anwalts_ai_prod
TOGETHER_API_KEY=your_together_api_key_here
JWT_SECRET_KEY=super_secret_jwt_key_change_in_production
ENVIRONMENT=production
EOF
    echo "✅ Environment file created"
else
    echo "✅ Environment file already exists"
fi

# Step 4: Initialize database tables
echo "🗄️ Creating database tables..."
python3 -c "
from database import init_db
try:
    init_db()
    print('✅ Database tables created successfully')
except Exception as e:
    print(f'⚠️ Database init: {e}')
    print('Continuing anyway...')
"

# Step 5: Create systemd service for backend
echo "⚙️ Creating backend service..."
cat > /etc/systemd/system/anwalts-api.service << 'EOF'
[Unit]
Description=AnwaltsAI API Server
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/var/www/portal-anwalts.ai/backend
Environment=PATH=/usr/local/bin
ExecStart=/usr/bin/python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 --workers 1
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

# Step 6: Start the backend service
echo "🚀 Starting backend API service..."
systemctl daemon-reload
systemctl enable anwalts-api
systemctl start anwalts-api

# Wait a moment for service to start
sleep 3

# Step 7: Test the setup
echo "🧪 Testing setup..."
echo "Backend service status:"
systemctl status anwalts-api --no-pager -l

echo ""
echo "Testing API health:"
curl -s http://localhost:8000/health || echo "API not responding yet"

echo ""
echo "Database list:"
su - postgres -c "psql -c '\l'" | grep anwalts

echo ""
echo "🎉 Setup complete!"
echo "📱 Frontend: http://portal-anwalts.ai"
echo "🔧 API: http://portal-anwalts.ai/api/health"
echo ""
echo "If login still fails, check logs with: journalctl -u anwalts-api -f"