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
from common import *
from statements import *
from numpy import *

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
  
    def setID(self, ID):
        self.id = ID

    def getID(self):
        return self.id

    def setParent(self, par):
        self.parent = par

    def getParent(self):
        return self.parent

    def setXMLNode(self, xml):
        self.xmlNode = xml

    def getXMLNode(self):
        return self.xmlNode

# VHDL Desgin class
class VHDLdesign(VHDLobject):
    "File class"
    # File list
    fileList = []
    mainFile = None
    mainArch = None

    def __init__(self, ID):
        self.fileList = []
        self.mainFile = None
        self.mainArch = None
        self.setID(ID)
        
    def addFile(self, f):
        self.fileList.append(f)

    def getFileList(self):
        return self.fileList

    def setMainFile(self, mf):
        self.mainFile = mf

    def getMainFile(self):
        return self.mainFile

    def setMainArch(self, ma):
        self.mainArch = ma

    def getMainArch(self):
        return self.mainArch

    def checkDependency(self):
        return self.mainArch.checkDependency()

# File class
class VHDLfile(VHDLobject):
    "File class"
    # Entity list
    entityMap = {}
    # Architecture list
    archMap = {}

    def __init__(self, ID, xml, par):
        self.entityMap = {}
        self.archMap = {}
        self.setID(ID)
        self.setXMLNode(xml)
        self.setParent(par)
        self.loadStructure()

    def addEntity(self, entity):
        self.entityMap[entity.getID()] = entity

    def getEntityMap(self):
        return self.entityMap

    def getEntityByName(self, name):
        return self.entityMap[name]

    def addArch(self, arch):
        self.archMap[arch.getID()] = arch

    def getArchMap(self):
        return self.archMap

    def getArchByName(self, name):
        return self.archMap[name]

    def loadStructure(self):
        self.loadLibraries()
        self.loadEntities()
        self.loadArchs()

    def loadLibraries(self):
        "Not yet supported"

    def loadEntities(self):
        for entityTag in self.getXMLNode().getElementsByTagName('entity'):
            idEntity = str(entityTag.getAttribute('id'))
            entityItem = Entity(idEntity, entityTag, self)
            print "analyse entity: " + idEntity
            portsTag = entityTag.getElementsByTagName('ports').item(0)
            for portTag in portsTag.getElementsByTagName('port'):
                idPort = str(portTag.getAttribute('id'))
                dirPort = str(portTag.getAttribute('io'))
                print "- port " + dirPort + ": " + idPort
                if dirPort == 'in':
                    portItem = InPort(idPort, entityItem)
                    entityItem.addInPort(portItem)
                elif dirPort == 'out':
                    portItem = OutPort(idPort, entityItem)
                    entityItem.addOutPort(portItem)
                elif dirPort == 'out':
                    portItem = InOutPort(idPort, entityItem)
                    entityItem.addInoutPort(portItem)
            self.addEntity(entityItem)

    def loadArchs(self):
        for archTag in self.getXMLNode().getElementsByTagName('architecture'):
            idArch = str(archTag.getAttribute('id'))
            idArchEnt = str(archTag.getAttribute('entity'))
            archItem = Architecture(idArch, archTag, self, idArchEnt)
            print "analyse architecture: " + idArch + " of entity: " + idArchEnt
            declTag = archTag.getElementsByTagName('declarations').item(0)
            for sigTag in declTag.getElementsByTagName('signalDeclaration'):
                idSig = str(sigTag.getAttribute('id'))
                signalItem = Signal(idSig, archItem)
                print "- signal: " + idSig
                archItem.addSignal(signalItem)
            for compTag in declTag.getElementsByTagName('componentDeclaration'):
                idComp = str(compTag.getAttribute('id'))
                compItem = Component(idComp, compTag, archItem)
                print "- component: " + idComp
                portsTag = compTag.getElementsByTagName('ports').item(0)
                for portTag in portsTag.getElementsByTagName('port'):
                    idPort = str(portTag.getAttribute('id'))
                    dirPort = str(portTag.getAttribute('io'))
                    print "- port " + dirPort + ": " + idPort
                    if dirPort == 'in':
                        portItem = InPort(idPort, compItem)
                        compItem.addInPort(portItem)
                    elif dirPort == 'out':
                        portItem = OutPort(idPort, compItem)
                        compItem.addOutPort(portItem)
                    elif dirPort == 'out':
                        portItem = InOutPort(idPort, compItem)
                        compItem.addInoutPort(portItem)
                archItem.addComp(compItem)
            self.addArch(archItem)

# VHDL interface class - Entity or Component
class VHDLinterfaceObject(VHDLobject):
    "VHDL interface class - Entity or Component"
    # Parameter (Generic) list
    parMap = {}
    # Port list
    inPortMap = {}
    outPortMap = {}
    inoutPortMap = {}
    
    def __init__(self, ID, xml, par):
        self.parMap = {}
        self.inPortMap = {}
        self.outPortMap = {}
        self.inoutPortMap = {}
        self.setID(ID)
        self.setXMLNode(xml)
        self.setParent(par)

    def addParameter(self, par):
        self.parMap[par.getID()] = par

    def getParMap(self):
        return self.parMap

    def getParByName(self, name):
        return self.parMap[name]

    def addInPort(self, port):
        self.inPortMap[port.getID()] = port

    def getInPortMap(self):
        return self.inPortMap

    def getInPortByName(self, name):
        return self.inPortMap[name]

    def addOutPort(self, port):
        self.outPortMap[port.getID()] = port

    def getOutPortMap(self):
        return self.outPortMap

    def getOutPortByName(self, name):
        return self.outPortMap[name]

    def addInoutPort(self, port):
        self.inoutPortMap[port.getID()] = port

    def getInoutPortMap(self):
        return self.inoutPortMap

    def getInoutPortByName(self, name):
        return self.inoutPortMap[name]

# Entity class
class Entity(VHDLinterfaceObject):
    "Entity class"


# Architecture class
class Architecture(VHDLobject):
    "Architecture class"
    # Entity of architecture
    entity = None
    # Signal list
    signalMap = {}
    # Component list
    compMap = {}
    # Dependency matrix
    depMat = None
    resultMat = None
    matrixMap = {}
    inMatrixMap = {}
    outMatrixMap = {}
    sigMatrixMap = {}
    idList = []
    resultString = None

    def __init__(self, ID, xml, par, ent):
        self.signalMap ={}
        self.compMap = {}
        self.depMat = None
        self.resultMat = None
        self.matrixMap = {}
        self.inMatrixMap = {}
        self.outMatrixMap = {}
        self.sigMatrixMap = {}
        self.setID(ID)
        self.setXMLNode(xml)
        self.setParent(par)
        self.setEntity(ent)
        self.idList = []
        self.resultString = ''
        
    def getEntity(self):
        return self.entity

    def setEntity(self, ent):
        self.entity = self.getParent().getEntityByName(ent)

    def addSignal(self, sig):
        self.signalMap[sig.getID()] = sig

    def getSignalMap(self):
        return self.signalMap

    def getSignalByName(self, name):
        return self.signalMap[name]

    def addComp(self, comp):
        self.compMap[comp.getID()] = comp

    def getCompMap(self):
        return self.compMap

    def createDepMatrix(self):
        count = 0
        print "in ports"
        for p in self.getEntity().getInPortMap().values():
            print "- " + p.getID()
            self.inMatrixMap[p.getID()] = count
            self.matrixMap[p.getID()] = count
            self.idList.append(p.getID())
            count = count + 1
        print "out ports"
        for p in self.getEntity().getOutPortMap().values():
            print "- " + p.getID()
            self.outMatrixMap[p.getID()] = count
            self.matrixMap[p.getID()] = count
            self.idList.append(p.getID())
            count = count + 1
        print "signals"
        for s in self.getSignalMap().values():
            print "- " + s.getID()
            self.sigMatrixMap[s.getID()] = count
            self.matrixMap[s.getID()] = count
            self.idList.append(s.getID())
            count = count + 1
        self.depMat = matrix(identity(count, int))
        self.printDepMatrix(True)
#        for i in range(0, len(self.idList)-1):
#            print str(i) + ": " + self.idList[i]

    def getDepMatrix(self):
        return self.depMat

    def printDepMatrix(self, raw):
        if raw:
            print self.depMat

    def setDep(self, master, slave):
        if self.matrixMap.has_key(slave):
            slaveNbr = self.matrixMap[slave]
            for id in master:
                if self.matrixMap.has_key(id):
                    self.depMat[self.matrixMap[id],slaveNbr] = 1
#                    print id + " -> " + slave

#                else:
#                    print 'signal or port ' + id + ' not defined'
#        else:
#            print 'signal or port ' + id + ' not defined'

    def countDepFromMatrix(self):
        changing = True
        tempMat = self.depMat * matrix(identity(len(self.idList), int))
        self.resultMat = self.depMat * matrix(identity(len(self.idList), int))
        while changing:
            self.resultMat = tempMat * tempMat
            print self.resultMat
            changing = False
            for i in range(0, len(self.idList)-1):
                for j in range(0, len(self.idList)-1):
                    if self.resultMat[i,j] != 0:
                        self.resultMat[i,j] = 1
                    if self.resultMat[i,j] != tempMat[i,j]:
                        changing = True
            tempMat = self.resultMat

    def depMatrixToString(self):

        def add(s):
            self.resultString = self.resultString + s + '\n'

        add('digraph ' + self.getID() + ' {')
        add('label = "Architecture ' + self.getID().upper() + \
            ' of entity ' + self.getEntity().getID().upper() + '";')
        for i in self.inMatrixMap.values():
            add('   ' + self.idList[i] + ' [shape=box];')
        for i in self.outMatrixMap.values():
            add('   ' + self.idList[i] + ' [shape=ellipse];')
        for i in self.inMatrixMap.values():
            for j in self.outMatrixMap.values():
                if self.resultMat[i,j] != 0:
                    add('   ' + self.idList[i] + ' -> ' + self.idList[j] + ';')
        add('}')
        return self.resultString

    def checkDependency(self):
        print "checking dependency"
        self.createDepMatrix()
        parStmtsTag = self.getXMLNode(). \
            getElementsByTagName('parallelStatements').item(0)
        parStmt = ParStmts(self.getID(), parStmtsTag, self, self, [])
        parStmt.checkDependency()
        self.countDepFromMatrix()
#        self.printDepMatrix(True)
        return self.depMatrixToString()

# Component class
class Component(VHDLinterfaceObject):
    "Component class"


# Port class
class Port(VHDLobject):
    "Port class"
    # Port direction (in/out/inout)
    io = ''
    
    def __init__(self, ID, par, IO):
        self.setID(ID)
        self.setParent(par)
        self.setIO(IO)

    def setIO(self, IO):
        self.io = IO

    def getIO(self):
        return self.io

# In Port class
class InPort(Port):
    "In Port class"
    
    def __init__(self, ID, par):
        self.setID(ID)
        self.setParent(par)
        self.io = 'in'

# Out Port class
class OutPort(Port):
    "Out Port class"
    
    def __init__(self, ID, par):
        self.setID(ID)
        self.setParent(par)
        self.io = 'out'

# InOut Port class
class InOutPort(Port):
    "InOut Port class"
    
    def __init__(self, ID, par):
        self.setID(ID)
        self.setParent(par)
        self.io = 'inout'

# Parameter class
class Parameter(VHDLobject):
    "Parameter class"
    value = ''

    def setValue(self, val):
        self.value = val

    def getVaule(self):
        return self.value

# Signal class
class Signal(VHDLobject):
    "Signal class"


