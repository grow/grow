from setuptools import setup


setup(
    name='grow',
    version=open('VERSION').read().strip(),
    description='Develop everywhere and deploy anywhere: a static site generator/CMS that helps teams build high-quality web sites.',
    long_description=open('description.txt').read().strip(),
    url='http://growsdk.org',
    license='MIT',
    author='Grow SDK Authors',
    author_email='hello@grow.io',
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
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ])
