# Backend stage
FROM python:3.11-alpine AS backend
RUN apk add --no-cache gcc musl-dev libffi-dev
WORKDIR /app/backend
COPY ./back .
RUN pip install --no-cache-dir -r req.txt uvicorn

# Frontend stage
FROM node:20 AS frontend
WORKDIR /app/frontend
COPY ./front .
RUN npm install
RUN npm run build

# Final stage
FROM python:3.11-alpine
RUN apk add --no-cache nodejs npm postgresql postgresql-contrib
WORKDIR /app
COPY --from=backend /app/backend /app/backend
COPY --from=frontend /app/frontend /app/frontend
EXPOSE 8000 3002 5432

# Initialize PostgreSQL data directory
RUN mkdir -p /var/lib/postgresql/data && chown -R postgres:postgres /var/lib/postgresql

# Create the run directory for PostgreSQL
RUN mkdir -p /run/postgresql && chown -R postgres:postgres /run/postgresql

# Install dotenv for loading environment variables
RUN npm install -g dotenv

# Start all services
CMD sh -c "su postgres -c 'pg_ctl initdb -D /var/lib/postgresql/data' && \
     su postgres -c 'echo \"listen_addresses = '\''*'\''\" >> /var/lib/postgresql/data/postgresql.conf' && \
     su postgres -c 'echo \"host all all 0.0.0.0/0 trust\" >> /var/lib/postgresql/data/pg_hba.conf' && \
     su postgres -c 'pg_ctl start -D /var/lib/postgresql/data' && \
     cd /app/backend && uvicorn main:app --host 0.0.0.0 --port 8000 & \
     cd /app/frontend && node -r dotenv/config build"

