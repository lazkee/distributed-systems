#!/bin/sh
# Wait for MySQL to be ready, using credentials from DATABASE_URL
set -e

host="$1"
shift
cmd="$@"

if [ -z "$DATABASE_URL" ]; then
  echo "ERROR: DATABASE_URL is not set" >&2
  exit 1
fi

# Parse mysql+pymysql://user:password@host:port/database
url_body=$(echo "$DATABASE_URL" | sed 's|^[^:]*://||')
db_user=$(echo "$url_body" | sed 's|:.*||')
db_password=$(echo "$url_body" | sed 's|[^:]*:||; s|@.*||')
db_host=$(echo "$url_body" | sed 's|.*@||; s|:.*||')
db_name=$(echo "$url_body" | sed 's|.*/||')

if [ -z "$db_user" ] || [ -z "$db_host" ] || [ -z "$db_name" ]; then
  echo "ERROR: Could not parse DATABASE_URL. Expected format: mysql+pymysql://user:password@host:port/database" >&2
  exit 1
fi

until mysql -h "$db_host" -u "$db_user" -p"$db_password" "$db_name" -e "select 1"; do
  echo "Waiting for MySQL at $db_host..."
  sleep 2
done

exec $cmd
