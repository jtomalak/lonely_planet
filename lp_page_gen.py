
from __future__ import print_function

import xml.etree.ElementTree as et
import argparse as ap
import sys

'''
    Lonely Planet XML to HTML Generator
'''

def walk(node, f_include = lambda: true, f_op = lambda node: None, depth = 0):
    for child in node:
        if not f_include(child):
            walk(child, f_include, f_op, depth)
        else:
            f_op(child, depth) # todo: the parent node _may_ also be useful here!
            walk(child, f_include, f_op, depth+1)

def valid_taxonomy_node(node):
    return node.find('node_name') is not None

def print_taxonomy_node(node, depth):
    prefix = "\t" * depth
    print(prefix, node.find('node_name').text, node.attrib)

def main():
    args_parser = ap.ArgumentParser()
    args_parser.add_argument('taxonomy_file')
    args_parser.add_argument('destinations_file')
    args_parser.add_argument('output_directory')

    args = args_parser.parse_args()

    try:
        taxonomy_tree = et.parse(args.taxonomy_file)

        walk(taxonomy_tree.getroot(), valid_taxonomy_node, print_taxonomy_node)

    except IOError as ex:
        print("XML Parsing Error:", str(ex))
        sys.exit(1)

if __name__ == '__main__':
    main()
    print("it works so far!")
