##############################################################################
#
# Command line interface manager (CLIManager) for FreeRTOS+CLI
# File: CLIManager.py
# This file contains the code of the CLI manager
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


import os
import re
import sys
import fileinput
import socket, errno
#import guipy
from gi.repository import Gtk, GObject	#TODO CHECK
from guipy import *


#Default parameters
CONFIG_FILENAME = "CLIManager.conf" #Configuration file
DefaultIP = "127.0.0.1"		  #Default IP address
DefaultPort = "5005"		  #Default port
DefaultType = "UDP"		  #Default protocol for the connection
DefaultColor = "ColorNone"	  #Default color scheme for the CLI


class ConnectionManagement:

  def __init__(self):
    if os.path.exists(CONFIG_FILENAME) == False:
      #Create default config file
      self.CreateDefaultConfigFile()
    else:
      #Load Connection parameters from existing config file
      self.UDPAddress, self.UDPPort, self.TCPAddress, self.TCPPort = self.GetConnectionsConfigFromFile()
      self.ConnectionType = self.GetConnectionTypeFromFile()

    self.EventHandlerId = None
    self.IsConnected = False
    self.DataHandlerCallback = None


  def Connect(self, callback):
    self.IsConnected = False
    try:
      if self.ConnectionType == "UDP":
	self.socket = socket.socket(socket.AF_INET,
                      socket.SOCK_DGRAM) # UDP
	self.IsConnected = True

      if self.ConnectionType == "TCP":
	self.socket = socket.socket(socket.AF_INET,
                      socket.SOCK_STREAM) # TCP

	self.socket.connect((self.TCPAddress, int(self.TCPPort)))
	self.IsConnected = True

      self.EventHandlerId = GObject.io_add_watch(self.socket, GObject.IO_IN, self.SocketListener)
      self.DataHandlerCallback = callback #Function that will handle datas to display
      return None

    except socket.timeout:
      return "Socket timeout"

    except socket.error, (errno, strerror):
      return("Socket error: " + strerror)


  def Disconnect(self):
    if self.IsConnected:
      self.socket.close()
      self.IsConnected = False

    if self.EventHandlerId != None:
      GObject.source_remove(self.EventHandlerId)
      self.EventHandlerId = None

    
  def Send(self, command):
    if self.ConnectionType == "UDP":
      self.socket.sendto(command, (self.UDPAddress, int(self.UDPPort)))
    elif self.ConnectionType == "TCP":
      self.socket.sendto(command, (self.TCPAddress, int(self.TCPPort)))

    return(self.socket) #for the socket listener


  def Receive(self):
    Data = self.socket.recv( 1024 )
    return Data


  def SocketListener(self, source, condition):
      Data = self.Receive()
      self.DataHandlerCallback(Data)  #Let the GUI handle the data
      if len(Data) > 0:
	return True
      else:
	return False


  def CreateDefaultConfigFile(self):
    #Create the default config file
    with open(CONFIG_FILENAME, 'w') as ConfigFile:
      ConfigFile.write("#Connections\n")
      ConfigFile.write("<UDP:" + DefaultIP + ":" + DefaultPort + "\n" )
      ConfigFile.write("<TCP:" + DefaultIP + ":" + DefaultPort + "\n")
      ConfigFile.write("<Type:" +  DefaultType + "\n")
      ConfigFile.write("#Options\n")
      ConfigFile.write("<Color:" +  DefaultColor + "\n")

    ConfigFile.close()

    #Set default variables
    self.UDPAddress = DefaultIP
    self.UDPPort = DefaultPort
    self.TCPAddress = DefaultIP
    self.TCPPort = DefaultPort
    self.ConnectionType = DefaultType


  def GetConnectionsConfig(self):
    return self.UDPAddress, self.UDPPort, self.TCPAddress, self.TCPPort


  def GetUDPConnectionConfig(self):
    return self.UDPAddress, self.UDPPort


  def GetTCPConnectionConfig(self):
    return self.TCPAddress, self.TCPPort


  def GetConnectionsConfigFromFile(self):

    UDPPattern = re.compile("<UDP:(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}):(.+)$")
    TCPPattern = re.compile("<TCP:(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}):(.+)$")

    #Read the config file and look for the defined patterns
    with open(CONFIG_FILENAME, 'r') as ConfigFile:
      for line in ConfigFile:
	UDPmatch = re.search(UDPPattern,line)
	TCPmatch = re.search(TCPPattern,line)
	if UDPmatch:
	  self.UDPAddress =  UDPmatch.group(1)
	  self.UDPPort = UDPmatch.group(2)
	if TCPmatch:
	  self.TCPAddress =  TCPmatch.group(1)
	  self.TCPPort = TCPmatch.group(2)

      ConfigFile.close()
      return self.UDPAddress, self.UDPPort, self.TCPAddress, self.TCPPort


  def SetConnectionsConfig(self, UDPAddress, UDPPort, TCPAddress, TCPPort):

    UDPPattern = re.compile("<UDP:(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}):(.+)$")
    TCPPattern = re.compile("<TCP:(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}):(.+)$")

    NewConfigUDP = "<UDP:" + UDPAddress + ":" + UDPPort
    NewConfigTCP = "<TCP:" + TCPAddress + ":" + TCPPort

    for line in fileinput.input(CONFIG_FILENAME, inplace=1):
        line = UDPPattern.sub(NewConfigUDP, line)
        line = TCPPattern.sub(NewConfigTCP, line)

	#Avoid having extra blank lines in the config file
	if '\n' in line:
	  line = line.replace("\n", "")
	  print line
	else:
	  print line

    fileinput.close()

    #Update 'local' variables
    self.UDPAddress = UDPAddress
    self.UDPPort = UDPPort
    self.TCPAddress  = TCPAddress
    self.TCPPort = TCPPort


  def SetConnectionType(self, ConnectionType):
    self.ConnectionType = ConnectionType

    TypePattern = re.compile("<Type:(.+)$")

    NewConnectionType = "<Type:" + ConnectionType

    for line in fileinput.input(CONFIG_FILENAME, inplace=1):
      line = TypePattern.sub(NewConnectionType, line)

      #Avoid extra blank lines in the config file
      if '\n' in line:
	line = line.replace("\n", "")
	print line
      else:
	print line

    fileinput.close()


  def GetConnectionType(self):
    return self.ConnectionType


  def GetConnectionTypeFromFile(self):

    TypePattern = re.compile("<Type:(.+)$")

    with open(CONFIG_FILENAME, 'r') as ConfigFile:
      for line in ConfigFile:
	Typematch = re.search(TypePattern,line)
	if Typematch:
	  self.ConnectionType =  Typematch.group(1)

      ConfigFile.close()

    return self.ConnectionType


  def IsConnectionActive(self):
    return self.IsConnected #Tells the GUI if a connection is active



class CLIManager:

  def __init__(self):
    #Create an instance of the connection manager
    self.ConManager = ConnectionManagement()
    self.CommandsSetLoaded = False  #No set loaded
    self.HideEscapeChars = False    #Option not enabled at startup
    self.HideSyntaxAssistant = False #Assistant popover show/hide
    self.CLIColor = self.GetCLIColorFromFile()	#Get color scheme from config file


  def IsCommandsSetLoaded(self):
    return self.CommandsSetLoaded #Tells GUI if a set of commands is loaded


  def SetCommandsSetLoaded(self, value):
    self.CommandsSetLoaded = value


  def GenerateCommandsSetFile(self, filename, liststore):
    #Generate the .set file from the list of commands currently loaded 
    #(Imported from source file)
    with open(filename,"w") as cfile:
      for row in liststore:
	cfile.write('"' + row[0] + '","' + row[2] + '",' + str(row[1]) + '\n')
    cfile.close()
      

  def GetCLIColorFromFile(self):

    Pattern = re.compile("<Color:(.+)$")

    with open(CONFIG_FILENAME, 'r') as ConfigFile:
      for line in ConfigFile:
	match = re.search(Pattern,line)
	if match:
	  CLIColor =  match.group(1)

      ConfigFile.close()

    return CLIColor


  def GetCLIColorConfig(self):
    return self.CLIColor  #Tells the GUI the color scheme to use


  def SetCLIColorConfig(self, value):
    self.CLIColor = value

    Pattern = re.compile("<Color:(.+)$")

    Color = "<Color:" + value

    for line in fileinput.input(CONFIG_FILENAME, inplace=1):
      line = Pattern.sub(Color, line)

      if '\n' in line:
	line = line.replace("\n", "")
	print line
      else:
	print line

    fileinput.close()


  def GetHideEscapeParam(self):
    """ Tells the GUI if the option is enabled """
    return self.HideEscapeChars


  def SetHideEscapeParam(self, value):
    """ Set the option state """
    self.HideEscapeChars = value


  def SetHideEscapeCharColumn(self, liststore):
    #Remove the escape characters \r and \n from the help string and copy it
    #in the 3rd column
    for row in liststore:
      row[3] = row[2].replace("\\n", "")
      row[3] = row[3].replace("\\r", "")


  def GetHideSyntaxAssistantParam(self):
    """ Tells the GUI if the option is enabled """
    return self.HideSyntaxAssistant


  def SetHideSyntaxAssistantParam(self, value):
    """ Set the option state """
    self.HideSyntaxAssistant = value


if __name__ == "__main__":
	
	app = CLIManager()
	win = MainWindow(app)
	win.connect("delete-event", Gtk.main_quit)
	win.show_all()
	Gtk.main()



