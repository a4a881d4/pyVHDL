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

from xml.dom import minidom
from xml.dom.minidom import parse, parseString, getDOMImplementation
from common import *

###############################################################################
# Statements class
class Statement(VHDLobject):
    "Statement class"
    # parent with dependency matrix
    matrixParent = None
    # sensitivity list
    masterList = []

    def __init__(self, ID, xml, par, mpar, lst):
        self.setID(ID)
        self.setXMLNode(xml)
        self.setParent(par)
        self.setMatrixParent(mpar)
        self.masterList = lst[:]

    def getMatrixParent(self):
        return self.matrixParent

    def setMatrixParent(self, mpar):
        self.matrixParent = mpar

    def addMaster(self, master):
        self.masterList.append(master)

    def getMasterList(self):
        return self.masterList

    def getExpressions(self, xmlNode):
        exprs = []
        for objTag in xmlNode.childNodes:
            t = objTag.localName
            if t == "logicalExpression" or t == "relationalExpression" or \
                t == "shiftExpression" or t == "addingExpression" or \
                t == "multiplyingExpression"  or t == "exponentialExpression" \
                or t == "prefixExpression" or t == "constantExpression"  or \
                t == "newExpression" or t == "timeExpression" or \
                t == "objectExpression"  or t == "recordExpression"  or \
                t == "aggregateExpression":
                    exprs.append(objTag)
        return exprs

# Parallel statements class
class ParStmts(Statement):
    "Parallel Statements class"

    def checkDependency(self):
        for parStmtTag in self.getXMLNode().childNodes:
            type = parStmtTag.localName
            if type == "blockParallelStatement":
#                print type + " not supported"
                pass
            elif type == "processParallelStatement":
                processPS = ProcessParStmt(parStmtTag.getAttribute('label'), \
                    parStmtTag, self, self.getMatrixParent(), \
                    self.getMasterList())
                processPS.checkDependency()
            elif type == "procedureParallelStatement":
#                print type + " not supported"
                pass
            elif type == "assignParallelStatement":
                assignPS = AssignParStmt(parStmtTag.getAttribute('label'), \
                    parStmtTag, self, self.getMatrixParent(), \
                    self.getMasterList())
                assignPS.checkDependency()
            elif type == "assertParallelStatement":
#                print type + " not supported"
                pass
            elif type == "selectParallelStatement":
#                print type + " not supported"
                pass
            elif type == "componentParallelStatement":
                compPS = CompParStmt(parStmtTag.getAttribute('label'), \
                    parStmtTag, self, self.getMatrixParent(), \
                    self.getMasterList())
                compPS.checkDependency()
            elif type == "entityParallelStatement":
#                print type + " not supported"
                pass
            elif type == "configurationParallelStatement":
#                print type + " not supported"
                pass
            elif type == "configurationParallelStatement":
#                print type + " not supported"
                pass
            elif type == "ifParallelStatement":
                ifPS = IfParStmt(parStmtTag.getAttribute('label'), \
                    parStmtTag, self, self.getMatrixParent(), \
                    self.getMasterList())
                ifPS.checkDependency()
            elif type == "forParallelStatement":
                forPS = ForParStmt(parStmtTag.getAttribute('label'), \
                    parStmtTag, self, self.getMatrixParent(), \
                    self.getMasterList())
                forPS.checkDependency()


# Process parallel statements class
class ProcessParStmt(Statement):
    "Process Parallel Statements class"

    def checkDependency(self):
        for objTag in self.getXMLNode().childNodes:
            type = objTag.localName
            if type == "range" or type == "parameters":
                for oTag in objTag.getElementsByTagName('objectExpression'):
                    self.addMaster(oTag.getAttribute('id'))
        seqStmtsTag = self.getXMLNode(). \
            getElementsByTagName('sequentialStatements').item(0)
        seqStmt = SeqStmts(seqStmtsTag.getAttribute('label'), seqStmtsTag, \
            self, self.matrixParent, self.masterList)
        seqStmt.checkDependency()


# Assign parallel statements class
class AssignParStmt(Statement):
    "Assign Parallel Statements class"

    def checkDependency(self):
        dependList = []
        for objTag in self.getXMLNode().childNodes:
            type = objTag.localName
            if type == "objectExpression":
                dependList.append(objTag.getAttribute('id'))
#                print objTag.getAttribute('id')
            elif type == "recordExpression" or type == "aggregateExpression":
                for oTag in objTag.getElementsByTagName('objectExpression'):
                    self.addMaster(oTag.getAttribute('id'))
        valuesList = self.getXMLNode().getElementsByTagName('signalValue')
        for valueTag in valuesList:
            for objTag in valueTag.getElementsByTagName('objectExpression'):
                self.addMaster(objTag.getAttribute('id'))
#                print objTag.getAttribute('id')
        for id in dependList:
            self.getMatrixParent().setDep(self.getMasterList(), id)


# Component parallel statements class
class CompParStmt(Statement):
    "Component Parallel Statements class"

    def checkDependency(self):
        dependList = []
#        portMapTag = self.getXMLNode().getElementsByTagName('portMap').item(0)
#        for mapTag in portMapTag.getElementsByTagName('map'):
#            for objTag in mapTag.childNodes:
#                if objTag.localName == 'objectExpression':
#                    objList.append(objTag.getAttribute('id'))
#            if objList.item(1) != None:
#                if obj in self.getMatrixParent().
#
##            if type == "objectExpression":
#                dependList.append(objTag.getAttribute('id'))
##                print objTag.getAttribute('id')
#            elif type == "recordExpression" or type == "aggregateExpression":
#                for oTag in objTag.getElementsByTagName('objectExpression'):
#                    self.addMaster(oTag.getAttribute('id'))
#        valuesList = self.getXMLNode().getElementsByTagName('signalValue')
#        for valueTag in valuesList:
#            for objTag in valueTag.getElementsByTagName('objectExpression'):
#                self.addMaster(objTag.getAttribute('id'))
##                print objTag.getAttribute('id')
#        for id in dependList:
#            self.getMatrixParent().setDep(self.getMasterList(), id)


# If parallel statements class
class IfParStmt(Statement):
    "If Parallel Statements class"

    def checkDependency(self):
        for exprTag in self.getExpressions(self.getXMLNode()):
            for objTag in exprTag.getElementsByTagName('objectExpression'):
                self.addMaster(objTag.getAttribute('id'))
        generateTag = self.getXMLNode().getElementsByTagName('generate').item(0)
        parStmtsTag = generateTag. \
            getElementsByTagName('parallelStatements').item(0)
        parStmt = ParStmts(parStmtsTag.getAttribute('label'), parStmtsTag, \
            self, self.matrixParent, self.masterList)
        parStmt.checkDependency()

# For parallel statements class
class ForParStmt(Statement):
    "For Parallel Statements class"

    def checkDependency(self):
        generateTag = self.getXMLNode().getElementsByTagName('generate').item(0)
        parStmtsTag = generateTag. \
            getElementsByTagName('parallelStatements').item(0)
        parStmt = ParStmts(parStmtsTag.getAttribute('label'), parStmtsTag, \
            self, self.matrixParent, self.masterList)
        parStmt.checkDependency()

###############################################################################
# Sequential statements class
class SeqStmts(Statement):
    "Sequential Statements class"

    def checkDependency(self):
        for seqStmtTag in self.getXMLNode().childNodes:
            type = seqStmtTag.localName
            if type == "waitSequentialStatement":
#                print type + " not supported"
                pass
            elif type == "assertSequentialStatement":
#                print type + " not supported"
                pass
            elif type == "reportSequentialStatement":
#                print type + " not supported"
                pass
            elif type == "signalAssignSequentialStatement":
                sigAssignSS = SigAssSeqStmt(seqStmtTag.getAttribute('label'), \
                    seqStmtTag, self, self.getMatrixParent(), \
                    self.getMasterList())
                sigAssignSS.checkDependency()
            elif type == "variableAssignSequentialStatement":
#                print type + " not supported"
                pass
            elif type == "procedureSequentialStatement":
#                print type + " not supported"
                pass
            elif type == "ifSequentialStatement":
                ifSS = IfSeqStmt(seqStmtTag.getAttribute('label'), \
                    seqStmtTag, self, self.getMatrixParent(), \
                    self.getMasterList())
                ifSS.checkDependency()
            elif type == "caseSequentialStatement":
#                print type + " not supported"
                pass
            elif type == "whileSequentialStatement":
#                print type + " not supported"
                pass
            elif type == "forSequentialStatement":
#                print type + " not supported"
                pass
            elif type == "nextSequentialStatement":
#                print type + " not supported"
                pass
            elif type == "exitSequentialStatement":
#                print type + " not supported"
                pass
            elif type == "returnSequentialStatement":
#                print type + " not supported"
                pass
            elif type == "nullSequentialStatement":
#                print type + " not supported"
                pass

# Signal assign sequential statements class
class SigAssSeqStmt(Statement):
    "Signal Assign Sequential Statements class"

    def checkDependency(self):
        dependList = []
        for objTag in self.getXMLNode().childNodes:
            type = objTag.localName
            if type == "objectExpression":
                dependList.append(objTag.getAttribute('id'))
#                print objTag.getAttribute('id')
            elif type == "recordExpression" or type == "aggregateExpression":
                for oTag in objTag.getElementsByTagName('objectExpression'):
                    self.addMaster(oTag.getAttribute('id'))
        valuesList = self.getXMLNode().getElementsByTagName('signalValue')
        for valueTag in valuesList:
            for objTag in valueTag.getElementsByTagName('objectExpression'):
                self.addMaster(objTag.getAttribute('id'))
#                print objTag.getAttribute('id')
        for id in dependList:
            self.getMatrixParent().setDep(self.getMasterList(), id)

# If sequential statements class
class IfSeqStmt(Statement):
    "If Sequential Statements class"

    def checkDependency(self):
        for exprTag in self.getExpressions(self.getXMLNode()):
            for objTag in exprTag.getElementsByTagName('objectExpression'):
                self.addMaster(objTag.getAttribute('id'))
        thenTag = self.getXMLNode().getElementsByTagName('then').item(0)
        seqStmtsTag = thenTag. \
            getElementsByTagName('sequentialStatements').item(0)
        seqStmt = SeqStmts(seqStmtsTag.getAttribute('label'), seqStmtsTag, \
            self, self.matrixParent, self.masterList)
        seqStmt.checkDependency()
        for elseifTag in self.getXMLNode().getElementsByTagName('elseif'):
            for exprTag in self.getExpressions(elseifTag):
                for objTag in exprTag.getElementsByTagName('objectExpression'):
                    self.addMaster(objTag.getAttribute('id'))
            seqStmtsTag = elseifTag. \
                getElementsByTagName('sequentialStatements').item(0)
            seqStmt = SeqStmts(seqStmtsTag.getAttribute('label'), seqStmtsTag, \
                self, self.matrixParent, self.masterList)
            seqStmt.checkDependency()
        elseTag = self.getXMLNode().getElementsByTagName('else').item(0)
        if elseTag != None:
            seqStmtsTag = elseTag. \
                getElementsByTagName('sequentialStatements').item(0)
            seqStmt = SeqStmts(seqStmtsTag.getAttribute('label'), seqStmtsTag, \
                self, self.matrixParent, self.masterList)
            seqStmt.checkDependency()
            