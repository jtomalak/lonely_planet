# -*- coding: utf-8 -*-

from __future__ import print_function

import sys
import os
import shutil

import xml.etree.ElementTree as xml_parser
import argparse as ap
import jinja2 as jj
import re as re
from collections import OrderedDict

# Import from our current path works fine on Linux, but who knows elsewhere?
import lp.Requirements as lp_req

'''
    Lonely Planet XML to HTML Generator
'''

def walk(node, f_op = lambda node: None, f_include = lambda node: True, parent = None, depth = 0):
    if f_include(node):
        f_op(node, parent, depth)

    for child in node:
        c_depth = depth + 1 if f_include(node) else depth
        c_parent = node if f_include(node) else parent

        walk(child, f_op, f_include, c_parent, c_depth)

class DestinationTemplatePopulator:
    def __init__(self, template, output_directory = './html_result'):
        self.template = jj.Template(template)
        self.output_directory = output_directory
        self.content_post_processors = []

    def add_content_postprocessor(self, post_proc):
        self.content_post_processors.append(post_proc)
        return self

    # TODO: this modifies the list, i.e. pass by reference and is too C-ish (blegh)
    # In fact, I REALLY dislike this however not modifying in place feels like it would cost too
    # much memory - so MEASURE it!
    def _content_post_processing(self, content_list):
        for post_proc in self.content_post_processors:
            for title_idx in content_list:
                for text_idx in range(0, len(content_list[title_idx])):
                   content_list[title_idx][text_idx] = post_proc(content_list[title_idx][text_idx])

    def get_file_name(self, node_name):
        return node_name.replace(' ', '_') + '.html'

    def __call__(self, node_name, connected_nodes, text_content):
        if not node_name: # kind of silly, maybe assert?
            print('Warning: Attempting to generate content for node with no name.')
            return

        self._content_post_processing(text_content)

        links = []
        for node in connected_nodes:
            links.append( { 'href': self.get_file_name(node), 'caption': node } )

        output_file = self.output_directory + '/' + self.get_file_name(node_name)
        with open(output_file, 'w') as o:
            output = self.template.render(
                destination_name = node_name,
                linked_destinations = links,
                destination_content = text_content
            )
            o.write( output.encode('utf-8') )


class TaxonomyNodeHtmlizer:
    def __init__(self, content_gen, html_gen):
        self.content_generator = content_gen
        self.html_generator = html_gen

    def valid_taxonomy_node(self, node):
        return node.find('node_name') is not None

    def __call__(self, node, parent, depth):
        node_name = node.find('node_name').text # TODO
        links = []
        if parent is not None and self.valid_taxonomy_node(parent):
            links.append( parent.find('node_name').text )

        for child in node:
            if self.valid_taxonomy_node(child):
                links.append( child.find('node_name').text ) # TODO

        # TODO: consider also moving this out...
        node_id = node.get('atlas_node_id')
        text_content = self.content_generator(node_id)
        if not text_content:
            print('Warning: No content was found for', node_name)
        self.html_generator(node_name, links, text_content)

class DestinationContentGenerator:
    def __init__(self, destinations_content_tree):
        self.content_tree = destinations_content_tree

    class ContentCollector:
        def __init__(self):
            self.content_map = OrderedDict()

        def __call__(self, node, parent, depth):
            if node.text and node.text.strip() and node.tag:
                title = node.tag.title().replace('_', ' ')
                if title not in self.content_map:
                    self.content_map[title] = [ node.text.strip() ]
                else:
                    self.content_map[title].append(node.text.strip())

    def _print_content_node(self, node, parent, depth):
        if node.text.strip():
            print(node.tag)
            print(node.text.strip())

    def __call__(self, node_id):
        node_collector = self.ContentCollector()
        if node_id is None:
            return node_collector.content_map

        try:
            xpath = "destination[@atlas_id='" + node_id + "']"
            destination_nodes = self.content_tree.findall(xpath)

            for dest in destination_nodes:
                walk(dest, node_collector)

            return node_collector.content_map
        except xml_parser.ParseError as ex:
            print("Problem when parsing destination XML file:", str(ex))
            raise

def create_directory_structure_and_copy_files(output_directory):
    os.mkdir(output_directory)
    os.mkdir(output_directory + '/static')
    lp_req.create_css_file(output_directory + '/static')

# uncomment this the line beginning with @ when running with the memory profiler
@profile
def main():
    args_parser = ap.ArgumentParser()
    args_parser.add_argument('taxonomy_file')
    args_parser.add_argument('destinations_file')
    args_parser.add_argument('output_directory')
    args_parser.add_argument('--force', action='store_true')

    args = args_parser.parse_args()

    try:
        if args.force and os.path.isdir(args.output_directory): #okay sure, we'll just nuke the directory
            shutil.rmtree(args.output_directory)
        # TODO: consider just checking with os.path.exists(), but better errors is more fun.
        elif os.path.isfile(args.output_directory):
            print('Error: A file with the specified directory name (' + args.output_directory + ') already exists.')
            sys.exit(1)
        elif os.path.islink(args.output_directory):
            print('Error: A link with the specified directory name (' + args.output_directory + ') already exists. Refusing to follow it.')
            sys.exit(1)
        elif os.path.ismount(args.output_directory):
            print('Error: A mount point with the specified directory name (' + args.output_directory + ') already exists. Refusing to touch it.')
            sys.exit(1)
        elif os.path.isdir(args.output_directory) and os.listdir(args.output_directory):
            print('Error: Specified output directory already exists and contains files. Refusing to generate files in polluted directory.')
            sys.exit(1)

        create_directory_structure_and_copy_files(args.output_directory)

    except OSError as ex:
        print('Fatal Error:', str(ex))
        sys.exit(1)

    try:
        taxonomy_tree = xml_parser.parse(args.taxonomy_file)
    except (IOError, xml_parser.ParseError) as ex:
        print("Error in taxonomy file(" + args.taxonomy_file + "):", str(ex))
        sys.exit(1)

    try:
        destinations_tree = xml_parser.parse(args.destinations_file)
    except (IOError, xml_parser.ParseError) as ex:
        print("Error in destinations file (" + args.destinations_file + ":)", str(ex))
        sys.exit(1)

    try:
        htmlizer = TaxonomyNodeHtmlizer(
            DestinationContentGenerator(destinations_tree),
            DestinationTemplatePopulator(lp_req.get_template(), args.output_directory)
        )
        walk(taxonomy_tree.getroot(), htmlizer, htmlizer.valid_taxonomy_node)

    except (IOError, xml_parser.ParseError) as ex:
        print("Error encountered during processing, aborting! File generation will be incomplete!", str(ex))
        sys.exit(1)

if __name__ == '__main__':
    main()
    sys.exit(0)

