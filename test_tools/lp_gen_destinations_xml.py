# -*- coding: utf-8 -*-

from __future__ import print_function

import sys
from lxml import etree as xml_parser
import argparse as ap
from collections import OrderedDict as odict

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

    nodes = []

    for num in range(num_nodes):
        dest_node = xml_parser.Element('destination')
        node_id = str(num).zfill(8)
        node_title = rstring_generator(random.randint(5,12))
        dest_node.set('atlas-id', node_id)
        dest_node.set('title', node_title)
        nodes.append( (node_id, node_title) )
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

    del root_node
    return nodes

# TODO: for now we just create a flat taxonomy node tree
def create_taxonomy_xml_file(filename, nodes):
    root_node = xml_parser.Element('taxonomies')
    taxonomy_root_node = xml_parser.Element('taxonomy')
    taxonomy_node = xml_parser.Element('taxonomy_name')
    taxonomy_node.text = 'World'
    taxonomy_root_node.append(taxonomy_node)

    for (node_id, node_title) in nodes:
        taxonomy_node = xml_parser.Element('node')
        taxonomy_node.set('atlas_node_id', node_id)
        taxonomy_name = xml_parser.Element('node_name')
        taxonomy_name.text = node_title
        taxonomy_node.append(taxonomy_name)
        taxonomy_root_node.append(taxonomy_node)

    root_node.append(taxonomy_root_node)

    with open(filename, 'w') as xml_file:
        xml_doc = xml_parser.ElementTree(root_node)
        xml_doc.write(
            xml_file,
            pretty_print = True,
            encoding = 'UTF-8',
            xml_declaration = True
        )

    del root_node

@profile
def main():
    args_parser = ap.ArgumentParser()
    args_parser.add_argument('out_dest')
    args_parser.add_argument('out_tax')
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

    nodes = create_content_xml_file(args.out_dest, num_nodes, num_children, child_depth)
    create_taxonomy_xml_file(args.out_tax, nodes)

    return 0

if __name__ == '__main__':
    sys.exit( main() )

