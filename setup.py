"""Setup script for NIA package."""

from setuptools import setup, find_packages

setup(
    name="nia",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "aiohttp",
        "qdrant-client",
        "neo4j",
    ],
    extras_require={
        "dev": [
            "pytest",
            "pytest-asyncio",
            "pytest-cov",
            "pytest-randomly",
            "pytest-sugar",
            "pytest-timeout",
            "pytest-mock",
            "pytest-env",
            "pytest-xdist",
            "pytest-dash",
            "black",
            "ruff",
            "mypy"
        ]
    },
    python_requires=">=3.8",
)
