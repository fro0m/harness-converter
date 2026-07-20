from setuptools import setup, find_packages

setup(
    name="harness-converter",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "click>=8.1.3",
    ],
    entry_points={
        'console_scripts': [
            'harness-converter=harness_converter.cli:main',
        ],
    },
)
