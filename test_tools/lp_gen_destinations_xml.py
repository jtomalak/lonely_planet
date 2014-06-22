# -*- coding: utf-8 -*-

from __future__ import print_function

import sys
from lxml import etree as xml_parser
import argparse as ap

import string
import random

def rstring_generator(size=6, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))

def rtext_generator(size=100, lines=6):
    result = '\n'
    for _ in range(lines):
        result = result + rstring_generator(size, string.ascii_uppercase + string.digits) + '\n'
    return result

def build_child_node(depth):
    node = xml_parser.Element(rstring_generator(random.randint(5,12),string.ascii_uppercase))
    build_child_node_impl(depth-1, node)
    return node

def build_child_node_impl(depth, node):
    if depth != 0:
        child = xml_parser.Element(rstring_generator(random.randint(5,12),string.ascii_uppercase))
        node.append(child)
        build_child_node_impl(depth-1, child)
    else:
        node.text = rtext_generator()

def create_content_xml_file(filename, num_nodes, num_children, child_depth):
    root_node = xml_parser.Element('destinations')

    for num in range(num_nodes):
        dest_node = xml_parser.Element('destination')
        dest_node.set('atlas-id', str(num).zfill(8))
        dest_node.set('title', rstring_generator(random.randint(5,12)))
        root_node.append(dest_node)

        for _ in range(num_children):
            dest_node.append( build_child_node(child_depth) )

    with open(filename, 'w') as xml_file:
        xml_doc = xml_parser.ElementTree(root_node)
        xml_doc.write(
            xml_file,
            pretty_print = True,
            encoding = 'UTF-8',
            xml_declaration = True
        )

def main():
    args_parser = ap.ArgumentParser()
    args_parser.add_argument('out')
    args_parser.add_argument('nodes')
    args_parser.add_argument('--children')
    args_parser.add_argument('--depth')

    args = args_parser.parse_args()

    try:
        num_nodes = int(args.nodes)
    except ValueError:
        print('ERROR: nodes argument must be an integer')
        return 1

    try:
        num_children = int(args.children)
    except TypeError:
        num_children = 1
    except ValueError:
        print('ERROR: children argument must be an integer')
        return 1

    try:
        child_depth = int(args.depth)
    except TypeError:
        child_depth = 1
    except ValueError:
        print('ERROR: children argument must be an integer')
        return 1

    create_content_xml_file(args.out, num_nodes, num_children, child_depth)

    return 0

if __name__ == '__main__':
    sys.exit( main() )

