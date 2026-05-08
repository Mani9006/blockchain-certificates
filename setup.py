"""Setup script for blockchain-certificates package."""

from setuptools import find_packages, setup

setup(
    name="blockchain-certificates",
    version="1.0.0",
    description="Blockchain-based Certificate Verification System",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    author="Mani",
    author_email="myfamily9006@gmail.com",
    url="https://github.com/blockchain-certs/blockchain-certificates",
    packages=find_packages(),
    python_requires=">=3.9",
    install_requires=[
        "cryptography>=41.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-cov>=4.1.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "cert-chain=src.cli:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Education",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Security :: Cryptography",
    ],
    license="MIT",
    zip_safe=False,
)
