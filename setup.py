import os

from setuptools import setup, find_packages


def content(file: str):
    local_dir = os.path.abspath(os.path.dirname(__file__))

    with open(os.path.join(local_dir, file), 'r') as f:
        file_content = f.read()

    return file_content


setup(
    name='template_python',
    version=content('VERSION'),
    packages=find_packages(),
    install_requires=[
        'wheel>=0.36.2',
        'versionner>=1.5.3',
    ],
    python_requires='>=3.9',
    long_description=content('README.md'),
    long_description_content_type='text/markdown'
)
