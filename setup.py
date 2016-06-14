# -*- coding: utf-8 -*-

from setuptools import setup, find_packages


setup(
    name='wikimedia_thumbor',
    version='0.1.2',
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
        'thumbor>=6.0.1',
        'python-swiftclient',
        'wand',
        'bs4',
        'lxml',
    ],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ]
)
