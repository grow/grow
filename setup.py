"""Grow Setup."""

from setuptools import find_packages
from setuptools import setup


INSTALL_REQ = []

for i in open('requirements.txt').readlines():
    req = i.strip()
    if req.startswith(('#', '-')):
        continue
    INSTALL_REQ.append(req)


setup(
    name='grow',
    version=open('grow/VERSION').read().strip(),
    description=(
        'Develop everywhere and deploy anywhere: a declarative '
        'site generator for rapid, high-quality web site production.'
    ),
    long_description=open('description.txt').read().strip(),
    url='https://grow.io',
    zip_safe=False,
    license='MIT',
    author='Grow SDK Authors',
    author_email='code@grow.io',
    include_package_data=True,
    packages=find_packages(exclude=[
        'lib*',
        'node_modules',
    ]),
    install_requires=INSTALL_REQ,
    scripts=[
        'bin/grow',
    ],
    keywords=[
        'grow',
        'cms',
        'static site generator',
        's3',
        'google cloud storage',
        'content management'
    ],
    classifiers=[
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ])
