from setuptools import setup, find_packages

setup(
    name="harness-converter",
    version="0.1.0",
    package_dir={"": "src"},
    packages=find_packages(where="src", exclude=["tests*"]),
    install_requires=[
        "click>=8.1.3",
    ],
    entry_points={
        'console_scripts': [
            'harness-converter=harness_converter.cli:main',
        ],
    },
)
