
from __future__ import print_function

import xml.etree.ElementTree as et
import argparse as ap
import sys
import jinja2 as jj

'''
    Lonely Planet XML to HTML Generator
'''
# TODO: using place names is a bad for file names, link them by node ID or something

def walk(node, f_include = lambda: true, f_op = lambda node: None, parent = None, depth = 0):
    if f_include(node):
        f_op(node, parent, depth)

    for child in node:
        c_depth = depth + 1 if f_include(node) else depth
        c_parent = node if f_include(node) else parent

        walk(child, f_include, f_op, c_parent, c_depth)

def valid_taxonomy_node(node):
    return node.find('node_name') is not None

def print_taxonomy_node(node, parent, depth):
    prefix = "   " * depth
    parent_name = parent.find('node_name').text if depth != 0 else "root"
    print("[", depth, "]", prefix, node.find('node_name').text, "=>", parent_name)

class TaxonomyNodeHtmlizer:
    def __init__(self, template_file, output_directory = './'):
# TODO asserts!
        self.template_file = template_file
        self.output_directory = output_directory

    def __call__(self, node, parent, depth):
        with open(self.template_file, 'r') as t: #TODO!
            name = node.find('node_name').text
            children = []
            for child in node:
                if valid_taxonomy_node(child):
                    children.append(child.find('node_name').text)

            text_content = [ "There is no content loaded yet!" ]

            template = jj.Template(t.read())
            output_file = self.output_directory + '/out_' + name + '.html'
            with open(output_file, 'w') as o:
                o.write( template.render(
                    destinationname = name,
                    child_destinations = children,
                    destination_content = text_content
                ))

#@profile
def main():
    args_parser = ap.ArgumentParser()
    args_parser.add_argument('taxonomy_file')
    args_parser.add_argument('destinations_file')
    args_parser.add_argument('output_directory')

    args = args_parser.parse_args()

    try:
        taxonomy_tree = et.parse(args.taxonomy_file)

        #walk(taxonomy_tree.getroot(), valid_taxonomy_node, print_taxonomy_node)
        htmlizer = TaxonomyNodeHtmlizer('lp_template.html', args.output_directory)
        walk(taxonomy_tree.getroot(), valid_taxonomy_node, htmlizer)

        destinations_tree = et.parse(args.destinations_file)

    except IOError as ex:
        print("XML Parsing Error:", str(ex))
        sys.exit(1)

if __name__ == '__main__':
    main()
