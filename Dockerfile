# Backend stage
FROM python:3.11-alpine AS backend
RUN apk add --no-cache gcc musl-dev libffi-dev
WORKDIR /app/backend
COPY ./back .
RUN pip install --no-cache-dir -r req.txt fastapi

# Frontend stage
FROM node:20 AS frontend
WORKDIR /app/frontend
COPY ./front .
RUN npm install
RUN npm run build

# Final stage
FROM python:3.11-alpine
RUN apk add --no-cache nodejs npm postgresql postgresql-contrib libffi-dev
WORKDIR /app
COPY --from=backend /app/backend /app/backend
COPY --from=frontend /app/frontend /app/frontend

# Set up environment and permissions for PostgreSQL
RUN mkdir -p /var/lib/postgresql/data && chown -R postgres:postgres /var/lib/postgresql/data
RUN mkdir -p /run/postgresql && chown -R postgres:postgres /run/postgresql

# Install dotenv globally for frontend
RUN npm install -g dotenv

# Expose necessary ports
EXPOSE 8000 3000 5432

# Set up entrypoint for running services
COPY ./docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

ENTRYPOINT ["docker-entrypoint.sh"]
