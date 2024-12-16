"""
Setup script for NIA package.
"""

from setuptools import setup, find_packages

setup(
    name="nia",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        # Core dependencies
        "aiohttp>=3.8.0",  # For async HTTP requests
        "neo4j>=5.0.0",    # For graph database
        
        # Vector store dependencies
        "torch>=2.0.0",              # PyTorch for embeddings
        "sentence-transformers>=2.0.0", # For text embeddings
        "qdrant-client>=1.1.0",      # Vector database
        
        # Utility dependencies
        "python-dotenv>=0.19.0",  # For environment variables
        "pydantic>=2.0.0",        # For data validation
        "numpy>=1.21.0",          # For numerical operations
        "tqdm>=4.65.0",           # For progress bars
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "black>=23.0.0",
            "isort>=5.12.0",
            "mypy>=1.0.0",
            "pylint>=2.17.0",
        ]
    },
    python_requires=">=3.9",
    author="Your Name",
    author_email="your.email@example.com",
    description="Neural Intelligence Architecture",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
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
