"""
Database integration for Sufast framework.
"""
import sqlite3
import json
from typing import Dict, Any, List, Optional, Union, Type
from pathlib import Path
from dataclasses import dataclass, fields
from abc import ABC, abstractmethod


class DatabaseConnection(ABC):
    """Abstract database connection."""
    
    @abstractmethod
    def execute(self, query: str, params: tuple = None) -> Any:
        pass
    
    @abstractmethod
    def fetchone(self, query: str, params: tuple = None) -> Optional[Dict[str, Any]]:
        pass
    
    @abstractmethod
    def fetchall(self, query: str, params: tuple = None) -> List[Dict[str, Any]]:
        pass
    
    @abstractmethod
    def close(self):
        pass


class SQLiteConnection(DatabaseConnection):
    """SQLite database connection."""
    
    def __init__(self, database_path: str):
        self.database_path = database_path
        self.conn = sqlite3.connect(database_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row  # Enable dict-like access
    
    def execute(self, query: str, params: tuple = None) -> sqlite3.Cursor:
        """Execute query and return cursor."""
        cursor = self.conn.cursor()
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        self.conn.commit()
        return cursor
    
    def fetchone(self, query: str, params: tuple = None) -> Optional[Dict[str, Any]]:
        """Fetch single row as dictionary."""
        cursor = self.execute(query, params)
        row = cursor.fetchone()
        return dict(row) if row else None
    
    def fetchall(self, query: str, params: tuple = None) -> List[Dict[str, Any]]:
        """Fetch all rows as list of dictionaries."""
        cursor = self.execute(query, params)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    
    def close(self):
        """Close database connection."""
        self.conn.close()


class Model:
    """Base model class for database entities."""
    
    _db: Optional[DatabaseConnection] = None
    _table_name: Optional[str] = None
    
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
    
    @classmethod
    def set_db(cls, db: DatabaseConnection):
        """Set database connection for all models."""
        cls._db = db
    
    @classmethod
    def table_name(cls) -> str:
        """Get table name for model."""
        if cls._table_name:
            return cls._table_name
        return cls.__name__.lower() + 's'
    
    @classmethod
    def create_table(cls):
        """Create table for model."""
        if not cls._db:
            raise RuntimeError("Database not connected")
        
        # Get model fields from dataclass or annotations
        if hasattr(cls, '__dataclass_fields__'):
            field_definitions = []
            for field_name, field_info in cls.__dataclass_fields__.items():
                sql_type = cls._python_to_sql_type(field_info.type)
                field_definitions.append(f"{field_name} {sql_type}")
        else:
            # Basic table with id
            field_definitions = ["id INTEGER PRIMARY KEY AUTOINCREMENT"]
        
        fields_sql = ", ".join(field_definitions)
        query = f"CREATE TABLE IF NOT EXISTS {cls.table_name()} ({fields_sql})"
        cls._db.execute(query)
    
    @classmethod
    def _python_to_sql_type(cls, python_type) -> str:
        """Convert Python type to SQL type."""
        type_mapping = {
            int: "INTEGER",
            str: "TEXT",
            float: "REAL",
            bool: "INTEGER",
            bytes: "BLOB"
        }
        
        # Handle Optional types
        if hasattr(python_type, '__origin__') and python_type.__origin__ is Union:
            args = python_type.__args__
            if len(args) == 2 and type(None) in args:
                non_none_type = args[0] if args[1] is type(None) else args[1]
                return type_mapping.get(non_none_type, "TEXT")
        
        return type_mapping.get(python_type, "TEXT")
    
    @classmethod
    def find(cls, id: Union[int, str]) -> Optional['Model']:
        """Find record by ID."""
        if not cls._db:
            raise RuntimeError("Database not connected")
        
        query = f"SELECT * FROM {cls.table_name()} WHERE id = ?"
        row = cls._db.fetchone(query, (id,))
        return cls(**row) if row else None
    
    @classmethod
    def all(cls) -> List['Model']:
        """Get all records."""
        if not cls._db:
            raise RuntimeError("Database not connected")
        
        query = f"SELECT * FROM {cls.table_name()}"
        rows = cls._db.fetchall(query)
        return [cls(**row) for row in rows]
    
    @classmethod
    def where(cls, **conditions) -> List['Model']:
        """Find records by conditions."""
        if not cls._db:
            raise RuntimeError("Database not connected")
        
        if not conditions:
            return cls.all()
        
        where_clauses = []
        params = []
        for key, value in conditions.items():
            where_clauses.append(f"{key} = ?")
            params.append(value)
        
        where_sql = " AND ".join(where_clauses)
        query = f"SELECT * FROM {cls.table_name()} WHERE {where_sql}"
        rows = cls._db.fetchall(query, tuple(params))
        return [cls(**row) for row in rows]
    
    @classmethod
    def create(cls, **data) -> 'Model':
        """Create new record."""
        if not cls._db:
            raise RuntimeError("Database not connected")
        
        fields = list(data.keys())
        values = list(data.values())
        placeholders = ", ".join(["?"] * len(values))
        fields_sql = ", ".join(fields)
        
        query = f"INSERT INTO {cls.table_name()} ({fields_sql}) VALUES ({placeholders})"
        cursor = cls._db.execute(query, tuple(values))
        
        # Get the created record
        data['id'] = cursor.lastrowid
        return cls(**data)
    
    def save(self) -> 'Model':
        """Save record (insert or update)."""
        if not self._db:
            raise RuntimeError("Database not connected")
        
        data = self.to_dict()
        
        if hasattr(self, 'id') and self.id:
            # Update existing record
            fields = [f"{key} = ?" for key in data.keys() if key != 'id']
            values = [value for key, value in data.items() if key != 'id']
            fields_sql = ", ".join(fields)
            
            query = f"UPDATE {self.table_name()} SET {fields_sql} WHERE id = ?"
            self._db.execute(query, tuple(values + [self.id]))
        else:
            # Insert new record
            fields = [key for key in data.keys() if key != 'id']
            values = [data[key] for key in fields]
            placeholders = ", ".join(["?"] * len(values))
            fields_sql = ", ".join(fields)
            
            query = f"INSERT INTO {self.table_name()} ({fields_sql}) VALUES ({placeholders})"
            cursor = self._db.execute(query, tuple(values))
            self.id = cursor.lastrowid
        
        return self
    
    def delete(self):
        """Delete record."""
        if not self._db:
            raise RuntimeError("Database not connected")
        
        if not hasattr(self, 'id') or not self.id:
            raise ValueError("Cannot delete record without ID")
        
        query = f"DELETE FROM {self.table_name()} WHERE id = ?"
        self._db.execute(query, (self.id,))
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary."""
        if hasattr(self, '__dataclass_fields__'):
            return {field.name: getattr(self, field.name) 
                   for field in fields(self)}
        else:
            return {key: value for key, value in self.__dict__.items() 
                   if not key.startswith('_')}
    
    def to_json(self) -> str:
        """Convert model to JSON."""
        return json.dumps(self.to_dict(), default=str)


class Database:
    """Database manager."""
    
    def __init__(self, connection: DatabaseConnection):
        self.connection = connection
        Model.set_db(connection)
    
    def create_tables(self, models: List[Type[Model]]):
        """Create tables for given models."""
        for model in models:
            model.create_table()
    
    def execute_migration(self, migration_sql: str):
        """Execute migration SQL."""
        self.connection.execute(migration_sql)
    
    def close(self):
        """Close database connection."""
        self.connection.close()


class Migration:
    """Database migration."""
    
    def __init__(self, name: str, up_sql: str, down_sql: str = None):
        self.name = name
        self.up_sql = up_sql
        self.down_sql = down_sql or ""
    
    def up(self, db: Database):
        """Apply migration."""
        db.execute_migration(self.up_sql)
    
    def down(self, db: Database):
        """Rollback migration."""
        if self.down_sql:
            db.execute_migration(self.down_sql)


class MigrationManager:
    """Manages database migrations."""
    
    def __init__(self, db: Database, migrations_dir: str = "migrations"):
        self.db = db
        self.migrations_dir = Path(migrations_dir)
        self.migrations: List[Migration] = []
        self._create_migrations_table()
    
    def _create_migrations_table(self):
        """Create migrations tracking table."""
        query = """
        CREATE TABLE IF NOT EXISTS migrations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        self.db.execute_migration(query)
    
    def add_migration(self, migration: Migration):
        """Add migration to manager."""
        self.migrations.append(migration)
    
    def get_applied_migrations(self) -> List[str]:
        """Get list of applied migration names."""
        query = "SELECT name FROM migrations ORDER BY applied_at"
        rows = self.db.connection.fetchall(query)
        return [row['name'] for row in rows]
    
    def migrate(self):
        """Apply pending migrations."""
        applied = set(self.get_applied_migrations())
        
        for migration in self.migrations:
            if migration.name not in applied:
                print(f"Applying migration: {migration.name}")
                migration.up(self.db)
                
                # Record migration as applied
                query = "INSERT INTO migrations (name) VALUES (?)"
                self.db.execute_migration(query)
                self.db.connection.execute(query, (migration.name,))
    
    def rollback(self, migration_name: str):
        """Rollback specific migration."""
        # Find migration
        migration = next((m for m in self.migrations if m.name == migration_name), None)
        if not migration:
            raise ValueError(f"Migration {migration_name} not found")
        
        print(f"Rolling back migration: {migration_name}")
        migration.down(self.db)
        
        # Remove from applied migrations
        query = "DELETE FROM migrations WHERE name = ?"
        self.db.connection.execute(query, (migration_name,))


# Example usage:
"""
@dataclass
class User(Model):
    id: Optional[int] = None
    username: str = ""
    email: str = ""
    created_at: Optional[str] = None

# Setup database
db_conn = SQLiteConnection("app.db")
db = Database(db_conn)

# Create tables
db.create_tables([User])

# Use model
user = User.create(username="john", email="john@example.com")
all_users = User.all()
john = User.find(1)
"""
