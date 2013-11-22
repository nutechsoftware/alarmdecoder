from setuptools import setup

def readme():
    with open('README.rst') as f:
        return f.read()

setup(name='pyad2',
    version='0.5',
    description='Python interface library for the AD2 family of alarm devices.',
    long_description=readme(),
    classifiers=[
        'Development Status :: 3 - Alpha',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 2.7',
        'Topic :: Security Alarms',
    ],
    keywords='alarm data ad2usb ad2serial ad2pi security ademco dsc',
    url='http://github.com/nutechsoftware/pyad2',
    author='Nu Tech Software Solutions, Inc.',
    author_email='general@support.nutech.com',
    license='',
    packages=['pyad2', 'pyad2.event'],
    install_requires=[
        'pyopenssl',
        'pyusb>=1.0.0b1',
        'pyserial>=2.6',
        'pyftdi',
    ],
    test_suite='nose.collector',
    tests_require=['nose', 'mock'],
    scripts=['bin/ad2-sslterm', 'bin/ad2-firmwareupload'],
    include_package_data=True,
    zip_safe=False)
