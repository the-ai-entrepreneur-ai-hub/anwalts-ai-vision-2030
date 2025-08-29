#!/usr/bin/env python3
"""
Client Data Migration Script for AnwaltsAI
Migrates data from localStorage/sessionStorage to PostgreSQL database
"""

import asyncio
import json
import uuid
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path
import argparse
import sys
import os

# Add the parent directory to the path to import our modules
sys.path.append(str(Path(__file__).parent.parent))

from database import Database
from auth_service import AuthService
from models import UserInDB, TemplateInDB, ClauseInDB, ClipboardEntryInDB

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('migration.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ClientDataMigrator:
    """Migrates client-side data to PostgreSQL database"""
    
    def __init__(self):
        self.db = Database()
        self.auth_service = AuthService()
        self.migration_stats = {
            'users_created': 0,
            'users_updated': 0,
            'templates_migrated': 0,
            'clauses_migrated': 0,
            'clipboard_entries_migrated': 0,
            'errors': 0
        }
    
    async def initialize(self):
        """Initialize database connection"""
        try:
            await self.db.connect()
            logger.info("Database connection established")
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise
    
    async def cleanup(self):
        """Cleanup database connection"""
        await self.db.disconnect()
        logger.info("Database connection closed")
    
    def load_client_data(self, data_file: str) -> Dict[str, Any]:
        """Load client data from JSON file"""
        try:
            with open(data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            logger.info(f"Loaded client data from {data_file}")
            logger.info(f"Data keys: {list(data.keys())}")
            
            return data
        except Exception as e:
            logger.error(f"Failed to load client data from {data_file}: {e}")
            raise
    
    def validate_client_data(self, data: Dict[str, Any]) -> bool:
        """Validate client data structure"""
        try:
            required_keys = ['user_info', 'templates', 'clauses', 'clipboard']
            
            for key in required_keys:
                if key not in data:
                    logger.warning(f"Missing required key: {key}")
                    data[key] = [] if key != 'user_info' else {}
            
            # Validate user_info
            if not isinstance(data['user_info'], dict):
                logger.error("user_info must be a dictionary")
                return False
            
            # Validate arrays
            for key in ['templates', 'clauses', 'clipboard']:
                if not isinstance(data[key], list):
                    logger.error(f"{key} must be a list")
                    return False
            
            logger.info("Client data validation passed")
            return True
        except Exception as e:
            logger.error(f"Data validation failed: {e}")
            return False
    
    async def migrate_user(self, user_data: Dict[str, Any]) -> UserInDB:
        """Migrate or create user"""
        try:
            email = user_data.get('email')
            name = user_data.get('name')
            role = user_data.get('role', 'assistant')
            
            if not email or not name:
                raise ValueError("Email and name are required for user creation")
            
            # Check if user already exists
            existing_user = await self.db.get_user_by_email(email)
            
            if existing_user:
                logger.info(f"User already exists: {email}")
                self.migration_stats['users_updated'] += 1
                return existing_user
            
            # Create new user with default password
            default_password = "AnwaltsAI2024!"  # User should change this
            password_hash = self.auth_service.hash_password(default_password)
            
            user = await self.db.create_user(
                email=email,
                name=name,
                role=role,
                password_hash=password_hash
            )
            
            logger.info(f"Created new user: {email}")
            logger.warning(f"Default password set for {email}: {default_password}")
            self.migration_stats['users_created'] += 1
            
            return user
        except Exception as e:
            logger.error(f"Failed to migrate user: {e}")
            self.migration_stats['errors'] += 1
            raise
    
    async def migrate_templates(self, user: UserInDB, templates: List[Dict[str, Any]]) -> int:
        """Migrate user templates"""
        migrated_count = 0
        
        for template_data in templates:
            try:
                # Validate required fields
                if not all(key in template_data for key in ['name', 'content']):
                    logger.warning(f"Skipping template with missing required fields: {template_data}")
                    continue
                
                # Create template
                template = await self.db.create_template(
                    user_id=user.id,
                    name=template_data['name'],
                    content=template_data['content'],
                    category=template_data.get('category', 'general'),
                    type=template_data.get('type', 'document')
                )
                
                # Update usage count if provided
                if 'usage_count' in template_data and template_data['usage_count'] > 0:
                    for _ in range(template_data['usage_count']):
                        await self.db.increment_template_usage(template.id)
                
                logger.debug(f"Migrated template: {template.name}")
                migrated_count += 1
                
            except Exception as e:
                logger.error(f"Failed to migrate template {template_data.get('name', 'unknown')}: {e}")
                self.migration_stats['errors'] += 1
                continue
        
        self.migration_stats['templates_migrated'] += migrated_count
        logger.info(f"Migrated {migrated_count} templates for user {user.email}")
        return migrated_count
    
    async def migrate_clauses(self, user: UserInDB, clauses: List[Dict[str, Any]]) -> int:
        """Migrate user clauses"""
        migrated_count = 0
        
        for clause_data in clauses:
            try:
                # Validate required fields
                if not all(key in clause_data for key in ['title', 'content', 'category']):
                    logger.warning(f"Skipping clause with missing required fields: {clause_data}")
                    continue
                
                # Create clause
                clause = await self.db.create_clause(
                    user_id=user.id,
                    category=clause_data['category'],
                    title=clause_data['title'],
                    content=clause_data['content'],
                    tags=clause_data.get('tags', []),
                    language=clause_data.get('language', 'de')
                )
                
                logger.debug(f"Migrated clause: {clause.title}")
                migrated_count += 1
                
            except Exception as e:
                logger.error(f"Failed to migrate clause {clause_data.get('title', 'unknown')}: {e}")
                self.migration_stats['errors'] += 1
                continue
        
        self.migration_stats['clauses_migrated'] += migrated_count
        logger.info(f"Migrated {migrated_count} clauses for user {user.email}")
        return migrated_count
    
    async def migrate_clipboard(self, user: UserInDB, clipboard: List[Dict[str, Any]]) -> int:
        """Migrate clipboard entries"""
        migrated_count = 0
        
        for entry_data in clipboard:
            try:
                # Validate required fields
                if 'content' not in entry_data:
                    logger.warning(f"Skipping clipboard entry with missing content: {entry_data}")
                    continue
                
                # Parse expires_at if provided
                expires_at = None
                if 'expires_at' in entry_data:
                    try:
                        expires_at = datetime.fromisoformat(entry_data['expires_at'].replace('Z', '+00:00'))
                    except (ValueError, AttributeError):
                        logger.warning(f"Invalid expires_at format: {entry_data['expires_at']}")
                
                # Create clipboard entry
                entry = await self.db.create_clipboard_entry(
                    user_id=user.id,
                    content=entry_data['content'],
                    source_type=entry_data.get('source_type', 'manual'),
                    metadata=entry_data.get('metadata', {}),
                    expires_at=expires_at
                )
                
                logger.debug(f"Migrated clipboard entry: {entry.id}")
                migrated_count += 1
                
            except Exception as e:
                logger.error(f"Failed to migrate clipboard entry: {e}")
                self.migration_stats['errors'] += 1
                continue
        
        self.migration_stats['clipboard_entries_migrated'] += migrated_count
        logger.info(f"Migrated {migrated_count} clipboard entries for user {user.email}")
        return migrated_count
    
    async def migrate_single_user_data(self, data: Dict[str, Any]) -> bool:
        """Migrate data for a single user"""
        try:
            # Validate data
            if not self.validate_client_data(data):
                return False
            
            # Migrate user
            user = await self.migrate_user(data['user_info'])
            
            # Migrate templates
            await self.migrate_templates(user, data['templates'])
            
            # Migrate clauses
            await self.migrate_clauses(user, data['clauses'])
            
            # Migrate clipboard entries
            await self.migrate_clipboard(user, data['clipboard'])
            
            logger.info(f"Successfully migrated all data for user {user.email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to migrate user data: {e}")
            self.migration_stats['errors'] += 1
            return False
    
    async def migrate_bulk_data(self, data_file: str) -> bool:
        """Migrate bulk data from file"""
        try:
            data = self.load_client_data(data_file)
            
            # Check if it's bulk data (multiple users) or single user data
            if 'users' in data and isinstance(data['users'], list):
                # Bulk data format
                logger.info(f"Migrating bulk data for {len(data['users'])} users")
                
                for user_data in data['users']:
                    await self.migrate_single_user_data(user_data)
            else:
                # Single user data format
                logger.info("Migrating single user data")
                await self.migrate_single_user_data(data)
            
            return True
            
        except Exception as e:
            logger.error(f"Bulk migration failed: {e}")
            return False
    
    def print_migration_stats(self):
        """Print migration statistics"""
        logger.info("=== Migration Statistics ===")
        for key, value in self.migration_stats.items():
            logger.info(f"{key.replace('_', ' ').title()}: {value}")
        logger.info("============================")
    
    async def create_sample_migration_file(self, output_file: str):
        """Create a sample migration file for reference"""
        sample_data = {
            "user_info": {
                "email": "example@law-firm.com",
                "name": "Dr. Max Mustermann",
                "role": "assistant"
            },
            "templates": [
                {
                    "name": "Standard Mietvertrag",
                    "content": "Mietvertrag zwischen {{landlord}} und {{tenant}}...",
                    "category": "Mietrecht",
                    "type": "document",
                    "usage_count": 5
                },
                {
                    "name": "Kündigungsschreiben",
                    "content": "Hiermit kündige ich das Mietverhältnis zum {{date}}...",
                    "category": "Mietrecht",
                    "type": "document",
                    "usage_count": 2
                }
            ],
            "clauses": [
                {
                    "category": "Haftungsausschluss",
                    "title": "Standard Haftungsausschluss",
                    "content": "Der Auftragnehmer haftet nur für Schäden...",
                    "tags": ["Haftung", "Standard", "Vertragsrecht"],
                    "language": "de"
                },
                {
                    "category": "Datenschutz",
                    "title": "DSGVO Klausel",
                    "content": "Die Verarbeitung personenbezogener Daten erfolgt...",
                    "tags": ["DSGVO", "Datenschutz", "Privacy"],
                    "language": "de"
                }
            ],
            "clipboard": [
                {
                    "content": "Wichtiger Vertragstext für späteren Gebrauch",
                    "source_type": "manual",
                    "metadata": {
                        "category": "Vertragsrecht",
                        "priority": "high"
                    }
                },
                {
                    "content": "AI-generierter Klauseltext",
                    "source_type": "ai_generated",
                    "metadata": {
                        "model": "llama-2-7b",
                        "prompt": "Generate liability clause"
                    },
                    "expires_at": "2024-12-31T23:59:59Z"
                }
            ]
        }
        
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(sample_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Sample migration file created: {output_file}")
            logger.info("Edit this file with your actual data and run the migration")
            
        except Exception as e:
            logger.error(f"Failed to create sample file: {e}")

async def main():
    """Main migration function"""
    parser = argparse.ArgumentParser(
        description="Migrate AnwaltsAI client data to PostgreSQL database"
    )
    parser.add_argument(
        "action",
        choices=["migrate", "sample"],
        help="Action to perform: migrate data or create sample file"
    )
    parser.add_argument(
        "--file",
        default="client_data.json",
        help="JSON file containing client data (default: client_data.json)"
    )
    parser.add_argument(
        "--output",
        default="sample_migration.json",
        help="Output file for sample data (default: sample_migration.json)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Perform a dry run without making changes"
    )
    
    args = parser.parse_args()
    
    migrator = ClientDataMigrator()
    
    try:
        if args.action == "sample":
            await migrator.create_sample_migration_file(args.output)
            return
        
        # Initialize database connection
        await migrator.initialize()
        
        if args.dry_run:
            logger.info("DRY RUN MODE - No changes will be made")
            # In dry run, we would validate data without making changes
            data = migrator.load_client_data(args.file)
            is_valid = migrator.validate_client_data(data)
            
            if is_valid:
                logger.info("Data validation passed - ready for migration")
            else:
                logger.error("Data validation failed - fix errors before migration")
                return 1
        else:
            # Perform actual migration
            success = await migrator.migrate_bulk_data(args.file)
            
            if success:
                migrator.print_migration_stats()
                logger.info("Migration completed successfully")
                
                # Print important information
                if migrator.migration_stats['users_created'] > 0:
                    logger.warning("IMPORTANT: Default passwords were set for new users!")
                    logger.warning("Users should change their passwords after first login.")
                    logger.warning("Default password: AnwaltsAI2024!")
                
                return 0
            else:
                logger.error("Migration failed")
                migrator.print_migration_stats()
                return 1
    
    except KeyboardInterrupt:
        logger.info("Migration cancelled by user")
        return 1
    except Exception as e:
        logger.error(f"Migration error: {e}")
        return 1
    finally:
        await migrator.cleanup()

if __name__ == "__main__":
    # Set up environment variables if not already set
    if "DATABASE_URL" not in os.environ:
        os.environ["DATABASE_URL"] = "postgresql://postgres:postgres@localhost:5432/anwalts_ai"
    
    # Run the migration
    exit_code = asyncio.run(main())
    sys.exit(exit_code)