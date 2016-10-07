# -*- coding: utf-8 -*-

from setuptools import setup, find_packages


tests_require = [
    'nose',
    'pyssim',
    'urllib3'
]


setup(
    name='wikimedia_thumbor',
    version='0.1.23',
    url='https://phabricator.wikimedia.org/diffusion/THMBREXT/',
    license='MIT',
    author='Gilles Dubuc, Wikimedia Foundation',
    description='Wikimedia Thumbor plugins',
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    platforms='any',
    install_requires=[
        'libthumbor>=1.3.2',
        'manhole',
        'python-swiftclient',
        'thumbor==6.0.1',
        'wand'
    ],
    extras_require={
        'tests': tests_require,
    },
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ]
)
