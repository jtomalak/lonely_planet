
from __future__ import print_function

import xml.etree.ElementTree as et
import argparse as ap
import sys

'''
    Lonely Planet XML to HTML Generator
'''

def walk_taxonomy(taxonomy_node, depth = 0):
    for child in taxonomy_node:
        if child.find('node_name') is None:
            walk_taxonomy(child, depth)
        else:
            prefix = "\t" * depth;
            print(prefix, child.find('node_name').text, child.attrib)
            walk_taxonomy(child, depth+1)

def main():
    args_parser = ap.ArgumentParser()
    args_parser.add_argument('taxonomy_file')
    args_parser.add_argument('destinations_file')
    args_parser.add_argument('output_directory')

    args = args_parser.parse_args()

    try:
        taxonomy_tree = et.parse(args.taxonomy_file)

        walk_taxonomy(taxonomy_tree.getroot())
        #for country in taxonomy_tree.getroot().iter('node'):
        #    print(country.find('node_name').text, country.attrib)

    except IOError as ex:
        print("XML Parsing Error:", str(ex))
        sys.exit(1)

if __name__ == '__main__':
    main()
    print("it works so far!")
