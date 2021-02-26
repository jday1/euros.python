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
    description='Simple Python template to get up and running',
    author='James Day',
    author_email='james.alex.day@outlook.com',
    packages=find_packages(include=['template_python', 'template_python.*']),
    install_requires=[
        'wheel>=0.36.2',
        'flask>=1.1.2',
        'gunicorn>=20.0.4'
    ],
    extras_require={
        'test': [
            'pytest>=6.0.2',
            'coverage>=5.4',
            'pytest-html>=3.1.1'
        ],
        'lint': [
            'pylama>=7.1.1'
        ],
        'versioning': [
            'versionner>=1.5.3'
        ]
    },
    python_requires='>=3.9',
    long_description=content('README.md'),
    long_description_content_type='text/markdown'
)
