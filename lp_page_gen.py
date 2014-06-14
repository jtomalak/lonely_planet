# -*- coding: utf-8 -*-

from __future__ import print_function

# TODO: UTF-8 support isn't ideal in Python,
# so let's just ensure everything uses it by default
import sys
#reload(sys)
#sys.setdefaultencoding('utf-8')

import xml.etree.ElementTree as et
import argparse as ap
import jinja2 as jj
import re as re

'''
    Lonely Planet XML to HTML Generator
'''
# TODO: using place names for the html file names isn't ideal but it makes the files much more human readable, link them by node ID or something
# TODO? Consider using lxml instead of the basic ElementTree (i.e. from lxml import ElementTree as et) - this however requires libxml
# TODO! write up a quick XML generator to create a much LARGER set of sample files to better profile cpu/mem usage

# TODO: refactor into a nicer top-level function with kwargs maybe
def walk(node, f_op = lambda node: None, f_include = lambda node: True, parent = None, depth = 0):
    if f_include(node):
        f_op(node, parent, depth)

    for child in node:
        c_depth = depth + 1 if f_include(node) else depth
        c_parent = node if f_include(node) else parent

        walk(child, f_op, f_include, c_parent, c_depth)

def valid_taxonomy_node(node):
    return node.find('node_name') is not None

def print_taxonomy_node(node, parent, depth):
    prefix = "   " * depth
    parent_name = parent.find('node_name').text if depth != 0 else "root"
    print("[", depth, "]", prefix, node.find('node_name').text, "=>", parent_name)

class TaxonomyNodeHtmlizer:
    def __init__(self, template_file, content_gen, output_directory = './'):
# TODO asserts!
        self.template_file = template_file
        self.output_directory = output_directory
        self.content_generator = content_gen

    def get_file_name(self, node):
        fixed_name = node.find('node_name').text.replace(' ', '_') # TODO
        return fixed_name + '.html'

    def __call__(self, node, parent, depth):
        with open(self.template_file, 'r') as t:
            name = node.find('node_name').text # TODO
            links = []
            if parent is not None and valid_taxonomy_node(parent):
                links.append( { 'href': self.get_file_name(parent), 'caption': parent.find('node_name').text } ) #TODO

            for child in node:
                if valid_taxonomy_node(child):
                    child_href = self.get_file_name(child)
                    child_caption = child.find('node_name').text # TODO
                    links.append( { 'href': child_href, 'caption': child_caption } )

            text_content = self.content_generator(node)

            self.content_post_processing(text_content)

            # TODO: with a bit of effort we can also put a wrapper around the templating implementation!
            template = jj.Template(t.read())
            output_file = self.output_directory + '/' + self.get_file_name(node)
            with open(output_file, 'w') as o:
                output = template.render(
                    destination_name = name,
                    linked_destinations = links,
                    destination_content = text_content
                )
                o.write( output.encode('utf-8') )

    def content_post_processing(self, content_list):
        www_digger = re.compile(r'www\.[a-zA-Z0-9\./_]*') # TODO unhandled chars: -~:?#\[\]@!$&()\*+,;=
        for idx in range(0, len(content_list)):
            www_matches = www_digger.findall(content_list[idx])
            for match in www_matches:
                href_url = '<a href="http://' + match + '" target="_blank">' + match + '</a>'
                content_list[idx] = content_list[idx].replace(match, href_url)


#TODO: Unblob content text and making it more presentable
class DestinationContentGenerator:
    def __init__(self, destinations_content_tree):
        self.content_tree = destinations_content_tree

    class ContentCollector:
        def __init__(self):
            self.content_map = []

        def __call__(self, node, parent, depth):
            node_text = node.text.strip()
            if node_text:
                self.content_map.append(node_text)

    def _print_content_node(self, node, parent, depth):
        if node.text.strip():
            print(node.tag)
            print(node.text.strip())

    def __call__(self, node):
        node_id = node.get('atlas_node_id')
        xpath = "destination[@atlas_id='" + node_id + "']"
        destination_nodes = self.content_tree.findall(xpath)

        node_collector = self.ContentCollector()
        for dest in destination_nodes:
            walk(dest, node_collector)

        return node_collector.content_map

# uncomment this the line beginning with @ when running with the memory profiler
#@profile
def main():
    args_parser = ap.ArgumentParser()
    args_parser.add_argument('taxonomy_file')
    args_parser.add_argument('destinations_file')
    args_parser.add_argument('output_directory')

    args = args_parser.parse_args()

    try:
        taxonomy_tree = et.parse(args.taxonomy_file)
        destinations_tree = et.parse(args.destinations_file)

        htmlizer = TaxonomyNodeHtmlizer('lp_template.html', DestinationContentGenerator(destinations_tree), args.output_directory)
        walk(taxonomy_tree.getroot(), htmlizer, valid_taxonomy_node)
        #walk(taxonomy_tree.getroot(), print_taxonomy_node, valid_taxonomy_node)

    except IOError as ex:
        print("XML Parsing Error:", str(ex))
        sys.exit(1)

if __name__ == '__main__':
    main()
