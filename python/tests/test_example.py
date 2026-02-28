"""Quick smoke test for the example app."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from example.complete_example import app
from sufast.testclient import TestClient

client = TestClient(app)

r = client.get("/")
print("Home:", r.status_code, r.json())

r = client.get("/api/users")
data = r.json()
print("Users:", r.status_code, "-", data["total"], "users")

r = client.post("/api/users", json_data={"name": "Dave", "email": "dave@test.com"})
print("Create User:", r.status_code, r.json())

r = client.get("/api/products")
data = r.json()
print("Products:", r.status_code, "-", len(data["products"]), "products")

r = client.get("/docs")
print("Swagger UI:", r.status_code, "-", len(r.text), "bytes")

r = client.get("/health")
print("Health:", r.status_code, r.json())

r = client.get("/html")
print("HTML:", r.status_code, "-", len(r.text), "bytes")

r = client.get("/text")
print("Text:", r.status_code, "-", r.text[:50])

r = client.get("/sync")
print("Sync:", r.status_code, r.json())

r = client.delete("/api/users/1")
print("Delete:", r.status_code, r.json())

r = client.get("/openapi.json")
spec = r.json()
paths = list(spec.get("paths", {}).keys())
print("OpenAPI paths:", len(paths))
for p in sorted(paths):
    print("  ", p)

print()
print("Example app smoke test passed!")
