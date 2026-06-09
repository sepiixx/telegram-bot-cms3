# Dynamic Telegram Bot CMS with Web Admin Panel

A production-ready Telegram Bot Management System built with Python, FastAPI, and SQLAlchemy. Complete admin panel for non-programmers to manage Telegram bots without coding.

## Features

### Core Telegram Bot Features
- ✅ Dynamic menu generation from database
- ✅ Unlimited nested menus and submenus
- ✅ Dynamic content pages (text, images, videos, files)
- ✅ Automatic back/home buttons
- ✅ Points-based access control
- ✅ Referral system with automatic rewards
- ✅ Forced join verification (channels/groups)
- ✅ Support ticket system
- ✅ Broadcast messaging (text, media, documents)
- ✅ Media library for reusable assets

### Admin Panel
- 📊 Dashboard with analytics
- 👥 User management
- 🔘 Button/menu management
- 📝 Content management
- 💰 Points system administration
- 🎁 Referral tracking and rewards
- 📞 Support ticket management
- 📢 Broadcast campaigns
- 📅 Task scheduling
- 🔐 Security and authentication

## Technology Stack

- **Backend**: FastAPI
- **Telegram Integration**: python-telegram-bot
- **Database**: SQLAlchemy ORM (SQLite dev, PostgreSQL production)
- **Authentication**: JWT
- **Frontend**: Jinja2 + Bootstrap 5
- **Task Scheduling**: APScheduler
- **Server**: Uvicorn

## Project Structure

```
app/
├── bot/                 # Telegram bot handlers and commands
├── admin/               # Admin panel routes and logic
├── database/            # Database initialization and migrations
├── models/              # SQLAlchemy models
├── schemas/             # Pydantic schemas for validation
├── services/            # Business logic services
├── repositories/        # Database repository layer
├── middleware/          # Authentication and CORS middleware
├── scheduler/           # Background task scheduling
├── utils/               # Utility functions
├── config/              # Configuration management
├── static/              # CSS, JS, images
├── templates/           # HTML templates
├── main.py              # FastAPI application
└── __init__.py

```

## Installation

### Requirements
- Python 3.12+
- SQLite (development) or PostgreSQL (production)

### Local Setup

1. Clone the repository:
```bash
git clone https://github.com/sepiixx/telegram-bot-cms3.git
cd telegram-bot-cms3
```

2. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create `.env` file:
```env
# FastAPI
FAST_API_HOST=0.0.0.0
FAST_API_PORT=8000
FAST_API_RELOAD=True

# Telegram
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_BOT_USERNAME=your_bot_username

# Database
DATABASE_URL=sqlite:///./telegram_bot.db
# For PostgreSQL: postgresql://user:password@localhost/dbname

# JWT
JWT_SECRET_KEY=your_super_secret_key_here_change_in_production
JWT_ALGORITHM=HS256
JWT_EXPIRE_DAYS=30

# Admin
ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin123

# Webhook (if using webhook instead of polling)
WEBHOOK_URL=https://yourdomain.com/webhook
```

5. Initialize database:
```bash
python -m app.database.init_db
```

6. Run the application:
```bash
uvicorn app.main:app --reload
```

Access:
- Telegram Bot: Talk to your bot on Telegram
- Admin Panel: http://localhost:8000/admin
- API Docs: http://localhost:8000/docs

## Configuration Guide

### Environment Variables

All configuration is done through `.env` file. See `.env.example` for all available options.

### Database

- **Development**: SQLite (file-based, no setup needed)
- **Production**: PostgreSQL (recommended)

Migrations are handled by SQLAlchemy ORM.

### Telegram Bot Token

1. Create a bot with @BotFather on Telegram
2. Copy the bot token
3. Set `TELEGRAM_BOT_TOKEN` in `.env`

## Deployment

### Docker

```bash
docker-compose up -d
```

See `docker-compose.yml` for configuration.

### VPS (Linux)

See `docs/VPS_DEPLOYMENT.md` for step-by-step guide.

### Local

See Installation section above.

## API Documentation

Interactive API docs available at `/docs` when server is running.

## Database Schema

See `docs/DATABASE_SCHEMA.md` for detailed schema documentation.

## Contributing

Pull requests welcome. For major changes, please open an issue first.

## License

MIT

## Support

For issues and questions, please use the GitHub issues page.
