FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

# Note: JWT_SECRET_KEY should be set via docker-compose or runtime environment
# If not set, the app will generate a random key (tokens won't persist across restarts)
# ENV JWT_SECRET_KEY=  # Don't set a default - let the app generate or require it

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--timeout", "120", "app:app"]
