"""Setup configuration for logslice."""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="logslice",
    version="0.1.0",
    author="logslice contributors",
    description="Fast log filtering and aggregation utility with regex and time-range support",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/example/logslice",
    packages=find_packages(exclude=["tests*"]),
    python_requires=">=3.8",
    install_requires=[
        # No mandatory third-party dependencies; stdlib only
    ],
    extras_require={
        "dev": [
            "pytest>=7.0",
            "pytest-cov>=4.0",
            "mypy>=1.0",
            "ruff>=0.1",
        ]
    },
    entry_points={
        "console_scripts": [
            "logslice=logslice.cli:main",
        ]
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: System :: Logging",
        "Topic :: Utilities",
    ],
    keywords="log filter grep regex time-range aggregation",
    project_urls={
        "Bug Tracker": "https://github.com/example/logslice/issues",
        "Source": "https://github.com/example/logslice",
    },
)
