"""Setup configuration for newsletters package."""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="newsletters",
    version="0.1.0",
    author="Your Name",
    description="AI newsletter analysis pipeline",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    python_requires=">=3.11",
    install_requires=[
        "anthropic>=0.40.0",
        "httpx>=0.27.0",
        "beautifulsoup4>=4.12.0",
        "lxml>=5.0.0",
        "google-auth>=2.25.0",
        "google-auth-oauthlib>=1.2.0",
        "google-auth-httplib2>=0.2.0",
        "google-api-python-client>=2.110.0",
        "notion-client>=2.2.0",
        "sqlalchemy>=2.0.0",
        "pandas>=2.0.0",
        "click>=8.1.0",
        "python-dotenv>=1.0.0",
        "pyyaml>=6.0",
        "python-dateutil>=2.8.0",
        "pytz>=2023.3",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "black>=23.0.0",
            "ruff>=0.1.0",
        ]
    },
    entry_points={
        "console_scripts": [
            "newsletter=src.cli:main",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Communications :: Email",
        "Topic :: Text Processing :: Markup",
        "Programming Language :: Python :: 3.11",
    ],
)
