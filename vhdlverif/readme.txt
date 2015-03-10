****************
* GENERAL info *
****************

Requirements
============
POSIX OS, Python>=2.3.
Library NumPy

VHDL Code Examples
==================
examples/
  cnt.vhd
  crc32_8b.vhd
  packet_splitter.vhd


Documentation
=============
doc/
  vhdl.xsd (xml schema of VHD2XML output)
  optimvhdl.xsd (xml schema of OPTIMVHD output)


Installation
============
There is no installation, just unpack it and it works.

$ tar xzf vhdlverif-0.2-alpha.tar.gz
$ cd vhdlverif/

$ ./vhd2xml.py file(s)
file .. vhdl file

$ ./optimvhd.py file(s)
file .. xml file

$ ./analysevhd.py file(s)
file .. xml file



****************
* VHD2XML tool *
****************

Version history
===============

Version 1.1 beta (29/10/2008)
-----------------------------

Bug fix:
- id & object elements (many changes of grammar and xml schema):
  - constant, variable, signal and file declaration
  - type identifier
  - object, record, aggregate expression
  - procedure, function call
  - signal, variable assignment
- declaration semicolon duplicate
- missing optional declaration list in function and procedure declaration
- incomplete use clause

New features:
- multiple file arguments
- xml schema validation tags



Version 1.0 beta (01/10/2008)
-----------------------------
- first release (full functionality)



*****************
* OPTIMVHD tool *
*****************

Version history
===============

Version 0.1 alpha (15/01/2009)
------------------------------

New features:
- optimize multiple signal declaration
- optimize multiple variable, constant and file declaration
- optimize multiple declaration parameters





*******************
* ANALYSEVHD tool *
*******************

Version history
===============

Version 0.2 alpha (28/03/2009)
------------------------------

New features:
- new OO model
- detection signal dependency


Version 0.1 alpha (27/02/2009)
------------------------------

New features:
- entity ports detection
- architecture signal detection
- architecture component detection



