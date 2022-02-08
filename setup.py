"""Grow.dev setup."""

import re
from setuptools import find_packages
from setuptools import setup


DEP_RE = re.compile(r'([\S]*)\s?=\s? [\"\']?([^\'\"]*)[\"\']?', re.IGNORECASE)
INSTALL_REQ = []

with open('Pipfile') as pipfile:
    in_dep_section = False
    for line in pipfile.readlines():
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        if in_dep_section:
            if line.startswith('['):
                in_dep_section = False
                continue
            line_match = DEP_RE.match(line)
            if line_match:
                INSTALL_REQ.append(
                    '{}{}'.format(line_match.group(1).strip('"'), line_match.group(2)))
        elif line == '[packages]':
            in_dep_section = True


setup(
    name='grow',
    version='2.1.3',
    description=(
        'Develop everywhere and deploy anywhere: a declarative '
        'site generator for rapid, high-quality web site production.'
    ),
    long_description=open('description.txt').read().strip(),
    url='https://grow.dev',
    zip_safe=False,
    license='MIT',
    author='Grow.dev Authors',
    author_email='code@grow.dev',
    include_package_data=True,
    packages=find_packages(exclude=[
        'lib*',
        'node_modules',
    ]),
    install_requires=INSTALL_REQ,
    python_requires='>=3.3',
    entry_points="""
        [console_scripts]
        grow=grow.cli:main
    """,
    keywords=[
        'grow',
        'cms',
        'static site generator',
        'content management'
    ],
    classifiers=[
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ])
