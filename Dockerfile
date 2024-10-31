# Backend stage
FROM python:3.11-alpine AS backend
RUN apk add --no-cache gcc musl-dev libffi-dev
WORKDIR /app/backend
COPY ./back .

# Create and activate virtual environment with all dependencies
RUN python -m venv venv && \
    . venv/bin/activate && \
    pip install --no-cache-dir -r req.txt fastapi uvicorn

# Frontend stage
FROM node:20 AS frontend
WORKDIR /app/frontend
COPY ./front .
RUN npm install
RUN npm run build

# Final stage
FROM python:3.11-alpine
RUN apk add --no-cache gcc musl-dev libffi-dev nodejs npm postgresql postgresql-contrib
WORKDIR /app

# Copy backend with venv and install dependencies in final stage
COPY --from=backend /app/backend /app/backend
RUN . /app/backend/venv/bin/activate && \
    pip install --no-cache-dir -r /app/backend/req.txt fastapi uvicorn

# Copy frontend build
COPY --from=frontend /app/frontend /app/frontend

# Set up PostgreSQL directories
RUN mkdir -p /var/lib/postgresql/data && chown -R postgres:postgres /var/lib/postgresql/data && \
    mkdir -p /run/postgresql && chown -R postgres:postgres /run/postgresql

# Install dotenv globally for frontend
RUN npm install -g dotenv

EXPOSE 8000 3000 5432

COPY ./docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

ENTRYPOINT ["docker-entrypoint.sh"]
