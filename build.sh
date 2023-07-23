#! /usr/bin/env bash
mkdir dist &>/dev/null
rm -rf dist
python setup.py sdist