from setuptools import setup, find_packages

setup(
    name="toggletest",
    version="1.0.0",
    author="Vaishnavi Rathi",
    author_email="rathi.va@northeastern.edu",
    description="Universal Python library for hardware toggle switch testing automation",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/vaishnavirathi456-coder/toggletest",
    packages=find_packages(),
    python_requires=">=3.8",
    install_requires=[],
    extras_require={
        "arduino": ["pyserial>=3.5"],
        "rpi": ["RPi.GPIO>=0.7"],
        "dev": ["pytest>=7.0", "pytest-cov"],
        "all": ["pyserial>=3.5", "pytest>=7.0", "pytest-cov"],
    },
    entry_points={
        "console_scripts": [
            "toggletest=toggletest.cli:main",
        ],
        "pytest11": [
            "toggletest=toggletest.pytest_plugin",
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Software Development :: Testing",
        "Topic :: System :: Hardware",
    ],
)