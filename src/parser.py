##############################################################################
#
# Command line interface manager (CLIManager) for FreeRTOS+CLI
# File: parser.py
# This file contains the parser to extract the set of commands from the source.
# This is based on pyparsing module.
# See: sourceforge.net/projects/pyparsing
#
# This software is released under the MIT licence
#
# Copyright (c) 2015 Jean-Baptiste Quelard
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
###############################################################################
#!/usr/bin/python

from pyparsing import *


class CmdParser:

  def __init__(self):

    #define grammar for parsing source .c file
    LEFT_BRACE,RIGHT_BRACE,EQ,COMMA = map(Suppress,"{}=,")
    _def = Suppress('static const CLI_Command_Definition_t')
    self.sign = oneOf("+ -")
    self.integer = Word(nums)
    signed_int = Combine(Optional(self.sign) + self.integer)
    CmdString = dblQuotedString(alphanums+"_")
    CmdHelp = dblQuotedString(alphanums+"_")
    identifier = Word(alphas,alphanums+'_')
    comment = Word(alphas,alphanums+'_')
    comment.ignore(cStyleComment)

    Declaration = Group( _def + identifier + EQ + LEFT_BRACE + \
			      CmdString('NameString').setParseAction(removeQuotes)  + \
			      COMMA + \
			      Optional(comment) + \
			      CmdHelp('Help').setParseAction(removeQuotes)  + \
			      COMMA + \
			      identifier + \
			      COMMA + \
			      Optional(comment) + \
			      signed_int('Args').setParseAction( lambda s,l,t: [ int(t[0]) ] ) + \
			      Optional(comment) + \
			      RIGHT_BRACE )

    self.CommandDefinition = Declaration('Command')
    self.CommandDefinition.ignore(cStyleComment)

    #define grammar for parsing the set of commands (.set file)
    line = Group( CmdString('NameString').setParseAction(removeQuotes) + \
			  COMMA + \
			  CmdHelp('Help').setParseAction(removeQuotes) + \
			  COMMA + \
			  signed_int('Args').setParseAction( lambda s,l,t: [ int(t[0]) ] ))
    
    self.Command = line('Command')


  def CmdParse(self, filename, source, liststore):

    #Open and read the file
    with open(filename,"r") as cfile:
      FileLines = cfile.readlines()
    cfile.close()

    FileContent = "".join(FileLines)

    # Set the string to parse
    if source == 'Source':
      ScannedString = self.CommandDefinition.scanString(FileContent)
    elif source == 'List':
      ScannedString = self.Command.scanString(FileContent)

    for item,start,stop in ScannedString:
      if len(liststore) != 0:
	Duplicate = False # (Re)Init duplicate flag
	for Row in liststore:
	  if Row[0] == item.Command.NameString:
	    Duplicate = True
	if Duplicate is False:	# Added to the list only if not a duplicate
	  liststore.append((item.Command.NameString, \
			    item.Command.Args, \
			    item.Command.Help, \
			    ""))
      else: # No command in the list yet
	liststore.append((item.Command.NameString, \
			  item.Command.Args, \
			  item.Command.Help, \
			  ""))


  def ParseHelpString(self, string, nbargs):
    """ Parse the help string to find command's arguments """

    if nbargs == 0:
      return None #No assistance can be provided to populate arguments

    # Define Grammar
    Wrd = Word(alphas,alphanums+'_')
    StringArg = QuotedString("<",endQuoteChar=">")
    BoolArg = QuotedString("[",endQuoteChar="]")

    _HelpString = Group(  ZeroOrMore(Wrd) + Optional(StringArg('StringParam')) + \
					    Optional(BoolArg('BoolParam')))

    HelpString = _HelpString('Str')

    Arglist = []
    for item,start,stop in HelpString.scanString(string):
      if item.Str.StringParam != "":
	Arglist.append(item.Str.StringParam)
      if item.Str.BoolParam != "":
	Arglist.append(item.Str.BoolParam)

    return Arglist


