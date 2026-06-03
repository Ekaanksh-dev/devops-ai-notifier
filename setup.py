from setuptools import setup, find_packages

setup(
    name="autopwflow",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "requests",
        "pynacl",
        "python-dotenv"
    ],
    entry_points={
        "console_scripts": [
            "autopwflow=autopwflow.cli:main"
        ]
    }
)
