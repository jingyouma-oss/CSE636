# Stage 1: build the React app to static files
FROM node:20-alpine AS build
WORKDIR /app

# Optional: trust an extra CA bundle for networks behind a TLS-inspecting proxy
# (e.g. Zscaler). Run `make certs` to drop certs/corp-ca.pem here (gitignored).
# With no bundle present this is a harmless no-op, so the image builds anywhere.
COPY certs/ /etc/npm-ca/

COPY package.json ./
RUN if [ -f /etc/npm-ca/corp-ca.pem ]; then export NODE_EXTRA_CA_CERTS=/etc/npm-ca/corp-ca.pem; fi; \
    npm install
COPY . .
RUN npm run build

# Stage 2: serve with Nginx (the /api proxy config is mounted from a ConfigMap)
FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
