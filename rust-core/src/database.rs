// Database integration with SQLite support

use std::collections::HashMap;
use std::sync::Arc;
use sqlx::{SqlitePool, Row};
use serde_json::Value;
use async_trait::async_trait;

#[derive(Debug, Clone)]
pub struct DatabasePool {
    pool: SqlitePool,
}

impl DatabasePool {
    pub async fn new(database_url: &str) -> Result<Self, DatabaseError> {
        let pool = SqlitePool::connect(database_url).await
            .map_err(DatabaseError::ConnectionError)?;
        
        Ok(Self { pool })
    }
    
    pub async fn execute_query(&self, query: &str, params: &[Value]) -> Result<Vec<HashMap<String, Value>>, DatabaseError> {
        let mut query_builder = sqlx::query(query);
        
        // Bind parameters
        for param in params {
            query_builder = match param {
                Value::String(s) => query_builder.bind(s),
                Value::Number(n) => {
                    if let Some(i) = n.as_i64() {
                        query_builder.bind(i)
                    } else if let Some(f) = n.as_f64() {
                        query_builder.bind(f)
                    } else {
                        query_builder.bind(n.to_string())
                    }
                }
                Value::Bool(b) => query_builder.bind(*b),
                Value::Null => query_builder.bind(None::<String>),
                _ => query_builder.bind(param.to_string()),
            };
        }
        
        let rows = query_builder.fetch_all(&self.pool).await
            .map_err(DatabaseError::QueryError)?;
        
        let mut results = Vec::new();
        for row in rows {
            let mut record = HashMap::new();
            
            for (i, column) in row.columns().iter().enumerate() {
                let column_name = column.name().to_string();
                let value = self.extract_value(&row, i)?;
                record.insert(column_name, value);
            }
            
            results.push(record);
        }
        
        Ok(results)
    }
    
    pub async fn execute_non_query(&self, query: &str, params: &[Value]) -> Result<u64, DatabaseError> {
        let mut query_builder = sqlx::query(query);
        
        for param in params {
            query_builder = match param {
                Value::String(s) => query_builder.bind(s),
                Value::Number(n) => {
                    if let Some(i) = n.as_i64() {
                        query_builder.bind(i)
                    } else if let Some(f) = n.as_f64() {
                        query_builder.bind(f)
                    } else {
                        query_builder.bind(n.to_string())
                    }
                }
                Value::Bool(b) => query_builder.bind(*b),
                Value::Null => query_builder.bind(None::<String>),
                _ => query_builder.bind(param.to_string()),
            };
        }
        
        let result = query_builder.execute(&self.pool).await
            .map_err(DatabaseError::QueryError)?;
        
        Ok(result.rows_affected())
    }
    
    fn extract_value(&self, row: &sqlx::sqlite::SqliteRow, index: usize) -> Result<Value, DatabaseError> {
        let column = &row.columns()[index];
        
        match column.type_info().name() {
            "TEXT" => {
                let value: Option<String> = row.try_get(index)
                    .map_err(|e| DatabaseError::ConversionError(e.to_string()))?;
                Ok(value.map(Value::String).unwrap_or(Value::Null))
            }
            "INTEGER" => {
                let value: Option<i64> = row.try_get(index)
                    .map_err(|e| DatabaseError::ConversionError(e.to_string()))?;
                Ok(value.map(|v| Value::Number(v.into())).unwrap_or(Value::Null))
            }
            "REAL" => {
                let value: Option<f64> = row.try_get(index)
                    .map_err(|e| DatabaseError::ConversionError(e.to_string()))?;
                Ok(value.map(|v| Value::Number(serde_json::Number::from_f64(v).unwrap_or_else(|| 0.into()))).unwrap_or(Value::Null))
            }
            "BOOLEAN" => {
                let value: Option<bool> = row.try_get(index)
                    .map_err(|e| DatabaseError::ConversionError(e.to_string()))?;
                Ok(value.map(Value::Bool).unwrap_or(Value::Null))
            }
            _ => {
                // Default to string for unknown types
                let value: Option<String> = row.try_get(index)
                    .map_err(|e| DatabaseError::ConversionError(e.to_string()))?;
                Ok(value.map(Value::String).unwrap_or(Value::Null))
            }
        }
    }
    
    pub async fn create_table(&self, table_name: &str, columns: &[ColumnDefinition]) -> Result<(), DatabaseError> {
        let mut query = format!("CREATE TABLE IF NOT EXISTS {} (", table_name);
        
        let column_defs: Vec<String> = columns.iter().map(|col| {
            let mut def = format!("{} {}", col.name, col.data_type);
            
            if col.primary_key {
                def.push_str(" PRIMARY KEY");
            }
            if col.auto_increment {
                def.push_str(" AUTOINCREMENT");
            }
            if col.not_null {
                def.push_str(" NOT NULL");
            }
            if let Some(ref default) = col.default_value {
                def.push_str(&format!(" DEFAULT {}", default));
            }
            if col.unique {
                def.push_str(" UNIQUE");
            }
            
            def
        }).collect();
        
        query.push_str(&column_defs.join(", "));
        query.push(')');
        
        self.execute_non_query(&query, &[]).await?;
        Ok(())
    }
    
    pub async fn get_table_info(&self, table_name: &str) -> Result<Vec<ColumnInfo>, DatabaseError> {
        let query = format!("PRAGMA table_info({})", table_name);
        let rows = self.execute_query(&query, &[]).await?;
        
        let mut columns = Vec::new();
        for row in rows {
            let column = ColumnInfo {
                name: row.get("name").and_then(|v| v.as_str()).unwrap_or("").to_string(),
                data_type: row.get("type").and_then(|v| v.as_str()).unwrap_or("").to_string(),
                not_null: row.get("notnull").and_then(|v| v.as_bool()).unwrap_or(false),
                default_value: row.get("dflt_value").cloned(),
                primary_key: row.get("pk").and_then(|v| v.as_i64()).unwrap_or(0) > 0,
            };
            columns.push(column);
        }
        
        Ok(columns)
    }
}

#[derive(Debug, Clone)]
pub struct ColumnDefinition {
    pub name: String,
    pub data_type: String,
    pub primary_key: bool,
    pub auto_increment: bool,
    pub not_null: bool,
    pub unique: bool,
    pub default_value: Option<String>,
}

impl ColumnDefinition {
    pub fn new(name: &str, data_type: &str) -> Self {
        Self {
            name: name.to_string(),
            data_type: data_type.to_string(),
            primary_key: false,
            auto_increment: false,
            not_null: false,
            unique: false,
            default_value: None,
        }
    }
    
    pub fn primary_key(mut self) -> Self {
        self.primary_key = true;
        self.not_null = true;
        self
    }
    
    pub fn auto_increment(mut self) -> Self {
        self.auto_increment = true;
        self
    }
    
    pub fn not_null(mut self) -> Self {
        self.not_null = true;
        self
    }
    
    pub fn unique(mut self) -> Self {
        self.unique = true;
        self
    }
    
    pub fn default_value(mut self, value: &str) -> Self {
        self.default_value = Some(value.to_string());
        self
    }
}

#[derive(Debug, Clone)]
pub struct ColumnInfo {
    pub name: String,
    pub data_type: String,
    pub not_null: bool,
    pub default_value: Option<Value>,
    pub primary_key: bool,
}

// Migration system
#[derive(Debug, Clone)]
pub struct Migration {
    pub id: String,
    pub description: String,
    pub up_sql: String,
    pub down_sql: String,
}

impl Migration {
    pub fn new(id: &str, description: &str) -> Self {
        Self {
            id: id.to_string(),
            description: description.to_string(),
            up_sql: String::new(),
            down_sql: String::new(),
        }
    }
    
    pub fn up(mut self, sql: &str) -> Self {
        self.up_sql = sql.to_string();
        self
    }
    
    pub fn down(mut self, sql: &str) -> Self {
        self.down_sql = sql.to_string();
        self
    }
}

pub struct MigrationRunner {
    pool: Arc<DatabasePool>,
}

impl MigrationRunner {
    pub fn new(pool: Arc<DatabasePool>) -> Self {
        Self { pool }
    }
    
    pub async fn init(&self) -> Result<(), DatabaseError> {
        let migrations_table = vec![
            ColumnDefinition::new("id", "TEXT").primary_key(),
            ColumnDefinition::new("description", "TEXT").not_null(),
            ColumnDefinition::new("applied_at", "DATETIME").not_null().default_value("CURRENT_TIMESTAMP"),
        ];
        
        self.pool.create_table("migrations", &migrations_table).await?;
        Ok(())
    }
    
    pub async fn run_migration(&self, migration: &Migration) -> Result<(), DatabaseError> {
        // Check if migration already applied
        let existing = self.pool.execute_query(
            "SELECT id FROM migrations WHERE id = ?",
            &[Value::String(migration.id.clone())]
        ).await?;
        
        if !existing.is_empty() {
            return Ok(()); // Already applied
        }
        
        // Run the migration
        self.pool.execute_non_query(&migration.up_sql, &[]).await?;
        
        // Record the migration
        self.pool.execute_non_query(
            "INSERT INTO migrations (id, description) VALUES (?, ?)",
            &[
                Value::String(migration.id.clone()),
                Value::String(migration.description.clone())
            ]
        ).await?;
        
        Ok(())
    }
    
    pub async fn rollback_migration(&self, migration: &Migration) -> Result<(), DatabaseError> {
        // Run the rollback
        self.pool.execute_non_query(&migration.down_sql, &[]).await?;
        
        // Remove from migrations table
        self.pool.execute_non_query(
            "DELETE FROM migrations WHERE id = ?",
            &[Value::String(migration.id.clone())]
        ).await?;
        
        Ok(())
    }
    
    pub async fn get_applied_migrations(&self) -> Result<Vec<String>, DatabaseError> {
        let rows = self.pool.execute_query(
            "SELECT id FROM migrations ORDER BY applied_at",
            &[]
        ).await?;
        
        Ok(rows.into_iter()
            .filter_map(|row| row.get("id")?.as_str().map(|s| s.to_string()))
            .collect())
    }
}

#[derive(Debug, thiserror::Error)]
pub enum DatabaseError {
    #[error("Connection error: {0}")]
    ConnectionError(#[from] sqlx::Error),
    #[error("Query error: {0}")]
    QueryError(sqlx::Error),
    #[error("Conversion error: {0}")]
    ConversionError(String),
    #[error("Migration error: {0}")]
    MigrationError(String),
}

#[cfg(test)]
mod tests {
    use super::*;
    use tempfile::tempdir;

    #[tokio::test]
    async fn test_database_basic_operations() {
        let temp_dir = tempdir().unwrap();
        let db_path = temp_dir.path().join("test.db");
        let db_url = format!("sqlite://{}", db_path.display());
        
        let pool = DatabasePool::new(&db_url).await.unwrap();
        
        // Create a test table
        let columns = vec![
            ColumnDefinition::new("id", "INTEGER").primary_key().auto_increment(),
            ColumnDefinition::new("name", "TEXT").not_null(),
            ColumnDefinition::new("email", "TEXT").unique(),
        ];
        
        pool.create_table("users", &columns).await.unwrap();
        
        // Insert data
        let rows_affected = pool.execute_non_query(
            "INSERT INTO users (name, email) VALUES (?, ?)",
            &[Value::String("John".to_string()), Value::String("john@example.com".to_string())]
        ).await.unwrap();
        
        assert_eq!(rows_affected, 1);
        
        // Query data
        let results = pool.execute_query("SELECT * FROM users", &[]).await.unwrap();
        assert_eq!(results.len(), 1);
        assert_eq!(results[0].get("name").unwrap().as_str().unwrap(), "John");
    }

    #[tokio::test]
    async fn test_migration_system() {
        let temp_dir = tempdir().unwrap();
        let db_path = temp_dir.path().join("test_migrations.db");
        let db_url = format!("sqlite://{}", db_path.display());
        
        let pool = Arc::new(DatabasePool::new(&db_url).await.unwrap());
        let runner = MigrationRunner::new(pool);
        
        runner.init().await.unwrap();
        
        let migration = Migration::new("001", "Create users table")
            .up("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT NOT NULL)")
            .down("DROP TABLE users");
        
        runner.run_migration(&migration).await.unwrap();
        
        let applied = runner.get_applied_migrations().await.unwrap();
        assert_eq!(applied, vec!["001"]);
    }
}
