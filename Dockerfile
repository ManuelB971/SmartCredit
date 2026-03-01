FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV APP_HOME=/app
ENV PYTHONPATH=/app/backend:$PYTHONPATH
ENV DJANGO_SETTINGS_MODULE=smart_credit.settings.development

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR $APP_HOME

# Copy requirements
COPY backend/requirements.txt .

# Install Python dependencies
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Copy project
COPY . .

# Create necessary directories
RUN mkdir -p staticfiles media/pdf

# Expose port
EXPOSE 8000

# Run development server
CMD ["python", "-m", "django", "runserver", "0.0.0.0:8000"]
