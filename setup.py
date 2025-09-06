"""
VaultRunner - HashiCorp Vault Docker Integration Tool

A comprehensive Python tool for seamless integration between HashiCorp Vault and Docker environments.
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [
        line.strip() for line in fh if line.strip() and not line.startswith("#")
    ]

setup(
    name="vaultrunner",
    version="1.0.0",
    author="VaultRunner Team",
    author_email="team@vaultrunner.dev",
    description="HashiCorp Vault Docker Integration Tool",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/1trippycat/vaultrunner",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: System :: Systems Administration",
        "Topic :: Security",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=6.0",
            "pytest-cov>=2.0",
            "black>=21.0",
            "flake8>=3.8",
            "mypy>=0.812",
        ],
    },
    entry_points={
        "console_scripts": [
            "vaultrunner=vaultrunner.main:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)
