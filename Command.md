## 📦 Building and Publishing the Package

To create the distribution files and upload your package to PyPI, run the following commands:

## 📝 Updating the Package

Update the version number in setup.py
Then run the following commands:

```bash
python setup.py sdist bdist_wheel
python -m twine upload dist/*
```

# Claer the dist directory before building:

```bash
rm -f build/*
rm -rf dist/*
rm -rf sufast.egg-info/*
```

# 🛠️ Building the Package
```bash
python setup.py sdist bdist_wheel
```
# 📝 Uploading to PyPI
```bash
python -m twine upload dist/*
```