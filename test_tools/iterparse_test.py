# -*- coding: utf-8 -*-

from __future__ import print_function

from lxml import etree as xml_parser
import sys
import argparse as ap

class ContentParser(object):
    def __init__(self):
        self.text = []

    def start(self, tag, attrib):
        pass

    def end(self, tag):
        pass

    def data(self, data):
        pass

    def close(self):
        return self.text

def find_text_in_elems(elem, show = False):
    if elem.text and elem.text.strip() and show:
        print(elem.tag, elem.text)

    for child in elem.iterchildren():
        find_text_in_elems(child, show)

#@profile
def main():
    args_parser = ap.ArgumentParser()
    args_parser.add_argument('infile')
    args_parser.add_argument('--verbose', action='store_true')

    args = args_parser.parse_args()
    context = xml_parser.iterparse(args.infile, tag='destination', events=('end',))

    node_count = 0
    for event, elem in context:
        find_text_in_elems(elem, args.verbose)
        elem.clear()
        for ancestor in elem.xpath('ancestor-or-self::*'):
            while ancestor.getprevious() is not None:
                del ancestor.getparent()[0]

        node_count += 1
        if node_count % 10000 == 0:
            print('Processed', node_count, 'nodes.')

    del context
    print('Done.')

if __name__ == '__main__':
    main()
    sys.exit(0)

