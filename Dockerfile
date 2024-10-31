# Backend stage
FROM python:3.11-alpine as backend
RUN apk add --no-cache gcc musl-dev libffi-dev
WORKDIR /app/backend
COPY ./back .
RUN apk add --no-cache curl && \
    curl -L https://ghcr.io/astral-sh/uv:latest -o /usr/local/bin/uv && \
    chmod +x /usr/local/bin/uv

RUN uv pip install --no-cache-dir -r req.txt

# Frontend stage
FROM node:20 as frontend
WORKDIR /app/frontend
COPY ./front .
RUN npm install
RUN npm run build

# Final stage
FROM python:3.11-alpine
WORKDIR /app
COPY --from=backend /app/backend /app/backend
COPY --from=frontend /app/frontend /app/frontend
EXPOSE 8000 3002

# Start both services
CMD ["sh", "-c", "cd /app/backend && uvicorn main:app --host 0.0.0.0 --port 8000 & cd /app/frontend && npm start"]