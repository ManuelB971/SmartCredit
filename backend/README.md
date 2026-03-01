# Smart Crédit

**Un simulateur de crédit intelligent alimenté par l'IA.**

## 🚀 Quick Start

```bash
# 1. Clone repo
git clone <repo>
cd smart-credit

# 2. Setup venv
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r backend/requirements.txt

# 4. Setup .env
cp .env.example .env
# Edit .env with your values

# 5. Setup database
python manage.py migrate
python manage.py createsuperuser

# 6. Run dev server
python manage.py runserver
```

**App**: http://localhost:8000
**Admin**: http://localhost:8000/admin

## 📦 Architecture

- **Backend**: Django 5.x + DRF API
- **Database**: PostgreSQL 16
- **Frontend**: Bootstrap 5 (Tabler) + Vanilla JS
- **IA**: Groq/HuggingFace LLM integration

See [docs/architecture.md](docs/architecture.md) for details.

## 🧪 Testing

```bash
python manage.py test
coverage run manage.py test && coverage report
```

## 📝 Documentation

- [Architecture](docs/architecture.md)
- [API Reference](docs/api.md)
- [README.md](../README.md)

## 👥 Team

ECE Paris Tech — DEVBANK 2025/2026
