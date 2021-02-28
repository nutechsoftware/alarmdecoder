"""Setup script"""

import sys
from setuptools import setup

def readme():
    """Returns the contents of README.rst"""

    with open('README.rst') as readme_file:
        return readme_file.read()

extra_requirements = []
if sys.version_info < (3,):
    extra_requirements.append('future>=0.14.3')

setup(name='alarmdecoder',
    version='1.13.10',
    description='Python interface for the AlarmDecoder (AD2) family '
                'of alarm devices which includes the AD2USB, AD2SERIAL and AD2PI.',
    long_description=readme(),
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.4',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Communications',
        'Topic :: Home Automation',
        'Topic :: Security',
    ],
    keywords='alarmdecoder alarm decoder ad2 ad2usb ad2serial ad2pi security '
             'ademco dsc nutech',
    url='http://github.com/nutechsoftware/alarmdecoder',
    author='Nu Tech Software Solutions, Inc.',
    author_email='general@support.nutech.com',
    license='MIT',
    packages=['alarmdecoder', 'alarmdecoder.devices', 'alarmdecoder.event', 'alarmdecoder.messages', 'alarmdecoder.messages.lrr'],
    install_requires=[
        'pyserial>=2.7',
    ] + extra_requirements,
    test_suite='nose.collector',
    tests_require=['nose', 'mock'],
    scripts=['bin/ad2-sslterm', 'bin/ad2-firmwareupload'],
    include_package_data=True,
    zip_safe=False)
