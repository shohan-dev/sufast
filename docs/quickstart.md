# Quick Start Guide

Get up and running with Sufast in 5 minutes!

## Installation

```bash
pip install sufast
```

## Your First App

Create a file called `app.py`:

```python
from sufast import App

app = App()

@app.get("/")
def hello():
    return {"message": "Hello, World!"}

@app.get("/user/{name}")
def greet_user():
    return {"greeting": "Hello, {name}!"}

if __name__ == "__main__":
    app.run(port=8080)
```

Run it:

```bash
python app.py
```

Visit: http://localhost:8080

## Key Concepts

### Routes

Sufast uses decorators to define routes:

```python
@app.get("/path")       # GET requests
@app.post("/path")      # POST requests
@app.put("/path")       # PUT requests
@app.patch("/path")     # PATCH requests
@app.delete("/path")    # DELETE requests
```

### Dynamic Routes

Use `{parameter}` syntax for dynamic routes:

```python
@app.get("/users/{user_id}")
def get_user():
    return {"user_id": "{user_id}"}  # Will be replaced at runtime

@app.get("/posts/{post_id}/comments/{comment_id}")
def get_comment():
    return {
        "post": "{post_id}",
        "comment": "{comment_id}"
    }
```

### Response Types

Return any JSON-serializable data:

```python
@app.get("/string")
def string_response():
    return "Hello World"

@app.get("/dict")
def dict_response():
    return {"key": "value"}

@app.get("/list")
def list_response():
    return [1, 2, 3, 4, 5]

@app.get("/complex")
def complex_response():
    return {
        "users": [
            {"id": 1, "name": "Alice"},
            {"id": 2, "name": "Bob"}
        ],
        "metadata": {
            "total": 2,
            "page": 1
        }
    }
```

## Real-World Example

```python
from sufast import App

app = App()

# Sample data
users_db = {
    "1": {"id": 1, "name": "Alice Johnson", "email": "alice@example.com"},
    "2": {"id": 2, "name": "Bob Smith", "email": "bob@example.com"},
    "3": {"id": 3, "name": "Carol Brown", "email": "carol@example.com"},
}

posts_db = {
    "1": {"id": 1, "title": "Hello World", "author_id": 1, "content": "First post!"},
    "2": {"id": 2, "title": "Python Tips", "author_id": 2, "content": "Use f-strings!"},
}

# API Routes
@app.get("/")
def home():
    return {
        "message": "Welcome to Sufast API",
        "version": "1.0.0",
        "endpoints": ["/users", "/users/{id}", "/posts", "/posts/{id}"]
    }

@app.get("/health")
def health_check():
    return {"status": "healthy", "timestamp": "2024-01-01T00:00:00Z"}

@app.get("/users")
def get_all_users():
    return {
        "users": list(users_db.values()),
        "count": len(users_db)
    }

@app.get("/users/{user_id}")
def get_user():
    return {
        "user": users_db.get("{user_id}", {"error": "User not found"}),
        "requested_id": "{user_id}"
    }

@app.get("/posts")
def get_all_posts():
    return {
        "posts": list(posts_db.values()),
        "count": len(posts_db)
    }

@app.get("/posts/{post_id}")
def get_post():
    return {
        "post": posts_db.get("{post_id}", {"error": "Post not found"}),
        "requested_id": "{post_id}"
    }

@app.get("/users/{user_id}/posts")
def get_user_posts():
    user_posts = [
        post for post in posts_db.values() 
        if str(post["author_id"]) == "{user_id}"
    ]
    return {
        "user_id": "{user_id}",
        "posts": user_posts,
        "count": len(user_posts)
    }

# Mock POST endpoints (responses are pre-computed)
@app.post("/users")
def create_user():
    return {
        "message": "User would be created",
        "user": {"id": 4, "name": "New User", "email": "new@example.com"}
    }

@app.post("/posts")
def create_post():
    return {
        "message": "Post would be created",
        "post": {"id": 3, "title": "New Post", "author_id": 1}
    }

if __name__ == "__main__":
    app.run(port=8080, production=False)
```

## Configuration Options

### Development vs Production

```python
# Development mode (default)
app.run(port=8080, production=False)
# - Binds to localhost only
# - Shows detailed startup messages
# - Includes helpful URLs

# Production mode
app.run(port=8080, production=True)
# - Binds to all interfaces (0.0.0.0)
# - Minimal startup messages
# - Optimized for deployment
```

### Custom Ports

```python
app.run(port=3000)    # Custom port
app.run(port=80)      # Standard HTTP port (requires admin on some systems)
app.run(port=443)     # Standard HTTPS port (requires admin on some systems)
```

## Performance Tips

1. **Pre-compute Responses**: Sufast executes handlers once and stores the results
2. **Keep Handlers Simple**: Complex logic should be in separate functions
3. **Use Static Data**: Since responses are pre-computed, use static or computed data
4. **Minimize Dependencies**: Fewer imports = faster startup

## Error Handling

Sufast automatically catches and handles handler errors:

```python
@app.get("/error")
def error_handler():
    raise ValueError("Something went wrong!")
    # Returns: {"error": "⚠️ Handler error for GET /error: Something went wrong!"}

@app.get("/divide")
def divide_by_zero():
    return {"result": 1 / 0}
    # Returns: {"error": "⚠️ Handler error for GET /divide: division by zero"}
```

## Next Steps

- Read the [API Reference](api.md) for detailed documentation
- Check out [Performance Guide](performance.md) for optimization tips
- See [Examples](examples/) for more complex use cases
- Learn about [Architecture](architecture.md) to understand how it works

## Common Patterns

### API Versioning

```python
@app.get("/api/v1/users")
def users_v1():
    return {"version": "1.0", "users": []}

@app.get("/api/v2/users")
def users_v2():
    return {"version": "2.0", "users": [], "metadata": {}}
```

### Resource Collections

```python
@app.get("/api/users")
def list_users():
    return {"users": users_db}

@app.get("/api/users/{id}")
def get_user():
    return {"user": "User {id}"}

@app.post("/api/users")
def create_user():
    return {"created": True}

@app.put("/api/users/{id}")
def update_user():
    return {"updated": True, "id": "{id}"}

@app.delete("/api/users/{id}")
def delete_user():
    return {"deleted": True, "id": "{id}"}
```

### Nested Resources

```python
@app.get("/companies/{company_id}/employees")
def company_employees():
    return {"company": "{company_id}", "employees": []}

@app.get("/companies/{company_id}/employees/{employee_id}")
def company_employee():
    return {
        "company": "{company_id}",
        "employee": "{employee_id}"
    }
```

Happy coding with Sufast! 🚀
