## 📦 Building and Publishing the Package

To create the distribution files and upload your package to PyPI, run the following commands:

## 📝 Updating the Package

Update the version number in setup.py
Then run the following commands:

```bash
python setup.py sdist bdist_wheel
python -m twine upload dist/*
```