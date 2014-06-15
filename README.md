lonely_planet
=============

Dear Lonely Planeteer(s),

This script is written for Python 2.7.5 (which should be the default on MAC OSX as of Aug 2013) and only needs the following modules:

    + Jinja2 - Installion instructions: http://jinja.pocoo.org/docs/intro/#installation

To run the script, either use the executable script: 'run_me' or type 'python lp_page_gen.py'.

To run the script against the sample files, and generate the result in a directory named 'html_result', use the executable script 'test_me'

XML Parser Optimisations

Firstly, we want to use lxml if possible however this is much more effort to install.

Pre-requisites: sudo apt-get install libxml2 libxml2-dev libxslt1-dev lib32z1-dev
Installing lxml: sudo pip install lxml

