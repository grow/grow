#!/bin/bash
python run_tests.py
python setup.py sdist upload
rm -rf *.egg-info
rm -rf dist/
