from setuptools import setup

with open('requirements.txt') as f:
    required = f.read().splitlines()


setup(
    name='webbackend',
    version='1.0',
    long_description=__doc__,
    packages=['webbackend'],
    include_package_data=True,
    zip_safe=False,
    install_requires=required
)
