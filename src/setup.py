from setuptools import setup, find_packages

setup(
    name='YeelightMatrix',
    version='0.1.1',
    packages=find_packages(),
    package_data={
        "custom_components.yeelight_matrix": ["*.json", "translations/*.json"],
    },
    include_package_data=True,
    install_requires=[
        'yeelight>=0.7.14',
        'Pillow>=11.0.0'
    ],
)