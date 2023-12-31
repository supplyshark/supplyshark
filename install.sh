#!/bin/bash
# TODO:
# Add install for python3.12, rubygems, & npm
# Maybe install ripgrep if we change from grep

# Install poetry 
curl -sSL https://install.python-poetry.org | python3 -

# Install pip requirements
pip install -r requirements.txt