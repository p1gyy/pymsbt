from setuptools import setup, find_packages

setup(
    name='pymsbt',
    version='1.0.2',
    author='Piggy Gaming',
    description='A python library for parsing and editing .msbt binary files',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/p1gyy/pymsbt',
    packages=find_packages(),
    python_requires='>=3.12',
    install_requires=[
        #none
    ],
)
