from setuptools import setup

def readme():
    with open('README.md') as f:
        return f.read()

setup(name='alarmdecoder',
    version='0.5',
    description='Python interface library for the Alarm Decoder (AD2) family of alarm devices, including: the AD2USB, AD2SERIAL and AD2PI.',
    long_description=readme(),
    classifiers=[
        'Development Status :: 4 - Beta',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 2.7',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Communications',
        'Topic :: Home Automation',
        'Topic :: Security',
    ],
    keywords='alarmdecoder alarm decoder ad2 ad2usb ad2serial ad2pi security ademco dsc',
    url='http://github.com/nutechsoftware/alarmdecoder',
    author='Nu Tech Software Solutions, Inc.',
    author_email='general@support.nutech.com',
    license='MIT',
    packages=['alarmdecoder', 'alarmdecoder.event'],
    install_requires=[
        'pyopenssl',
        'pyusb>=1.0.0b1',
        'pyserial>=2.7',
        'pyftdi>=0.9.0',
    ],
    dependency_links=[
        'https://github.com/eblot/pyftdi/archive/v0.9.0.tar.gz#egg=pyftdi-0.9.0'
    ],
    test_suite='nose.collector',
    tests_require=['nose', 'mock'],
    scripts=['bin/ad2-sslterm', 'bin/ad2-firmwareupload'],
    include_package_data=True,
    zip_safe=False)
