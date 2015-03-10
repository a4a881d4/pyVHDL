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
from elements import VHDLdesign, VHDLfile
import re


def deleteWS(file):
    txt = open(file, 'r').read()
    r = re.compile('\n', re.MULTILINE)
    txt = r.sub('', txt)
    r = re.compile('\t')
    txt = r.sub('', txt)
    r = re.compile('>( )*<')
    txt = r.sub('><', txt)
    return txt

###############################################################################
# Basic function                                                              #
###############################################################################

if __name__ == "__main__":
    if len(sys.argv)>1:
        for file_arg in sys.argv[1:]:
            design = VHDLdesign('myDesign')
            if file_arg.endswith('optim.xml'):
                print file_arg
                DOMimplement = minidom.parseString(deleteWS(file_arg))
                topElement = DOMimplement.getElementsByTagName('optimalVHDL') \
                    .item(0)
                newFile = VHDLfile(file_arg, topElement, design)
                design.addFile(newFile)
                print '------------ done'
            else:
                print file_arg + ' is not valid name file'
            firstFile = design.getFileList()[0]
            design.setMainFile(firstFile)
            design.setMainArch(firstFile.getArchMap().values()[0])
            filename = file_arg[:-10]+'.dot'
            dot_file = open(filename, 'w')
            dot_file.write(design.checkDependency())
            dot_file.close()
    else:
        print >>sys.stderr, 'syntax: %s file.vhd.optim.xml' % sys.argv[0]

