# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Flask-based e-commerce admin panel and Telegram bot backend for "Elevamart" (online marketplace). The application manages product catalogs, promotional content, payment information, and integrates with a Telegram bot for customer engagement. All product images are stored on Yandex Cloud S3.

## Development Commands

### Running the Application
```bash
# Run the main Flask application (also starts the Telegram bot in background thread)
python3 admin.py

# The app will be available at http://localhost:5000
```

### Database Management
```bash
# Initialize database (creates all tables)
# This is handled automatically on startup in admin.py via db.create_all()

# For migrations (Flask-Migrate is installed but not actively used):
flask db init          # Initialize migrations (if needed)
flask db migrate -m "description"  # Create migration
flask db upgrade       # Apply migrations
```

### Environment Setup
```bash
# Install dependencies
pip3 install -r requirements.txt
pip3 install aiogram   # Note: aiogram is missing from requirements.txt

# Create environment file at secrets/.env with required variables:
FLASK_SECRET_KEY=your-secret-key
ADMIN_PASSWORD=your-admin-password
TELEGRAM_BOT_TOKEN=your-telegram-bot-token
YC_ACCESS_KEY=yandex-cloud-access-key
YC_SECRET_KEY=yandex-cloud-secret-key
YC_BUCKET_NAME=your-bucket-name
YC_ENDPOINT_URL=https://storage.yandexcloud.net
```

### Git Commands
```bash
# Check status
git status

# View recent commits
git log --oneline -10

# Create branch for new feature
git checkout -b feature/description
```

## Application Architecture

### Entry Point and Initialization
- **Main file:** `admin.py` (315 lines)
- App initialization creates Flask instance, configures SQLAlchemy with SQLite database (`database.db`)
- On startup: creates admin user (username: `admin`, password from `ADMIN_PASSWORD` env var)
- Spawns daemon thread running Telegram bot via `bot_handler.py`
- Uses Flask-Login for session-based authentication

### Route Organization (Non-Blueprint Architecture)
All routes defined directly in `admin.py`:

**Authenticated Admin Routes** (require login):
- `/` - Admin dashboard
- `/login`, `/logout` - Authentication
- `/promo` - Manage promotional images
- `/bestsales` - Manage top sales products
- `/new_products` - Manage new product listings
- `/metadata` - System settings (support links, category images)
- `/payment` - Payment information management
- `/bot_settings` - Telegram bot configuration and broadcasts

**Public API Routes** (no authentication, CORS enabled):
- `/api/promo` - Get promotional images
- `/api/bestSales` - Get best-selling products
- `/api/new_products` - Get new products
- `/api/metadata` - Get system metadata
- `/api/payment` - Get active payment methods

### Database Models (modules/models.py)
11 SQLAlchemy models:
- **User** - Admin authentication
- **Promo** - Promotional images
- **Bestsales** - Top-selling products
- **NewProducts** - New product listings
- **Metadata** - Key-value configuration store
- **PaymentInfo** - Bank account details for customer payments
- **BotSettings** - Telegram bot welcome message/image
- **BotUser** - Registered Telegram bot users
- **BroadcastMessage** - Scheduled broadcast messages
- **BroadcastImage** - Images attached to broadcasts

### Module Structure

**modules/** - Core utilities:
- `models.py` - SQLAlchemy ORM models (11 models)
- `s3_controller.py` - Yandex Cloud S3 integration (upload/delete with AWS4 signatures)
- `image_tools.py` - Legacy image utilities
- `api.py` - API response formatting and caching

**pages_py/** - Request handlers (functional modules):
- `promo.py` - Promotional image CRUD handlers
- `BestSales.py` - Best sales product CRUD handlers
- `new_products.py` - New products CRUD handlers
- `metadata.py` - Metadata management and category image uploads
- `payment.py` - Payment information CRUD
- `bot_settings.py` - Bot configuration, broadcast creation/sending
- `api.py` - Public API endpoints with 10-60 second caching

**login/** - Authentication:
- `login.py` - Login/logout handlers, password verification

**middleware/** - Request processing:
- `cors.py` - CORS header injection for `/api/*` routes

**bot_handler.py** - Telegram bot (using aiogram library):
- `/start` command handler - registers users, sends welcome message
- Broadcast sending (text + images)
- Runs in background thread via asyncio

### External Integrations

**Yandex Cloud S3 Storage** (modules/s3_controller.py):
- AWS-compatible S3 API with AWS4-HMAC-SHA256 signatures
- All product/promo images uploaded to cloud storage
- Base URL: `https://sqwonkerb.storage.yandexcloud.net/`
- Functions: `upload_image_to_s3()`, `delete_image_from_s3()`

**Telegram Bot API** (bot_handler.py):
- Using aiogram 3.x framework
- Polling mode (runs in background thread)
- Features: user registration, welcome messages, broadcast messaging
- Stores user data in both database (BotUser table) and JSON files (data/users/)

### API Design Patterns

**Caching Strategy:**
- Multiple modules implement independent time-based caching
- Promo/bestsales: 10 second cache
- Metadata/new products: 60 second cache
- Cache decorator pattern in `modules/api.py` and `pages_py/api.py`

**CORS Configuration:**
- All `/api/*` routes have CORS headers added via middleware
- `Access-Control-Allow-Origin: *` (open to all origins)
- Allows GET, POST, PUT, DELETE, OPTIONS, PATCH

### Request Processing Flow Example

**Adding a promotional image:**
1. POST to `/upload` (authenticated)
2. `upload_image_handler()` receives file + metadata
3. Generate UUID filename, save temporarily to `static/uploads/`
4. Upload to S3 via `upload_image_to_s3()` (AWS4 signed request)
5. Create Promo model with S3 URL
6. Save to database, delete temporary file
7. Return JSON response
8. Cache clears on next `/api/promo` request

### Authentication Flow

**Flask-Login session-based:**
- Admin login at `/login` with username/password
- Password hashing via `werkzeug.security.generate_password_hash()`
- `@login_required` decorator on all admin routes
- `before_request()` middleware redirects unauthenticated requests
- API routes explicitly bypass authentication

### Bot Functionality

**User Registration:**
- `/start` command creates BotUser record
- Saves user JSON file: `data/users/{chat_id}.json`
- Adds chat_id to `data/users_list.txt`

**Welcome Messages:**
- Customizable text stored in `data/welcome_message.txt` and BotSettings table
- Optional image from S3
- Inline button with WebAppInfo link to https://smarket-irk.ru/

**Broadcast System:**
- Create broadcasts via `/bot_settings` admin panel
- Upload multiple images (stored in S3)
- Status tracking: pending → sent
- Send to all registered users via `send_broadcast()`

## File Upload Handling

1. Files temporarily saved to `static/uploads/`
2. Uploaded to Yandex Cloud S3 with UUID filename
3. S3 URL stored in database
4. Temporary file deleted
5. Max upload size: 16MB (configured in Flask)

## Important Notes

- **No Blueprints:** All routes defined in single `admin.py` file (non-standard but simple)
- **Multiple Cache Implementations:** Several modules have independent caching decorators
- **Bot Thread Safety:** Bot runs in daemon thread, uses nest_asyncio for event loop
- **Database:** SQLite with connection pooling (pool_size: 50, max_overflow: 100)
- **File-based Config:** Some settings duplicated in both database and text files (data/)
- **aiogram Missing:** `aiogram` library not in requirements.txt but required for bot

## Common Development Tasks

### Adding a New Product Category
1. Update `Metadata` table with category key-value pairs
2. Upload category image via `/metadata` page
3. Category images stored with key pattern: `category_image_{name}`

### Creating a Bot Broadcast
1. Navigate to `/bot_settings`
2. Click "Создать рассылку" (Create Broadcast)
3. Add text and upload images (optional)
4. Submit - status set to "pending"
5. Click "Отправить" to send to all users

### Modifying Welcome Message
1. Navigate to `/bot_settings`
2. Update text in "Приветственное сообщение" field
3. Optionally upload new welcome image
4. Submit - updates both database and `data/welcome_message.txt`

### Adding New Payment Method
1. Navigate to `/payment`
2. Fill in bank account details (account number, bank name, recipient)
3. Toggle active status as needed
4. Only active payment methods shown in `/api/payment`

## Security Considerations

- All admin routes protected by `@login_required`
- Passwords hashed with werkzeug.security
- S3 requests signed with AWS4-HMAC-SHA256
- SQLAlchemy ORM prevents SQL injection
- CORS currently open to all origins (consider restricting in production)
- Secrets managed via environment variables in `secrets/.env`

## File Structure Summary

```
backend/
├── admin.py                    # Main Flask app + all routes
├── bot_handler.py              # Telegram bot (aiogram)
├── requirements.txt            # Python dependencies
├── database.db                 # SQLite database
├── modules/
│   ├── models.py               # ORM models (11 tables)
│   ├── s3_controller.py        # S3 upload/delete
│   ├── image_tools.py          # Image utilities
│   └── api.py                  # API caching
├── pages_py/                   # Request handlers by feature
│   ├── promo.py
│   ├── BestSales.py
│   ├── new_products.py
│   ├── metadata.py
│   ├── payment.py
│   ├── bot_settings.py
│   └── api.py                  # Public APIs with caching
├── login/
│   └── login.py                # Authentication
├── middleware/
│   └── cors.py                 # CORS headers
├── templates/                  # HTML templates for admin UI
├── static/
│   └── uploads/                # Temporary file storage
├── data/                       # Bot configuration files
│   ├── welcome_message.txt
│   ├── welcome_image_url.txt
│   └── users/                  # User JSON files
└── secrets/
    └── .env                    # Environment variables
```
