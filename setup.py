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
        "pytest",
        "pytest-asyncio",
        "pytest-cov"
    ],
    python_requires=">=3.8",
)
