#!/bin/sh

# Initialize PostgreSQL
su postgres -c 'pg_ctl initdb -D /var/lib/postgresql/data'
su postgres -c 'echo "listen_addresses = '\''*'\''" >> /var/lib/postgresql/data/postgresql.conf'
su postgres -c 'echo "host all all 0.0.0.0/0 trust" >> /var/lib/postgresql/data/pg_hba.conf'
su postgres -c 'pg_ctl start -D /var/lib/postgresql/data'

# Start backend with correct venv path
cd /app/backend
/app/backend/venv/bin/python -m uvicorn main:app --host 0.0.0.0 --port 8000 &

cd /app/frontend
node -r dotenv/config build

# Wait indefinitely to keep the container running
tail -f /dev/null
