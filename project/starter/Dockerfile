# A minimal container image for the starter service.
# You'll learn what each line does in Week 1's Docker foundations.

FROM python:3.12-slim

# Don't write .pyc files; flush logs immediately (good defaults for containers).
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Copy requirements first so Docker can cache the dependency layer.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Now copy the application code.
COPY app ./app

EXPOSE 8000

CMD ["python", "-m", "app.main"]
