from setuptools import setup, find_packages

setup(
    name="loger-1073",
    version="1.0.0",
    description="CLI and web dashboard for monitoring server programs and logs on port 1073",
    author="mak74ik",
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            "loger = loger_cli:main",
        ],
    },
    python_requires=">=3.9",
)
