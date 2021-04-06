from setuptools import find_packages
from distutils.core import setup

setup(
    name='aiolistener',
    version='1.0.0',
    packages=find_packages(exclude=['tests']),
    description='asyncio listening socket wrapper',
    long_description="""
Documentation
-------------
    You can see the project and documentation at the `GitHub repo <https://github.com/robertchase/aiolistener>`
    """,
    author='Bob Chase',
    url='https://github.com/robertchase/aiolistener',
    license='MIT',
)
