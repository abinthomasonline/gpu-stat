from setuptools import find_packages, setup

# Read version without importing
with open("gpu_stat/_version.py", "r") as f:
    exec(f.read())

setup(
    name="gpu-stat",
    version=__version__,
    packages=find_packages(),
    install_requires=[
        "click",
        "paramiko",
        "pyyaml",
        "streamlit",
        "plotly",
        "pandas",
    ],
    extras_require={
        "dev": [
            "black",
            "isort",
        ],
    },
    entry_points={
        "console_scripts": [
            "gpu-stat=gpu_stat.cli:main",
        ],
    },
    author="Abin Thomas",
    author_email="abinthomasonline@gmail.com",
    description="A simple tool to monitor NVIDIA GPU usage on remote machines",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/abinthomasonline/gpu-stat",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
)
