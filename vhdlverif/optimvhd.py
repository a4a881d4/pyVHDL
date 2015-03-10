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

import sys
import os # for OS functions
from xml.dom import minidom
from xml.dom.minidom import parse, parseString, getDOMImplementation
import re

# output file
DOMimplement = None
xml_document = None
top_element = None

###############################################################################
# Optimize functions                                                          #
###############################################################################

# main optimize function calls all other
def optimizeXML():
    #optimGenericParams()
    optimSignalDecl()
    optimVarDecl()
    optimFileDecl()
    optimConstDecl()
    optimSignalPar()
    optimVarPar()
    optimConstPar()
    optimIdPar()

###############################################################################
# replaces generic parameters
def optimGenericParams():
    print "replacing generic parameters"
    for entityTag in top_element.getElementsByTagName('entity'):
        idEntity = entityTag.getAttribute('id')
        genericTag = entityTag.getElementsByTagName('generic').item(0)
        for paramTag in genericTag.childNodes:
            idParam = paramTag.getAttribute('id')
            print "- parameter id: " + idParam
            valueTag = paramTag.getElementsByTagName('value').item(0)
            expTag = valueTag.firstChild
            portTag = entityTag.getElementsByTagName('ports').item(0)
            for objTag in portTag.getElementsByTagName('objectExpression'):
                if idParam == objTag.getAttribute('id'):
                    print "-- object id: " + objTag.getAttribute('id')
                    clone = expTag.cloneNode(True)
                    objTag.parentNode.insertBefore(clone, objTag)
                    objTag.parentNode.removeChild(objTag)
            for archTag in top_element.getElementsByTagName('architecture'):
                if idEntity == archTag.getAttribute('entity'):
                    for objTag in archTag. \
                        getElementsByTagName('objectExpression'):
                        if idParam == objTag.getAttribute('id'):
                            print "-- object id: " + objTag.getAttribute('id')
                            clone = expTag.cloneNode(True)
                            objTag.parentNode.insertBefore(clone, objTag)
                            objTag.parentNode.removeChild(objTag)
        # component generic not yet supported

###############################################################################
# optimizes multiple signal declaration identifiers
def optimSignalDecl():
    print "optimizing signal declaration"
    for maintag in top_element.getElementsByTagName('signalDeclaration'):
        mainclone = maintag.cloneNode(True)
        mainclone.removeChild(mainclone.getElementsByTagName('ids').item(0))
        idstag = maintag.getElementsByTagName('ids').item(0)
        for idtag in idstag.childNodes:
            subclone = mainclone.cloneNode(True)
            id = idtag.getAttribute('id')
            print "- signal: " + id
            subclone.setAttribute('id', id)
            maintag.parentNode.insertBefore(subclone, maintag)
        maintag.parentNode.removeChild(maintag)


# optimizes multiple variable declaration identifiers
def optimVarDecl():
    print "optimizing variable declaration"
    for maintag in top_element.getElementsByTagName('variableDeclaration'):
        mainclone = maintag.cloneNode(True)
        mainclone.removeChild(mainclone.getElementsByTagName('ids').item(0))
        idstag = maintag.getElementsByTagName('ids').item(0)
        for idtag in idstag.childNodes:
            subclone = mainclone.cloneNode(True)
            id = idtag.getAttribute('id')
            print "- variable: " + id
            subclone.setAttribute('id', id)
            maintag.parentNode.insertBefore(subclone, maintag)
        maintag.parentNode.removeChild(maintag)

# optimizes multiple constant declaration identifiers
def optimConstDecl():
    print "optimizing constant declaration"
    for maintag in top_element.getElementsByTagName('constantDeclaration'):
        mainclone = maintag.cloneNode(True)
        mainclone.removeChild(mainclone.getElementsByTagName('ids').item(0))
        idstag = maintag.getElementsByTagName('ids').item(0)
        for idtag in idstag.childNodes:
            subclone = mainclone.cloneNode(True)
            id = idtag.getAttribute('id')
            print "- constant: " + id
            subclone.setAttribute('id', id)
            maintag.parentNode.insertBefore(subclone, maintag)
        maintag.parentNode.removeChild(maintag)

# optimizes multiple file declaration identifiers
def optimFileDecl():
    print "optimizing file declaration"
    for maintag in top_element.getElementsByTagName('fileDeclaration'):
        mainclone = maintag.cloneNode(True)
        mainclone.removeChild(mainclone.getElementsByTagName('ids').item(0))
        idstag = maintag.getElementsByTagName('ids').item(0)
        for idtag in idstag.childNodes:
            subclone = mainclone.cloneNode(True)
            id = idtag.getAttribute('id')
            print "- file: " + id
            subclone.setAttribute('id', id)
            maintag.parentNode.insertBefore(subclone, maintag)
        maintag.parentNode.removeChild(maintag)

###############################################################################
# optimizes multiple signal parameter identifiers
def optimSignalPar():
    print "optimizing signal parameter"
    for maintag in top_element.getElementsByTagName('signalParameter'):
        mainclone = maintag.cloneNode(True)
        mainclone.removeChild(mainclone.getElementsByTagName('ids').item(0))
        idstag = maintag.getElementsByTagName('ids').item(0)
        for idtag in idstag.childNodes:
            subclone = mainclone.cloneNode(True)
            id = idtag.getAttribute('id')
            print "- signal: " + id
            subclone.setAttribute('id', id)
            maintag.parentNode.insertBefore(subclone, maintag)
        maintag.parentNode.removeChild(maintag)


# optimizes multiple variable parameter identifiers
def optimVarPar():
    print "optimizing variable parameter"
    for maintag in top_element.getElementsByTagName('variableParameter'):
        mainclone = maintag.cloneNode(True)
        mainclone.removeChild(mainclone.getElementsByTagName('ids').item(0))
        idstag = maintag.getElementsByTagName('ids').item(0)
        for idtag in idstag.childNodes:
            subclone = mainclone.cloneNode(True)
            id = idtag.getAttribute('id')
            print "- variable: " + id
            subclone.setAttribute('id', id)
            maintag.parentNode.insertBefore(subclone, maintag)
        maintag.parentNode.removeChild(maintag)

# optimizes multiple constant parameter identifiers
def optimConstPar():
    print "optimizing constant parameter"
    for maintag in top_element.getElementsByTagName('constantParameter'):
        mainclone = maintag.cloneNode(True)
        mainclone.removeChild(mainclone.getElementsByTagName('ids').item(0))
        idstag = maintag.getElementsByTagName('ids').item(0)
        for idtag in idstag.childNodes:
            subclone = mainclone.cloneNode(True)
            id = idtag.getAttribute('id')
            print "- constant: " + id
            subclone.setAttribute('id', id)
            maintag.parentNode.insertBefore(subclone, maintag)
        maintag.parentNode.removeChild(maintag)

# optimizes multiple id parameter identifiers
def optimIdPar():
    print "optimizing id parameter"
    for maintag in top_element.getElementsByTagName('idParameter'):
        mainclone = maintag.cloneNode(True)
        mainclone.removeChild(mainclone.getElementsByTagName('ids').item(0))
        idstag = maintag.getElementsByTagName('ids').item(0)
        for idtag in idstag.childNodes:
            subclone = mainclone.cloneNode(True)
            id = idtag.getAttribute('id')
            print "- id: " + id
            subclone.setAttribute('id', id)
            maintag.parentNode.insertBefore(subclone, maintag)
        maintag.parentNode.removeChild(maintag)


###############################################################################
# Basic functions                                                             #
###############################################################################

# delete white spaces from file

def deleteWS(file):
    txt = open(file, 'r').read()
    r = re.compile('\n', re.MULTILINE)
    txt = r.sub('', txt)
    r = re.compile('\t')
    txt = r.sub('', txt)
    r = re.compile('>( )*<')
    txt = r.sub('><', txt)
    return txt
    
# parse file in new tree
def parseFile(file):
    dom = minidom.parseString(deleteWS(file))
    top = dom.getElementsByTagName('vhdl').item(0)
    while top.hasChildNodes():
        top_element.appendChild(top.firstChild)

if __name__ == "__main__":
    if len(sys.argv)>1:
        for file_arg in sys.argv[1:]:
            if file_arg.endswith('.xml'):
                print file_arg
                DOMimplement = getDOMImplementation()
                xml_document = DOMimplement.createDocument(None, \
                    "optimalVHDL", None)
                top_element = xml_document.documentElement
                parseFile(file_arg)
                optimizeXML()
                filename = file_arg[:-4]+'.optim.xml'
                xml_file = open(filename, 'w')
                xml_file.write(xml_document.toprettyxml('  '))
                xml_file.close()
                print '------------ done'
            else:
                print file_arg + ' is not valid name file'
    else:
        print >>sys.stderr, 'syntax: %s file.vhd.xml' % sys.argv[0]

