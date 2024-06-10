from setuptools import setup, find_packages

setup(
    name='telegram_lib',  # Replace with your desired package name
    version='0.1',  # Initial version
    packages=find_packages(where='.'),  # Automatically find packages
    package_dir={'': 'telegram_lib'},  # Specify the directory for the package
)
