FROM python:3.12-slim
WORKDIR /app

# Optional: trust an extra CA bundle for networks behind a TLS-inspecting proxy
# (e.g. Zscaler). Run `make certs` to drop certs/corp-ca.pem here (gitignored).
# With no bundle present this is a harmless no-op, so the image builds anywhere.
COPY certs/ /etc/pip-ca/

COPY requirements.txt .
RUN if [ -f /etc/pip-ca/corp-ca.pem ]; then export PIP_CERT=/etc/pip-ca/corp-ca.pem; fi; \
    pip install --no-cache-dir -r requirements.txt
COPY app ./app
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
