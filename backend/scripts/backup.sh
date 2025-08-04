#!/bin/bash
# PostgreSQL Backup Script for AnwaltsAI
# Creates compressed backups with timestamp and retention management

set -e

# Configuration
DB_HOST="${DB_HOST:-postgres}"
DB_PORT="${DB_PORT:-5432}"
DB_NAME="${DB_NAME:-anwalts_ai}"
DB_USER="${DB_USER:-postgres}"
BACKUP_DIR="${BACKUP_DIR:-/backups}"
RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-30}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Create backup directory if it doesn't exist
create_backup_dir() {
    if [ ! -d "$BACKUP_DIR" ]; then
        mkdir -p "$BACKUP_DIR"
        print_status "Created backup directory: $BACKUP_DIR"
    fi
}

# Check if PostgreSQL is accessible
check_postgres() {
    print_status "Checking PostgreSQL connection..."
    
    if pg_isready -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" > /dev/null 2>&1; then
        print_success "PostgreSQL is accessible"
    else
        print_error "Cannot connect to PostgreSQL at $DB_HOST:$DB_PORT"
        exit 1
    fi
}

# Create database backup
create_backup() {
    local timestamp=$(date +"%Y%m%d_%H%M%S")
    local backup_file="$BACKUP_DIR/anwalts_ai_backup_$timestamp.sql.gz"
    
    print_status "Creating backup: $backup_file"
    
    # Create compressed backup
    pg_dump -h "$DB_HOST" \
            -p "$DB_PORT" \
            -U "$DB_USER" \
            -d "$DB_NAME" \
            --verbose \
            --clean \
            --if-exists \
            --create \
            --format=plain \
            | gzip > "$backup_file"
    
    if [ $? -eq 0 ]; then
        local file_size=$(du -h "$backup_file" | cut -f1)
        print_success "Backup created successfully: $backup_file ($file_size)"
        echo "$backup_file"
    else
        print_error "Backup failed"
        exit 1
    fi
}

# Clean old backups
cleanup_old_backups() {
    print_status "Cleaning up backups older than $RETENTION_DAYS days..."
    
    local deleted_count=0
    
    # Find and delete old backup files
    while IFS= read -r -d '' file; do
        rm "$file"
        deleted_count=$((deleted_count + 1))
        print_status "Deleted old backup: $(basename "$file")"
    done < <(find "$BACKUP_DIR" -name "anwalts_ai_backup_*.sql.gz" -type f -mtime +$RETENTION_DAYS -print0)
    
    if [ $deleted_count -gt 0 ]; then
        print_success "Cleaned up $deleted_count old backup(s)"
    else
        print_status "No old backups to clean up"
    fi
}

# List existing backups
list_backups() {
    print_status "Existing backups:"
    
    if [ -d "$BACKUP_DIR" ]; then
        local backup_count=0
        
        for backup in "$BACKUP_DIR"/anwalts_ai_backup_*.sql.gz; do
            if [ -f "$backup" ]; then
                local file_size=$(du -h "$backup" | cut -f1)
                local file_date=$(date -r "$backup" "+%Y-%m-%d %H:%M:%S")
                echo "  - $(basename "$backup") ($file_size) - $file_date"
                backup_count=$((backup_count + 1))
            fi
        done
        
        if [ $backup_count -eq 0 ]; then
            print_warning "No backups found"
        else
            print_success "Found $backup_count backup(s)"
        fi
    else
        print_warning "Backup directory does not exist: $BACKUP_DIR"
    fi
}

# Restore from backup
restore_backup() {
    local backup_file="$1"
    
    if [ -z "$backup_file" ]; then
        print_error "Backup file not specified"
        echo "Usage: $0 restore <backup_file>"
        exit 1
    fi
    
    if [ ! -f "$backup_file" ]; then
        print_error "Backup file does not exist: $backup_file"
        exit 1
    fi
    
    print_warning "This will restore the database from: $backup_file"
    print_warning "This operation will DROP the existing database!"
    
    read -p "Are you sure you want to continue? (yes/no): " -r
    if [[ ! $REPLY =~ ^yes$ ]]; then
        print_status "Restore cancelled"
        exit 0
    fi
    
    print_status "Restoring database from backup..."
    
    # Restore from compressed backup
    gunzip -c "$backup_file" | psql -h "$DB_HOST" \
                                   -p "$DB_PORT" \
                                   -U "$DB_USER" \
                                   -d postgres \
                                   --verbose
    
    if [ $? -eq 0 ]; then
        print_success "Database restored successfully"
    else
        print_error "Restore failed"
        exit 1
    fi
}

# Verify backup integrity
verify_backup() {
    local backup_file="$1"
    
    if [ -z "$backup_file" ]; then
        print_error "Backup file not specified"
        echo "Usage: $0 verify <backup_file>"
        exit 1
    fi
    
    if [ ! -f "$backup_file" ]; then
        print_error "Backup file does not exist: $backup_file"
        exit 1
    fi
    
    print_status "Verifying backup integrity: $backup_file"
    
    # Test if the file can be decompressed and contains valid SQL
    if gunzip -t "$backup_file" 2>/dev/null; then
        print_success "Backup file compression is valid"
        
        # Check if it contains SQL commands
        if gunzip -c "$backup_file" | head -n 20 | grep -q -E "(CREATE|INSERT|DROP)" 2>/dev/null; then
            print_success "Backup contains valid SQL commands"
        else
            print_warning "Backup may not contain valid SQL"
        fi
    else
        print_error "Backup file is corrupted or invalid"
        exit 1
    fi
}

# Main function
main() {
    local command="${1:-backup}"
    
    case "$command" in
        "backup")
            echo "============================================"
            echo "🗄️  AnwaltsAI Database Backup"
            echo "============================================"
            create_backup_dir
            check_postgres
            create_backup
            cleanup_old_backups
            ;;
        "list")
            list_backups
            ;;
        "restore")
            check_postgres
            restore_backup "$2"
            ;;
        "verify")
            verify_backup "$2"
            ;;
        "cleanup")
            cleanup_old_backups
            ;;
        *)
            echo "Usage: $0 {backup|list|restore|verify|cleanup}"
            echo
            echo "Commands:"
            echo "  backup  - Create a new database backup (default)"
            echo "  list    - List existing backups"
            echo "  restore - Restore from a backup file"
            echo "  verify  - Verify backup file integrity"
            echo "  cleanup - Clean up old backups"
            echo
            echo "Environment variables:"
            echo "  DB_HOST            - Database host (default: postgres)"
            echo "  DB_PORT            - Database port (default: 5432)"
            echo "  DB_NAME            - Database name (default: anwalts_ai)"
            echo "  DB_USER            - Database user (default: postgres)"
            echo "  BACKUP_DIR         - Backup directory (default: /backups)"
            echo "  BACKUP_RETENTION_DAYS - Retention period (default: 30)"
            exit 1
            ;;
    esac
}

# Run main function with all arguments
main "$@"