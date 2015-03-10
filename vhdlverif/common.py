import xml.dom.minidom
#! /usr/bin/env python
# vim:ts=4:expandtab:sw=4:tw=0
###############################################################################
#                                                                             #
# Author: Zdenek Rehak <rehak.zdenek@gmail.com>                               #
#                                                                             #
# This program is free software; you can redistribute it and/or modify        #
#   it under the terms of the GNU General Public License as published by      #
#   the Free Software Foundation; either version 2 of the License, or         #
#   (at your option) any later version.                                       #
#   See http://www.gnu.org/licenses/gpl.html for more details.                #
#                                                                             #
###############################################################################
###############################################################################

from xml.dom.minidom import Node
from xml.dom import minidom
from xml.dom.minidom import parse, parseString, getDOMImplementation, Element

# Superclass of all VHDL objects
class VHDLobject(object):
    "Superclass of all vhdl objects"
    # Parent
    parent = None
    # Identifier
    id = ''
    # xml node
    xmlNode = None

    def __init__(self, ID, par):
        self.setID(ID)
        self.setParent(par)

    def getID(self):
        return self.id

    def setID(self, ID):
        self.id = ID

    def getParent(self):
        return self.parent

    def setParent(self, par):
        self.parent = par

    def getXMLNode(self):
        return self.xmlNode

    def setXMLNode(self, xml):
        self.xmlNode = xml

def getFirstReallyChild(xmlNode):
    for obj in xmlNode.childNodes:
        print obj
        if obj is xml.dom.minidom.Element:
            return obj
    return None