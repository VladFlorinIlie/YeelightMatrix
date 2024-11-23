from setuptools import setup, find_packages

setup(
    name='YeelightMatrix',
    version='0.1.0',
    packages=find_packages(include=['yeelight_matrix']),
    install_requires=[
        'yeelight==0.7.14',
        'Pillow==11.0.0',
        'setuptools==65.5.0'
    ],
)