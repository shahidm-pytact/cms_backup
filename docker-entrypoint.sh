#!/bin/bash
set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Container Startup Script${NC}"
echo -e "${GREEN}========================================${NC}"

# Function to check database connectivity
check_database() {
    echo -e "${YELLOW}Checking database connectivity...${NC}"
    
    # Extract database connection details from DATABASE_URL
    # Format: postgresql+asyncpg://user:pass@host:port/dbname
    if [ -z "$DATABASE_URL" ]; then
        echo -e "${RED}ERROR: DATABASE_URL environment variable is not set${NC}"
        exit 1
    fi
    
    # Parse DATABASE_URL to get host and port
    # Remove postgresql+asyncpg:// or postgresql:// prefix
    DB_CONN=$(echo "$DATABASE_URL" | sed 's|postgresql+asyncpg://||' | sed 's|postgresql://||')
    # Extract user:pass@host:port/dbname
    DB_CRED_HOST=$(echo "$DB_CONN" | cut -d'/' -f1)
    DB_HOST=$(echo "$DB_CRED_HOST" | cut -d'@' -f2 | cut -d':' -f1)
    DB_PORT=$(echo "$DB_CRED_HOST" | cut -d'@' -f2 | cut -d':' -f2)
    
    # Default port if not specified
    if [ -z "$DB_PORT" ] || [ "$DB_PORT" = "$DB_HOST" ]; then
        DB_PORT=5432
    fi
    
    # Extract username (for pg_isready)
    DB_USER=$(echo "$DB_CRED_HOST" | cut -d'@' -f1 | cut -d':' -f1)
    if [ -z "$DB_USER" ]; then
        DB_USER=postgres
    fi
    
    echo -e "${YELLOW}Connecting to database at $DB_HOST:$DB_PORT as $DB_USER...${NC}"
    
    # Wait for database to be ready (max 30 attempts, 2 seconds each = 60 seconds)
    MAX_RETRIES=30
    RETRY_COUNT=0
    
    while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
        if pg_isready -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" > /dev/null 2>&1; then
            echo -e "${GREEN}✓ Database is ready${NC}"
            return 0
        fi
        
        RETRY_COUNT=$((RETRY_COUNT + 1))
        if [ $RETRY_COUNT -lt $MAX_RETRIES ]; then
            echo -e "${YELLOW}Waiting for database... (attempt $RETRY_COUNT/$MAX_RETRIES)${NC}"
            sleep 2
        fi
    done
    
    echo -e "${RED}ERROR: Database is not ready after $MAX_RETRIES attempts${NC}"
    echo -e "${RED}Database host: $DB_HOST, port: $DB_PORT${NC}"
    exit 1
}

# Function to run migrations
run_migrations() {
    echo -e "${YELLOW}Running database migrations...${NC}"
    
    # Run alembic upgrade head
    if alembic upgrade head; then
        echo -e "${GREEN}✓ Migrations completed successfully${NC}"
        return 0
    else
        echo -e "${RED}ERROR: Migration failed${NC}"
        exit 1
    fi
}

# Main execution
main() {
    # Check database connectivity
    check_database
    
    # Run migrations
    run_migrations
    
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}Starting application...${NC}"
    echo -e "${GREEN}========================================${NC}"
    
    # Execute the command passed to the container
    # This allows the script to work with any command (uvicorn, celery, etc.)
    exec "$@"
}

# Run main function 
main "$@"

