import os
from typing import List

import setuptools


def get_long_description() -> str:
    with open('README.md') as fh:
        return fh.read()


def get_required() -> List[str]:
    with open('requirements.txt') as fh:
        return fh.read().splitlines()


def get_version():
    with open(os.path.join('metaflowbot', 'version.py')) as fh:
        for line in fh:
            if line.startswith('__version__ = '):
                return line.split()[-1].strip().strip("'")


setuptools.setup(
    name='metaflowbot',
    packages=setuptools.find_packages(),
    version=get_version(),
    license='Apache License 2.0',
    author='Machine Learning Infrastructure Team at Netflix',
    include_package_data=True,
    url='https://github.com/Netflix/metaflow-tools',
    long_description=get_long_description(),
    long_description_content_type='text/markdown',
    install_requires=get_required(),
    python_requires='>=3.6',
    entry_points={
        'console_scripts': ['metaflowbot=metaflowbot.__main__:main'],
    }
)
