# 🚀 Sufast – A Blazing Fast Python Web Framework Powered by Rust

**Sufast** is a hybrid web framework that combines the developer-friendly simplicity of **Python 🐍** with the raw execution speed of **Rust 🦀**.

Built for high-performance APIs, scalable microservices, and modern AI-era backends, Sufast delivers the best of both worlds:


---

# ⚡ Why Sufast?

- 🚀 **52,000+ RPS** performance with Rust core
- 🐍 FastAPI-style decorator syntax (`@app.get`, `@app.post`)
- 📦 Easy to use and install

---

```bash
pip install Sufast
```
⚠️ Requires Python 3.8+ and a platform-compatible Rust binary bundled in the package.

# 🚀 Quickstart

```bash
from Sufast import App

app = App()

@app.get("/")
def hello():
    return {"message": "Hello from Sufast 👋"}

app.run()
```
Visit -> [http://localhost:8080/ 🚀](http://localhost:8080/)


# 📚 Advanced Example – API Server
```bash
from Sufast import App

app = App()

# 🧪 Sample database
users = {
    "shohan": {"name": "shohan", "email": "shohan@example.com"},
    "bob": {"name": "Bob", "email": "bob@example.com"},
    "alice": {"name": "Alice", "email": "alice@example.com"},
}

@app.get("/")
def home():
    return {"message": "Welcome to Sufast API 🚀"}

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

## 📊 Real-World Performance Benchmark

| **Metric**               | 🦀 **Native Rust** (Actix-Web) | 🚀 **Sufast** (Rust + Python) | 🐍 **FastAPI** (Uvicorn) | 🌐 **Node.js** (Express) |
|--------------------------|--------------------------------|-------------------------------|---------------------------|----------------------------|
| **Language**             | 🦀 Rust                        | 🦀 Rust + 🐍 Python             | 🐍 Python                | <img src="https://cdn.jsdelivr.net/gh/devicons/devicon/icons/javascript/javascript-original.svg" width="20"/> JavaScript |
| **Avg. Requests/sec** 🚀 | 🔥 **56,000+**                 | 🔥 **52,000+**                 | 🐢 ~25,000+              | ⚡ ~35,000+                |
| **Avg. Latency (ms)** ⏱  | ~1.7                           | ~2.1                          | ~5.6                    | ~4.2                      |
| **Memory Usage (MB)** 💾 | ~20                            | ~25                           | ~60                     | ~50                       |
| **Startup Time (ms)** ⚡  | ~25                            | ~35                           | ~90                     | ~40                       |
| **Developer UX** 🧑‍💻     | ⚠️ Manual, low-level routing   | ✅ FastAPI-style, intuitive    | ✅ Very Dev-Friendly     | ✅ Dev-Friendly           |


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

✅ Python decorators like `@app.get()` , `@app.post()`

✅ FastAPI-style route syntax

✅ Clean, readable API for rapid prototyping

✅ Modular architecture for production use



# 🔭 Roadmap

 🧠 Static parameters (like `/users`)

 🌐 Static file serving

 🐳 Docker support

 📄 PyPI full release and documentation site

# ⚠️ Development Status
Notice: Sufast is currently under active development.
While it is fully functional for experimentation and early prototyping, it is not yet recommended for production or commercial deployment.

Contributions, bug reports, and feature suggestions are welcome! 🙌

# 🤝 Contributing
Found a bug or want to help?
## How to Contribute

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit your changes: `git commit -m 'Add some amazing feature'`
4. Push to the branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

Have suggestions or found a bug? [Open an issue](https://github.com/shohan-dev/sufast/issues) or submit a PR!

Join our growing community of contributors helping make Sufast even better!


# 📃 License

This project is licensed under the terms of the MIT license.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

[View the full license](https://opensource.org/licenses/MIT)

