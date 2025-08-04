# AnwaltsAI Backend

A production-ready FastAPI backend for the AnwaltsAI legal assistant application, featuring PostgreSQL database, Redis caching, JWT authentication, and Together AI integration.

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   FastAPI       │    │   PostgreSQL    │    │     Redis       │
│   Backend       │◄──►│   Database      │    │     Cache       │
│                 │    │                 │    │                 │
│ • Authentication│    │ • Users         │    │ • Sessions      │
│ • API Endpoints │    │ • Templates     │    │ • Rate Limiting │
│ • AI Integration│    │ • Clauses       │    │ • AI Responses  │
│ • File Handling │    │ • Documents     │    │ • Data Cache    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │
         ▼
┌─────────────────┐
│   Together AI   │
│   API Service   │
│                 │
│ • LLM Models    │
│ • Text Gen      │
│ • Document Gen  │
└─────────────────┘
```

## 🚀 Features

### Core Functionality
- **FastAPI Framework** - Modern, fast web API framework
- **Async Operations** - Full async/await support for optimal performance
- **PostgreSQL Database** - Reliable, ACID-compliant data storage
- **Redis Caching** - High-performance caching and session management
- **JWT Authentication** - Secure token-based authentication
- **Together AI Integration** - Advanced LLM capabilities

### Security Features
- **Password Hashing** - bcrypt with configurable rounds
- **Token Blacklisting** - JWT token revocation support
- **Rate Limiting** - Sliding window rate limiting
- **Input Validation** - Pydantic model validation
- **SQL Injection Protection** - Parameterized queries
- **CORS Configuration** - Configurable cross-origin requests

### Developer Experience
- **Comprehensive Logging** - Structured logging with levels
- **Health Checks** - Database and cache health monitoring
- **Error Handling** - Consistent error responses
- **API Documentation** - Auto-generated OpenAPI/Swagger docs
- **Docker Support** - Multi-stage Dockerfiles
- **Migration Tools** - Client data migration utilities

## 📦 Project Structure

```
backend/
├── main.py                 # FastAPI application entry point
├── database.py            # Database operations and connection pooling
├── cache_service.py       # Redis caching and session management
├── auth_service.py        # JWT authentication and security
├── ai_service.py          # Together AI integration
├── models.py              # Pydantic data models
├── requirements.txt       # Python dependencies
├── docker-compose.yml     # Docker services configuration
├── Dockerfile             # Multi-stage Docker build
├── .env.example          # Environment configuration template
├── database/
│   └── schema.sql        # PostgreSQL database schema
├── migration/
│   ├── migrate_client_data.py    # Data migration script
│   └── extract_client_data.js    # Browser data extraction
└── scripts/
    ├── setup.sh          # Environment setup script
    └── backup.sh         # Database backup script
```

## 🛠️ Quick Start

### Option 1: Docker Compose (Recommended)

1. **Clone and Setup**
   ```bash
   cd backend
   cp .env.example .env
   # Edit .env with your configuration
   ```

2. **Start Services**
   ```bash
   docker-compose up -d
   ```

3. **Check Health**
   ```bash
   curl http://localhost:8000/health
   ```

### Option 2: Manual Setup

1. **Prerequisites**
   ```bash
   # Python 3.11+
   python3 --version
   
   # PostgreSQL 13+
   psql --version
   
   # Redis 6+
   redis-cli --version
   ```

2. **Environment Setup**
   ```bash
   chmod +x scripts/setup.sh
   ./scripts/setup.sh
   ```

3. **Database Setup**
   ```bash
   psql -U postgres -f database/schema.sql
   ```

4. **Start Application**
   ```bash
   source venv/bin/activate
   uvicorn main:app --reload
   ```

## 🔧 Configuration

### Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
# Database
DATABASE_URL=postgresql://postgres:password@localhost:5432/anwalts_ai
DB_HOST=localhost
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=your_password
DB_NAME=anwalts_ai

# Redis
REDIS_URL=redis://localhost:6379/0
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=your_redis_password

# JWT Security
JWT_SECRET_KEY=your-256-bit-secret-key
ACCESS_TOKEN_EXPIRE_MINUTES=1440
REFRESH_TOKEN_EXPIRE_DAYS=30

# Together AI
TOGETHER_API_KEY=your_together_api_key
DEFAULT_AI_MODEL=meta-llama/Llama-2-7b-chat-hf

# Application
ENVIRONMENT=development
DEBUG=false
LOG_LEVEL=INFO
```

### Security Configuration

- **JWT Secret**: Use a cryptographically secure 256-bit key
- **Password Policy**: Minimum 8 characters with complexity requirements
- **Rate Limiting**: Configurable requests per minute/hour
- **CORS Origins**: Whitelist allowed frontend domains

## 📊 API Endpoints

### Authentication
- `POST /auth/login` - User login
- `POST /auth/register` - User registration
- `GET /auth/me` - Get current user info

### Templates
- `GET /api/templates` - List user templates
- `POST /api/templates` - Create template
- `PUT /api/templates/{id}` - Update template
- `DELETE /api/templates/{id}` - Delete template

### Clauses
- `GET /api/clauses` - List user clauses
- `POST /api/clauses` - Create clause

### Clipboard
- `GET /api/clipboard` - List clipboard entries
- `POST /api/clipboard` - Add clipboard entry

### AI Services
- `POST /api/ai/complete` - Generate AI completion
- `POST /api/ai/generate-document` - Generate legal document

### System
- `GET /health` - Health check
- `GET /docs` - API documentation (Swagger UI)

## 🔄 Data Migration

### From Client Storage

1. **Extract Client Data**
   ```javascript
   // Run in browser console on existing AnwaltsAI site
   // Copy and paste migration/extract_client_data.js
   downloadAnwaltsAIData()  // Downloads JSON file
   ```

2. **Migrate to Database**
   ```bash
   python migration/migrate_client_data.py migrate --file client_data.json
   ```

3. **Verify Migration**
   ```bash
   python migration/migrate_client_data.py migrate --file client_data.json --dry-run
   ```

### Sample Data

Generate sample migration file:
```bash
python migration/migrate_client_data.py sample --output sample_data.json
```

## 🗄️ Database Management

### Backup & Restore

```bash
# Create backup
./scripts/backup.sh backup

# List backups
./scripts/backup.sh list

# Restore backup
./scripts/backup.sh restore backup_file.sql.gz

# Verify backup
./scripts/backup.sh verify backup_file.sql.gz
```

### Schema Updates

The database schema includes:
- **Users** - Authentication and profiles
- **Templates** - Legal document templates
- **Clauses** - Reusable legal clauses
- **Clipboard** - Temporary content storage
- **Documents** - Generated documents with AI metadata
- **Sessions** - User session management
- **Analytics** - Usage tracking and metrics

## 🚦 Monitoring & Logging

### Health Checks

- **Database**: Connection pool status
- **Cache**: Redis connectivity
- **AI Service**: API availability
- **Application**: Memory and performance metrics

### Logging

Structured logging with configurable levels:
```python
import logging
logger = logging.getLogger(__name__)

logger.info("User authenticated", extra={"user_id": user.id})
logger.warning("Rate limit approached", extra={"client_ip": request.client.host})
logger.error("Database connection failed", extra={"error": str(e)})
```

### Performance Monitoring

- Request/response times
- Database query performance
- Cache hit/miss ratios
- AI API usage and costs
- Error rates and patterns

## 🔒 Security Best Practices

### Authentication & Authorization
- JWT tokens with short expiration
- Refresh token rotation
- Password strength validation
- Account lockout after failed attempts

### Data Protection
- Input validation and sanitization
- SQL injection prevention via parameterized queries
- XSS protection with proper encoding
- CSRF protection for state-changing operations

### Infrastructure Security
- Non-root Docker containers
- Minimal base images
- Secrets management via environment variables
- Network isolation with Docker networks

## 🧪 Testing

### Running Tests
```bash
# Install test dependencies
pip install -r requirements-dev.txt

# Run tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test file
pytest tests/test_auth.py -v
```

### Test Categories
- **Unit Tests**: Individual function testing
- **Integration Tests**: Database and API testing
- **Security Tests**: Authentication and authorization
- **Performance Tests**: Load and stress testing

## 🚀 Deployment

### Production Deployment

1. **Environment Setup**
   ```bash
   # Production environment file
   cp .env.example .env.production
   # Configure production values
   ```

2. **Docker Deployment**
   ```bash
   # Build production image
   docker build --target production -t anwalts-ai-backend .
   
   # Deploy with compose
   docker-compose -f docker-compose.yml up -d
   ```

3. **Health Verification**
   ```bash
   curl https://your-domain.com/health
   ```

### Scaling Considerations

- **Horizontal Scaling**: Multiple backend instances with load balancer
- **Database**: PostgreSQL read replicas for query scaling
- **Cache**: Redis cluster for high availability
- **CDN**: Static asset delivery optimization
- **Monitoring**: Application performance monitoring (APM)

## 📈 Performance Optimization

### Database
- Connection pooling (5-20 connections)
- Query optimization and indexing
- Read replica usage for analytics
- Connection timeout management

### Caching
- Template and clause caching (1-2 hours TTL)
- AI response caching (2 hours TTL)
- Session data in Redis
- Rate limiting with sliding windows

### API
- Response compression (gzip)
- Async request handling
- Connection keep-alive
- Request timeout limits

## 🐛 Troubleshooting

### Common Issues

**Database Connection Issues:**
```bash
# Check PostgreSQL status
docker-compose logs postgres

# Test connection
psql -h localhost -U postgres -d anwalts_ai
```

**Redis Connection Issues:**
```bash
# Check Redis status
docker-compose logs redis

# Test connection
redis-cli ping
```

**Authentication Issues:**
```bash
# Check JWT configuration
python -c "from auth_service import AuthService; print(AuthService()._get_secret_key())"
```

### Debug Mode

Enable debug logging:
```bash
export LOG_LEVEL=DEBUG
export DEBUG=true
uvicorn main:app --reload --log-level debug
```

## 📝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run the test suite
6. Submit a pull request

### Code Standards
- **Black** for code formatting
- **isort** for import sorting  
- **flake8** for linting
- **mypy** for type checking
- **pytest** for testing

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
- **Documentation**: Check this README and API docs at `/docs`
- **Issues**: GitHub Issues for bug reports
- **Discussions**: GitHub Discussions for questions
- **Health Check**: `GET /health` for system status

## 🔄 Changelog

### v1.0.0 (Current)
- Initial production release
- Complete CRUD operations for all entities
- JWT authentication with refresh tokens
- Together AI integration
- Redis caching and session management
- Docker containerization
- Data migration tools
- Comprehensive logging and monitoring
- Production-ready configuration

---

**Built with ❤️ for the legal profession**