# -*- coding: utf-8 -*-

from __future__ import print_function

from lxml import etree as xml_parser
import sys

class ContentParser(object):
    def __init__(self):
        self.text = []

    def start(self, tag, attrib):
        pass
        #print(tag, attrib)

    def end(self, tag):
        pass

    def data(self, data):
        pass
        #if self.is_title:
        #    self.text.append(data.encode('utf-8'))

    def close(self):
        return self.text

def find_text_in_nodes(node):
    if node.text and node.text.strip():
        print(node.tag, node.text)

    for child in node.iterchildren():
        find_text_in_nodes(child)

@profile
def main():
    infile = './sample_files/destinations.xml'
    context = xml_parser.iterparse(infile, tag='destination', events=('end',))

    for event, elem in context:
       print(event, elem.attrib, dir(elem))
       find_text_in_nodes(elem)
       elem.clear()

if __name__ == '__main__':
    main()
    sys.exit(0)

