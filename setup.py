from setuptools import setup


setup(
    name='webbackend',
    version='1.0',
    long_description=__doc__,
    packages=['app'],
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        'Flask==2.2.2',
        'Flask-MQTT==1.1.1',
        'Flask-SocketIO==5.3.2'
    ]
)
