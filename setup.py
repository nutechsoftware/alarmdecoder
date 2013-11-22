from setuptools import setup

def readme():
    with open('README.rst') as f:
        return f.read()

setup(name='pyad2',
    version='0.5',
    description='Interface to the AD2 family of alarm devices.',
    long_description=readme(),
    classifiers=[
        'Development Status :: 3 - Alpha',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 2.7',
        'Topic :: Security Alarms',
    ],
    keywords='ad2usb ad2serial ad2pi alarm security ademco',
    url='http://github.com/nutechsoftware/pyad2',
    author='Nu Tech Software Solutions, Inc.',
    author_email='general@support.nutech.com',
    license='',
    packages=['pyad2'],
    install_requires=[
        'pyopenssl',
        'pyftdi'
    ],
    test_suite='nose.collector',
    tests_require=['nose', 'mock'],
    scripts=['bin/ad2-sslterm', 'bin/ad2-firmwareupload'],
    include_package_data=True,
    zip_safe=False)
