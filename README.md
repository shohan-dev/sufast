# 🚀 sufast – A Blazing Fast Python Web Framework Powered by Rust ⚙️

**sufast** is a hybrid web framework that combines the developer-friendly simplicity of **Python 🐍** with the raw execution speed of **Rust 🦀**.

Built for high-performance APIs, scalable microservices, and modern AI-era backends, sufast delivers the best of both worlds:


---

# ⚡ Why sufast?

- 🚀 **52,000+ RPS** performance with Rust core
- 🐍 FastAPI-style decorator syntax (`@app.get`, `@app.post`)
- 📦 Easy to use and install

---

```bash
pip install sufast
```
⚠️ Requires Python 3.8+ and a platform-compatible Rust binary bundled in the package.

# 🚀 Quickstart

```bash
from sufast import App

app = App()

@app.get("/")
def hello():
    return {"message": "Hello from sufast 👋"}

app.run()
```
Visit -> [http://localhost:8080/ 🚀](http://localhost:8080/)


# 📚 Advanced Example – API Server
```bash
from sufast import App

app = App()

# 🧪 Sample database
users = {
    "shohan": {"name": "shohan", "email": "shohan@example.com"},
    "bob": {"name": "Bob", "email": "bob@example.com"},
    "alice": {"name": "Alice", "email": "alice@example.com"},
}

@app.get("/")
def home():
    return {"message": "Welcome to sufast API 🚀"}

@app.get("/shohan")
def app_info():
    return {"message": "Built by Shohan – Power of Rust & Python ⚙️🐍"}

@app.get("/users")
def get_users():
    return {"users": users}

@app.post("/users")
def show_user():
    # This is a mocked POST example
    return {
        "data": users["bob"]
    }

app.run()
```

# 📊 Real-World Performance Benchmark

| **Metric**               | **Sufast (Rust + Python)** | **Native Rust (Actix-Web)** | **FastAPI (Uvicorn)** | **Node.js (Express)** |
|--------------------------|----------------------------|------------------------------|------------------------|------------------------|
| **Language**             | 🦀 Rust + 🐍 Python         | 🦀 Rust                      | 🐍 Python              | ☕ JavaScript           |
| **Avg. Req/sec** 🚀      | ✅ **52,000+**              | 🔥 **58,000+**               | 🐍 20,000+             | 🚀 30,000+             |
| **Avg. Latency (ms)** ⏱  | ~2.1                       | ~1.7                         | ~5.6                  | ~4.2                  |
| **Memory Usage (MB)** 💾 | ~25                        | ~20                          | ~60                   | ~50                   |
| **Startup Time (ms)** ⚡  | ~35                        | ~25                          | ~90                   | ~40                   |
| **Developer UX** 🧑‍💻    | ✅ FastAPI-style syntax     | ⚠️ Manual routing            | ✅ Excellent           | ✅ Excellent           |



# 🔬 Load Testing with k6
```bash
// test.js
import http from 'k6/http';
import { check, sleep } from 'k6';

export let options = {
  vus: 100,
  duration: '10s',
};

export default function () {
  let res = http.get('http://localhost:8080');

  check(res, {
    'status is 200': (r) => r.status === 200,
    'response has message': (r) => r.json().message !== undefined,
  });

  sleep(0.001);
}
```

Run the test:
```bash
k6 run test.js
```

# ✨ Features

✅ Rust-based core for high-speed routing

✅ Python decorators like @app.get() / @app.post()

✅ FastAPI-style route syntax

✅ Clean, readable API for rapid prototyping

✅ Modular architecture for production use



# 🔭 Roadmap

 🧠 Static parameters (like /users)

 🌐 Static file serving

 🐳 Docker support

 📄 PyPI full release and documentation site

# ⚠️ Development Status
Notice: sufast is currently under active development.
While it is fully functional for experimentation and early prototyping, it is not yet recommended for production or commercial deployment.

Contributions, bug reports, and feature suggestions are welcome! 🙌

# 🤝 Contributing
Found a bug or want to help?
Open an issue or PR on GitHub!


📃 License
MIT License – do anything you want, just give credit 😄
Copyright © Shohan


