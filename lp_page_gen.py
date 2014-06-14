
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
        self.content_generator = lambda node : [ "There is no content loaded yet!" ]

    def content_generator(content_gen):
        self.content_generator = content_gen

    def get_file_name(self, node):
        fixed_name = node.find('node_name').text.replace(' ', '_') # TODO
        return fixed_name + '.html'

    def __call__(self, node, parent, depth):
        with open(self.template_file, 'r') as t:
            name = node.find('node_name').text # TODO
            links = []
            if parent is not None and valid_taxonomy_node(parent):
                links.append( { 'href': self.get_file_name(parent), 'caption': parent.find('node_name').text } )

            for child in node:
                if valid_taxonomy_node(child):
                    child_href = self.get_file_name(child)
                    child_caption = child.find('node_name').text # TODO
                    links.append( { 'href': child_href, 'caption': child_caption } )

            text_content = self.content_generator(node)

            # TODO: with a bit of effort we can also put a wrapper around the templating implementation!
            template = jj.Template(t.read())
            output_file = self.output_directory + '/' + self.get_file_name(node)
            with open(output_file, 'w') as o:
                o.write( template.render(
                    destination_name = name,
                    linked_destinations = links,
                    destination_content = text_content
                ))

@profile
def main():
    args_parser = ap.ArgumentParser()
    args_parser.add_argument('taxonomy_file')
    args_parser.add_argument('destinations_file')
    args_parser.add_argument('output_directory')

    args = args_parser.parse_args()

    try:
        taxonomy_tree = et.parse(args.taxonomy_file)

        htmlizer = TaxonomyNodeHtmlizer('lp_template.html', args.output_directory)
        walk(taxonomy_tree.getroot(), valid_taxonomy_node, htmlizer)
        walk(taxonomy_tree.getroot(), valid_taxonomy_node, print_taxonomy_node)

        destinations_tree = et.parse(args.destinations_file)

    except IOError as ex:
        print("XML Parsing Error:", str(ex))
        sys.exit(1)

if __name__ == '__main__':
    main()
