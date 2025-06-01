from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="sufast",
    version="0.2",  # Bump the version!
    author="Shohan",
    author_email="shohan.dev.cse@gmail.com",
    description="A blazing-fast Python web framework powered by Rust 🚀",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/shohan-dev/sufast",
    project_urls={
        "Bug Tracker": "https://github.com/shohan-dev/sufast/issues",
        "Documentation": "https://github.com/shohan-dev/sufast",
    },
    license="MIT",
    packages=find_packages(),
    include_package_data=True,  # ✅ this is required
    install_requires=[],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        # "Framework :: sufast", # still not supported
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Internet :: WWW/HTTP",
        "Development Status :: 3 - Alpha",
    ],
    python_requires=">=3.8",
)
