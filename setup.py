import os
import re
from setuptools import setup, find_packages

def read_version():
    version_file = os.path.join("LightYtSearch", "version.py")
    with open(version_file, "r", encoding="utf-8") as f:
        content = f.read()

    version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]", content, re.M)
    if version_match:
        return version_match.group(1)
    raise RuntimeError("Unable to find version string.")

__version__ = read_version()

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open(os.path.join(os.path.dirname(__file__), "requirements.txt"), "r", encoding="utf-8-sig") as f:
    required_packages = f.read().splitlines()

setup(
    name="LightYtSearch",
    version=__version__,
    author="Your Name",
    description="Lightweight YouTube search scraper without using the official API",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/LightYtSearch",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Internet :: WWW/HTTP :: Indexing/Search",
    ],
    python_requires=">=3.9",
    install_requires=required_packages,
    entry_points={
        "console_scripts": [
            "lightytsearch=LightYtSearch.cli:main",
        ],
    },
)
