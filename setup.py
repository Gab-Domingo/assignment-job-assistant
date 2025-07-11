from setuptools import setup, find_packages
setup(
    name="apify_scraper",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        "requests==2.31.0",
        "python-dotenv==1.0.1",
        "azure-ai-inference",
        "azure-core",
        "pydantic",
        "setuptools"
    ],
    python_requires=">=3.8",
    author="Gab Domingo",
    description="A job scraping and analysis tool using Apify",
)