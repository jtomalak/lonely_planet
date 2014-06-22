# -*- coding: utf-8 -*-

from __future__ import print_function

import sys
import os
import shutil

from lxml import etree as xml_parser
import argparse as ap
import jinja2 as jj
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
    def __init__(self, template, **kwargs):
        no_gen = lambda : None
        self.template = jj.Template(template)
        self.output_directory = './html_result' if 'output_directory' not in kwargs else kwargs['output_directory']
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

    def __call__(self, node_name, node_id, connected_nodes, text_content):
        if not node_name: # kind of silly, maybe assert?
            print('Warning: Attempting to generate content for node with no name.')
            return

        if not text_content:
            print('Warning: No content was found for', node_name)
        else:
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
    def __init__(self, gen):
        self.generator = gen

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

        self.generator(node_name, node.get('atlas_node_id'), links)

class DestinationContentGenerator:
    def __init__(self, destinations_content_nodes, destination_nodes, generator):
        self.content_nodes = destinations_content_nodes
        self.destination_nodes = destination_nodes
        self.generator = generator

    class ContentCollector:
        def __init__(self):
            self.content_map = OrderedDict()

        def find_text_in_all_nodes(self, node):
            if node.text and node.text.strip() and node.tag:
                title = node.tag.title().replace('_', ' ')
                if title not in self.content_map:
                    self.content_map[title] = [ node.text.strip() ]
                else:
                    self.content_map[title].append(node.text.strip())

            for child in node.iterchildren():
                self.find_text_in_all_nodes(child)

            return self.content_map

    def _print_no_content_warning(self, node):
        print(
            'WARNING: Destination node',
            node.get('title'),
            'appears to have no associated taxonomy node, so no content will be generated.'
        )

    def _print_no_tax_node_warning(self, node):
        print(
            'WARNING: Destination node',
            node.get('title'),
            'has a node id that is not present in the taxonomy, so no content will be generated.'
        )

    def process_node(self, node):
        node_id = node.get('atlas_id')

        if not node_id:
            self._print_no_content_warning(node)
            return;

        if node_id not in self.destination_nodes:
            self._print_no_tax_node_warning(node)
            return;

        node_name = self.destination_nodes[node_id]['name']
        connected_nodes = self.destination_nodes[node_id]['children']
        collector = self.ContentCollector()
        text_content = collector.find_text_in_all_nodes(node)

        self.generator(node_name, node_id, connected_nodes, text_content)
        del collector

    @profile
    def parse(self):
        for event, node in self.content_nodes:
            print(mem_usage())
            self.process_node(node)

            node.clear()
            while node.getprevious() is not None:
                del node.getparent()[0]

class TaxonomyNodeTreeBuilder:
    def __init__(self):
        self.nodes = OrderedDict()

    def __call__(self, node_name, node_id, connected_nodes):
        self.nodes[node_id] = {
            'name': node_name,
            'id': node_id,
            'children': connected_nodes
        }

def create_directory_structure_and_copy_files(output_directory):
    os.mkdir(output_directory)
    os.mkdir(output_directory + '/static')
    lp_req.create_css_file(output_directory + '/static')

# uncomment this the line beginning with @ when running with the memory profiler
#@profile
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
        #destinations_tree = xml_parser.parse(args.destinations_file)
        destinations_tree = xml_parser.iterparse(args.destinations_file, tag = 'destination', events = ('end',))
    except (IOError, xml_parser.ParseError) as ex:
        print("Error in destinations file (" + args.destinations_file + ":)", str(ex))
        sys.exit(1)

    try:
        node_tree_gen = TaxonomyNodeTreeBuilder()
        htmlizer = TaxonomyNodeHtmlizer( node_tree_gen )
        walk(taxonomy_tree.getroot(), htmlizer, htmlizer.valid_taxonomy_node)

        html_gen = DestinationTemplatePopulator(lp_req.get_template(), output_directory = args.output_directory)
        content_gen = DestinationContentGenerator(destinations_tree, node_tree_gen.nodes, html_gen)
        content_gen.parse()

    except (IOError, xml_parser.ParseError) as ex:
        print("Error encountered during processing, aborting! File generation will be incomplete!", str(ex))
        sys.exit(1)

if __name__ == '__main__':
    main()
    sys.exit(0)

