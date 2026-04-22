from sufast import App

# Use debug mode so local dev runs on Python server
# and responds cleanly to Ctrl+C on Windows terminals.
app = App(debug=True)

# Sample data
users = {
    "1": {"name": "Alice", "email": "alice@example.com"},
    "2": {"name": "Bob", "email": "bob@example.com"},
    "3": {"name": "Charlie", "email": "charlie@example.com"},
    "4": {"name": "Diana", "email": "diana@example.com"},
    "5": {"name": "Eve", "email": "eve@example.com"}
}

@app.get("/")
def home():
    return {"message": "Welcome to Sufast API 🚀"}

@app.get("/users")
def get_users():
    return {"users": list(users.values())}

@app.get("/users/{user_id}")
def get_user(user_id: str):
    if user_id in users:
        return {"user": users[user_id]}
    return {"error": "User not found"}, 404

@app.post("/users")
def create_user():
    return {"message": "User created", "status_code": 201}

if __name__ == "__main__":
    app.run(debug=True)