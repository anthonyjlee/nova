"""
Setup configuration for NIA package.
"""

from setuptools import setup, find_packages

setup(
    name="nia",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "aiohttp",
        "neo4j",
        "qdrant-client",
        "numpy"
    ],
    extras_require={
        "dev": [
            "pytest",
            "pytest-asyncio",
            "black",
            "ruff",
            "mypy"
        ]
    },
    python_requires=">=3.9",
    description="Neural Intelligence Architecture",
    author="Your Name",
    author_email="your.email@example.com",
    url="https://github.com/yourusername/nia",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
)
