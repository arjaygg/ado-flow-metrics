"""Setup configuration for flow-metrics package."""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="flow-metrics",
    version="0.1.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="A Python implementation of flow metrics for software development teams",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/flow-metrics-python",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=3.0.0",
            "black>=22.0.0",
            "flake8>=4.0.0",
            "mypy>=0.950",
            "pre-commit>=2.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "flow-metrics=src.cli:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["config/*.json"],
    },
)