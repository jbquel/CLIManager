##############################################################################
#
# Command line interface manager (CLIManager) for FreeRTOS+CLI
# File: gui.py
# This file defines the user interface and its behavior. The following code is
# based on pyGTK3.
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

from gi.repository import Gtk
from parser import *
from CLIManager import * 

import os
import sys


UI_MENU = """
<ui>
  <menubar name='MenuBar'>    
    <menu action='FileMenu'>
      <menuitem action='FileOpen' />
      <menuitem action='ImportFromSource' />
      <menuitem action='SaveAs' />
      <separator/>
      <menuitem action='FileQuit' />
    </menu>
    <menu action='ConnectionsMenu'>
      <menu action='SelectConnection'>
	<menuitem action='SelectUDP' />
	<menuitem action='SelectTCP' />
      </menu>
      <menuitem action='EditConnection' />
      <menuitem action='Connect' />
      <menuitem action='Disconnect' />
    </menu>
    <menu action='OptionsMenu'>
      <menu action='CLIColor'>
	<menuitem action='ColorNone' />
	<menuitem action='ColorSea' />
	<menuitem action='ColorConsole' />
      </menu>
      <menuitem action='HideEscapeChar' />
    </menu>
  </menubar>
  <toolbar name='ToolBar'>
    <toolitem action='FileOpen' />
    <toolitem action='ImportFromSource' />
    <toolitem action='SaveAs' />
    <separator/>
    <toolitem action='Connect' />
    <toolitem action='Disconnect' />
    <separator/>
    <toolitem action='ClearConsole' />
  </toolbar>
</ui>
"""

_APP_NAME = "CLI Manager for FreeRTOS"


class MainWindow(Gtk.Window):
  """ Application main window """

  def __init__(self, app):
    Gtk.Window.__init__(self, title = _APP_NAME)
    self.set_border_width(10)
    self.set_default_size(900, 700)

    self.CLIManager = app

    #Create grid
    self.grid = Gtk.Grid()
    self.grid.set_column_homogeneous(True)
    self.grid.set_row_homogeneous(False)	
    self.grid.set_row_spacing(10)		
    self.grid.set_column_spacing(10)	
    self.add(self.grid)

    #Liststore which contains the list of commands
    self.CommandsListstore = Gtk.ListStore(str, int, str, str)
    #Liststore which contains the CLI
    self.CLIListstore = Gtk.ListStore(str, str, str)

    ActionGroup = Gtk.ActionGroup("MenuActions")
    self.AddFileMenuActions(ActionGroup)
    self.AddConnectionsMenuActions(ActionGroup)
    self.AddOptionsMenuActions(ActionGroup)

    UIManager = self.CreateUIManager()
    UIManager.insert_action_group(ActionGroup)

    #Menu and toolbar
    self.Menubar = UIManager.get_widget("/MenuBar")
    self.Toolbar = UIManager.get_widget("/ToolBar")

    self.AppStatusbar = Statusbar(self)

    #Create text entry
    self.CmdEntry = Gtk.Entry()
    self.CmdEntry.set_text("Command")
    self.CmdEntry.set_icon_from_stock(Gtk.EntryIconPosition.PRIMARY, Gtk.STOCK_EXECUTE)
    self.CmdEntry.connect("activate", self.SendCommand)

    #create the treeview for the set of commands
    self.CmdSetTreeview = Gtk.TreeView.new_with_model(self.CommandsListstore)
    for i, Title in enumerate(["Command", " Nb Arguments", "Help string", "Help string"]):
      CmdSetRenderer = Gtk.CellRendererText()
      column = Gtk.TreeViewColumn(Title, CmdSetRenderer, text=i)
      self.CmdSetTreeview.append_column(column)

    #create the treeview for the CLI
    self.CLITreeview = Gtk.TreeView.new_with_model(self.CLIListstore)
    CLIRenderer = Gtk.CellRendererText()
    CLIColumn = Gtk.TreeViewColumn("Interface", CLIRenderer, text=0, background=1, foreground=2)
    self.CLITreeview.append_column(CLIColumn)

    #Create send button
    self.SendButton = Gtk.Button("Send")
    self.SendButton.connect("clicked", self.SendCommand)

    #Scrolled windows
    self.CmdSetScrollWindow = Gtk.ScrolledWindow()
    self.CmdSetScrollWindow.set_vexpand(True)
    self.CLIScrollWindow = Gtk.ScrolledWindow()
    self.CLIScrollWindow.set_vexpand(True)

    #Layout of the main window
    self.grid.attach(self.Menubar, 0, 0, 8, 1)
    self.grid.attach(self.Toolbar, 0, 1, 8, 1)
    self.grid.attach(self.CLIScrollWindow, 0, 2, 8, 15)
    self.grid.attach(self.CmdEntry, 0, 17, 7, 1)
    self.grid.attach(self.SendButton, 7, 17, 1, 1)
    self.grid.attach(self.CmdSetScrollWindow, 0, 18, 8, 15)
    self.grid.attach(self.AppStatusbar, 0, 33, 8, 1)

    self.CmdSetScrollWindow.add(self.CmdSetTreeview)
    self.CLIScrollWindow.add(self.CLITreeview)

    #The entry selected in the list is used to populate the command entry
    CommandSelected = self.CmdSetTreeview.get_selection()
    CommandSelected.connect("changed", self.OnCommandSelected)

    #Allow completion of command from the command list
    Completion = Gtk.EntryCompletion()
    Completion.set_model(self.CommandsListstore)
    self.CmdEntry.set_completion(Completion)
    Completion.set_text_column(0)

    #Add the connection status to the main title of the window
    self.SetConnectionStatusInTitle()

    # Hide the column where the escape chars are displayed
    self.CmdSetTreeview.get_column(3).set_visible(False)

    #Set colors for the CLI
    self.SetCLIColor(self.CLIManager.GetCLIColorConfig())
	  
    self.show_all()


  def OnCommandSelected(self, Selection):
    """ Called when an entry is selected in the list of commands """
    Model, TreeIter = Selection.get_selected()
    if TreeIter != None:
      self.CmdEntry.set_text(Model[TreeIter][0])


  def SendCommand(self, entry):
    """ Called when 'Enter' is pressed or send button activated """
    CmdStr = self.CmdEntry.get_text()
    #Add the command to the view
    ListIter = self.CLIListstore.append((CmdStr, self.CLIColorBackground , self.CLIColorForegroundTx ))
    #Follow the last line in the view
    Path = self.CLIListstore.get_path(ListIter)
    self.CLITreeview.scroll_to_cell(self.CLIListstore.get_path(ListIter))
    #Send the command
    if self.CLIManager.ConManager.IsConnectionActive():
      self.fd = self.CLIManager.ConManager.Send(CmdStr)

    self.CmdEntry.set_text("")	#Erase the content of the entry once the command is sent


  def AddConnectionsMenuActions(self, ActionGroup):
    ActionGroup.add_actions([
            ("ConnectionsMenu", None, "Connections"),
            ("SelectConnection", None, "Select", None, None,
             None),
            ("EditConnection", None, "Edit", None, None,
             self.OnMenuEditConnections),
            ("Connect", Gtk.STOCK_CONNECT, "Connect", None, "Connect",
             self.OnMenuConnect),
            ("Disconnect", Gtk.STOCK_DISCONNECT, "Disconnect", None, "Disconnect",
             self.OnMenuDisconnect),
            ("ClearConsole", Gtk.STOCK_CLEAR, "Clear", None, "Clear console",
             self.OnMenuClear)])

    #Get default connection type
    if self.CLIManager.ConManager.GetConnectionType() == "UDP":
      DefaultType = 1
    elif self.CLIManager.ConManager.GetConnectionType() == "TCP":
      DefaultType = 2

    ActionGroup.add_radio_actions([
            ("SelectUDP", None, "UDP", None, None, 1),
            ("SelectTCP", None, "TCP", None, None, 2)
	    ], DefaultType, self.OnMenuConnectionTypeChanged)


  def AddFileMenuActions(self, ActionGroup):
    ActionGroup.add_actions([
            ("FileMenu", None, "File"),
            ("FileOpen", Gtk.STOCK_OPEN, "Open", None, "Open file (.set)",
             self.OnMenuImportFromSet),
            ("ImportFromSource", Gtk.STOCK_CONVERT, "Import from source", None, None,
             self.OnMenuImportFromSource),
            ("SaveAs", Gtk.STOCK_FLOPPY, "Save As", None, None,
             self.OnMenuSaveAs)])

    FilequitAction = Gtk.Action("FileQuit", None, None, Gtk.STOCK_QUIT)
    FilequitAction.connect("activate", self.OnMenuFileQuit)
    ActionGroup.add_action(FilequitAction)


  def AddOptionsMenuActions(self, ActionGroup):
    ActionGroup.add_actions([
            ("OptionsMenu", None, "Options"),
            ("CLIColor", None, "CLI color") ])

    EscapeChar = Gtk.ToggleAction("HideEscapeChar", "Hide escape sequences", \
				      None, None)
    EscapeChar.connect("toggled", self.OnOptionEscapeCharToggled)
    ActionGroup.add_action(EscapeChar)

    ActionGroup.add_actions([
            ("ColorNone", None, "None", None, None, self.OnOptionSelectColor),
            ("ColorSea", None, "Sea", None, None, self.OnOptionSelectColor),
            ("ColorConsole", None, "Console", None, None, self.OnOptionSelectColor) ])


  def OnMenuFileQuit(self, widget):
    """ Called when the cross is clicked or quit from file menu """
    Gtk.main_quit()


  def OnOptionSelectColor(self, widget):
    """ Called when the user select a color scheme for the CLI """
    self.CLIManager.SetCLIColorConfig(widget.get_name())
    self.SetCLIColor(widget.get_name())


  def SetCLIColor(self, ColorStyle):
    """ Called when the CLI color must be changed """

    if ColorStyle == "ColorNone":
      self.CLIColorBackground = "white"
      self.CLIColorForegroundTx = "Black"
      self.CLIColorForegroundRx = "Black"
    elif ColorStyle == "ColorSea":
      self.CLIColorBackground = "#123A4A"
      self.CLIColorForegroundTx = "turquoise2"
      self.CLIColorForegroundRx = "aquamarine3"
    elif ColorStyle == "ColorConsole":
      self.CLIColorBackground = "black"
      self.CLIColorForegroundRx = "White"
      self.CLIColorForegroundTx = "White"


  def OnOptionEscapeCharToggled(self, widget):
    """ Called when the hide escape char option state is changed """

    if widget.get_active():
      self.CLIManager.SetHideEscapeParam(True)
      #The column without escape chars (3) is set to visible whereas the other is not
      self.CmdSetTreeview.get_column(2).set_visible(False)
      self.CmdSetTreeview.get_column(3).set_visible(True)
    else:
      self.CLIManager.SetHideEscapeParam(False)
      #The column with escape chars (2) is set to visible whereas the other is not
      self.CmdSetTreeview.get_column(2).set_visible(True)
      self.CmdSetTreeview.get_column(3).set_visible(False)


  def OnMenuClear(self, widget):
    """ Called when the clear button from the toolbar is pressed """	
    self.CLIListstore.clear()
	

  def OnMenuConnectionTypeChanged(self, widget, current):
    """ Called when the connection type to be used has changed """
    if current.get_name() == "SelectUDP":
      self.CLIManager.ConManager.SetConnectionType("UDP")
    elif current.get_name() == "SelectTCP":
      self.CLIManager.ConManager.SetConnectionType("TCP")


  def DataHandler(self, data):
    """ Callback to handle data received from the socket """
    ListIter = self.CLIListstore.append(( data, self.CLIColorBackground , self.CLIColorForegroundRx ))
    #Scroll to the last entry
    path = self.CLIListstore.get_path(ListIter)
    self.CLITreeview.scroll_to_cell(self.CLIListstore.get_path(ListIter))


  def OnMenuConnect(self, widget):
    """ Called when the user ask for opening the port/establish connection """
    Error = self.CLIManager.ConManager.Connect(self.DataHandler)
    self.SetConnectionStatusInTitle()
    self.AppStatusbar.Connect(Error)	#Update the status bar


  def OnMenuDisconnect(self, widget):
    """ Called when the user ask for closing the socket/connection """
    self.CLIManager.ConManager.Disconnect()
    self.SetConnectionStatusInTitle()
    self.AppStatusbar.Disconnect()  #Update status bar


  def OnMenuEditConnections(self, widget):
    """ build the dialog for editing connections parameters """
    Dialog = ConnectionsDialog(self)
    Dialog.show()
    Response = Dialog.run()

    if Response == Gtk.ResponseType.OK:
      if Dialog.HasConfigBeenModified():
	Dialog.SaveConfig()   #Save modifications
    #No action if cancel button is pressed
    Dialog.destroy()


  def OnMenuImportFromSet(self, widget):
    """ Called when the user request to open a file """
    Dialog = Gtk.FileChooserDialog("Select commands set file (.set)", self,
             Gtk.FileChooserAction.OPEN,
            (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
             Gtk.STOCK_OPEN, Gtk.ResponseType.OK))

    FilterSet = Gtk.FileFilter()
    FilterSet.set_name(".set")
    FilterSet.add_pattern("*.set")
    Dialog.add_filter(FilterSet)

    FilterAll = Gtk.FileFilter()
    FilterAll.set_name("All")
    FilterAll.add_pattern("*")
    Dialog.add_filter(FilterAll)

    Response = Dialog.run()

    if Response == Gtk.ResponseType.OK:
      Filename = Dialog.get_filename()
      if not Filename.endswith ('.set'):
	Filename += '.set'

      #Check if a set is already loaded
      if self.CLIManager.IsCommandsSetLoaded():
	#liststore should be emptied first
	self.CommandsListstore.clear()
	self.CLIManager.SetCommandsSetLoaded(False)

      #parse the file and load the commands set
      Parser = CmdParser()
      Parser.CmdParse(Filename, 'Set', self.CommandsListstore)

      self.CLIManager.SetHideEscapeCharColumn(self.CommandsListstore)
      self.CLIManager.SetCommandsSetLoaded(True)

      self.AppStatusbar.FileLoaded(Filename)

    Dialog.destroy()


  def OnMenuImportFromSource(self, widget):
    """ Called when the user request to import a file from sources """
    Dialog = Gtk.FileChooserDialog("Select source file", self,
             Gtk.FileChooserAction.OPEN,
            (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
             Gtk.STOCK_OPEN, Gtk.ResponseType.OK))

    FilterC = Gtk.FileFilter()
    FilterC.set_name("C files")
    FilterC.add_pattern("*.c")
    Dialog.add_filter(FilterC)

    FilterAll = Gtk.FileFilter()
    FilterAll.set_name("All")
    FilterAll.add_pattern("*")
    Dialog.add_filter(FilterAll)

    Response = Dialog.run()
    if Response == Gtk.ResponseType.OK:
      Filename = Dialog.get_filename()
      if not Filename.endswith ('.c'):
	Filename += '.c'

      #Check if a set is already loaded
      if self.CLIManager.IsCommandsSetLoaded():
	#liststore should be emptied first
	self.CommandsListstore.clear()
	self.CLIManager.SetCommandsSetLoaded(False)

      #parse the file and load the generated set
      Parser = CmdParser()
      Parser.CmdParse(Filename, 'Source', self.CommandsListstore)

      self.CLIManager.SetHideEscapeCharColumn(self.CommandsListstore)

      self.CLIManager.SetCommandsSetLoaded(True)
      self.AppStatusbar.FileImported(Filename)
      
    Dialog.destroy()


  def OnMenuSaveAs(self,widget):
    """ Called when the user request to save the commands currently loaded """
    if self.CLIManager.IsCommandsSetLoaded():
      Dialog = Gtk.FileChooserDialog("Save as", self,
	       Gtk.FileChooserAction.SAVE,
	      (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
	       Gtk.STOCK_SAVE, Gtk.ResponseType.OK))

      FilterAll = Gtk.FileFilter()
      FilterAll.set_name("All")
      FilterAll.add_pattern("*")
      Dialog.add_filter(FilterAll)

      Response = Dialog.run()
      if Response == Gtk.ResponseType.OK:
	Filename = Dialog.get_filename()
	if not Filename.endswith ('.set'):
	  Filename += '.set'
	self.CLIManager.GenerateCommandsSetFile(Filename, self.CommandsListstore )
	self.AppStatusbar.FileSaved(Filename)

      Dialog.destroy()
    else:
      Dialog = Gtk.MessageDialog(self, 0, Gtk.MessageType.ERROR,
	       Gtk.ButtonsType.CANCEL, "Error")
      Dialog.format_secondary_text("A set of commands must be loaded")
      Dialog.run()
      Dialog.destroy()


  def CreateUIManager(self):
    UIManager = Gtk.UIManager()

    UIManager.add_ui_from_string(UI_MENU)
    AccelGroup = UIManager.get_accel_group()
    self.add_accel_group(AccelGroup)
    return UIManager


  def SetConnectionStatusInTitle(self):
    """ Called to set the title of the main window with the connection status """
    if self.CLIManager.ConManager.IsConnectionActive():
      self.set_title(_APP_NAME + "  [CONNECTED]")
    else:
      self.set_title(_APP_NAME + "  [DISCONNECTED]")



class ConnectionsDialog(Gtk.Dialog):
  """ Dialog for the connection parameters """

  def __init__(self, parent):
    Gtk.Dialog.__init__(self, "Edit connections parameters", parent, 0,
		       (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
			Gtk.STOCK_OK, Gtk.ResponseType.OK))

    self.set_default_size( 480, 320 )

    Box = self.get_content_area()
    Notebook = Gtk.Notebook()
    Box.add(Notebook)

    self.Parent = parent

    #Get current config
    self.UDPAddress, self.UDPPort, self.TCPAddress, self.TCPPort \
    = parent.CLIManager.ConManager.GetConnectionsConfig()

    self.UDPTab(Notebook)
    self.TCPTab(Notebook)

    self.ConfigModified = False;

    self.show_all()


  def UDPTab(self, notebook):
    """ Tab dedicated to UDP parameters """

    HBoxUDP = Gtk.HBox( False, 10 )
    notebook.append_page( HBoxUDP, Gtk.Label( "UDP" ) )

    UDPgrid = Gtk.Grid()
    UDPgrid.set_column_homogeneous(False)
    UDPgrid.set_row_homogeneous(True)
    UDPgrid.set_row_spacing(10)
    UDPgrid.set_column_spacing(10)
    HBoxUDP.pack_start(UDPgrid, True, True, 0)

    #Objects of the tab
    UDPAddress = Gtk.Label("Host IP Address")
    UDPAddress.set_margin_top(20)
    UDPAddress.set_margin_left(50)
    UDPPort = Gtk.Label("Port")
    UDPPort.set_margin_bottom(10)
    UDPPort.set_margin_left(50)
    self.UDPAddressEntry = Gtk.Entry()
    self.UDPAddressEntry.set_margin_top(20)
    self.UDPAddressEntry.set_margin_right(50)
    self.UDPPortEntry = Gtk.Entry()
    self.UDPPortEntry.set_margin_bottom(15)
    self.UDPPortEntry.set_margin_right(50)

    #Put elements in the grid
    UDPgrid.attach(UDPAddress, 0, 0, 1, 1)
    UDPgrid.attach(UDPPort, 0, 1, 1, 1)
    UDPgrid.attach_next_to(self.UDPAddressEntry, UDPAddress, Gtk.PositionType.RIGHT, 2,1)
    UDPgrid.attach_next_to(self.UDPPortEntry, UDPPort, Gtk.PositionType.RIGHT, 2,1)

    self.UDPAddressEntry.set_text(self.UDPAddress)
    self.UDPPortEntry.set_text(self.UDPPort)

    self.UDPAddressEntry.connect("changed", self.EntryModified_cb)
    self.UDPPortEntry.connect("changed", self.EntryModified_cb)


  def TCPTab(self, notebook):
    """ Tab dedicated to TCP parameters """

    HBoxTCP = Gtk.HBox( False, 10 )
    notebook.append_page( HBoxTCP, Gtk.Label( "TCP" ) )

    TCPgrid = Gtk.Grid()
    TCPgrid.set_column_homogeneous(False)
    TCPgrid.set_row_homogeneous(True)
    TCPgrid.set_row_spacing(10)
    TCPgrid.set_column_spacing(10)
    HBoxTCP.pack_start(TCPgrid, True, True, 0)

    #Objects of the tab
    TCPAddress = Gtk.Label("Host IP Address")
    TCPAddress.set_margin_top(20)
    TCPAddress.set_margin_left(50)
    TCPPort = Gtk.Label("Port")
    TCPPort.set_margin_bottom(10)
    TCPPort.set_margin_left(50)
    self.TCPAddressEntry = Gtk.Entry()
    self.TCPAddressEntry.set_margin_top(20)
    self.TCPAddressEntry.set_margin_right(50)
    self.TCPPortEntry = Gtk.Entry()
    self.TCPPortEntry.set_margin_bottom(15)
    self.TCPPortEntry.set_margin_right(50)

    #Put elements in the grid
    TCPgrid.attach(TCPAddress, 0, 0, 1, 1)
    TCPgrid.attach(TCPPort, 0, 1, 1, 1)
    TCPgrid.attach_next_to(self.TCPAddressEntry, TCPAddress, Gtk.PositionType.RIGHT, 2,1)
    TCPgrid.attach_next_to(self.TCPPortEntry, TCPPort, Gtk.PositionType.RIGHT, 2,1)

    self.TCPAddressEntry.set_text(self.TCPAddress)
    self.TCPPortEntry.set_text(self.TCPPort)

    self.TCPAddressEntry.connect("changed", self.EntryModified_cb)
    self.TCPPortEntry.connect("changed", self.EntryModified_cb)


  def EntryModified_cb(self, entry):
    """ Flag the modification of the configuration """
    self.ConfigModified = True;


  def HasConfigBeenModified(self):
    """ tells if the configuration has been modified """
    return self.ConfigModified


  def SaveConfig(self):
    """ When the config is chnaged the preferences are updated """
    self.Parent.CLIManager.ConManager.SetConnectionsConfig(self.UDPAddressEntry.get_text(), \
							   self.UDPPortEntry.get_text(), \
							   self.TCPAddressEntry.get_text(), \
							   self.TCPPortEntry.get_text())


class SaveDialog(Gtk.Dialog):
  """ Dialog for saving the imported commands """    

  def __init__(self, parent):
    Gtk.Dialog.__init__(self, "Save", parent, 0,
		       (Gtk.STOCK_NO, Gtk.ResponseType.NO,
			Gtk.STOCK_YES, Gtk.ResponseType.YES))

    self.set_default_size(150, 100)

    Label = Gtk.Label("\nWould you like to save the converted file?")

    Box = self.get_content_area()
    Box.add(Label)
    self.show_all()


class Statusbar(Gtk.Statusbar):
  """ Status bar of the main window """

  def __init__(self, parent):

    self.parent = parent

    Gtk.Statusbar.__init__(self)
    self.ContextId = self.get_context_id("Application status")
    self.push(self.ContextId, "Ready...")


  def Pop(self):
    """ Pop the message in the status bar """
    self.pop(self.ContextId)


  def FileLoaded(self, filename):
    """ Set the message in the status bar once the file is loaded """
    self.Pop()
    Msg = "File loaded: " + os.path.basename(filename)
    self.push(self.ContextId, Msg)


  def FileSaved(self, filename):
    """ Set the message in the status bar once the file is saved """
    self.Pop()
    Msg = "File saved: " + os.path.basename(filename)
    self.push(self.ContextId, Msg)


  def FileImported(self, filename):
    """ Set the message in the status bar once the file is imported """
    self.Pop()
    Msg = "CLI imported from: " + os.path.basename(filename)
    self.push(self.ContextId, Msg)


  def Connect(self, error):
    """ Set the message in the status bar when the app is connected """
    self.Pop()
    if error == None:
      if self.parent.CLIManager.ConManager.GetConnectionType() == "UDP":
	UDPAddress, UDPPort = self.parent.CLIManager.ConManager.GetUDPConnectionConfig()
	Msg = "UDP port open"
      elif self.parent.CLIManager.ConManager.GetConnectionType() == "TCP":
	TCPAddress, TCPPort = self.parent.CLIManager.ConManager.GetTCPConnectionConfig()
	Msg = "Connected to: " + TCPAddress + ":" + TCPPort
    else:
      Msg = error

    self.push(self.ContextId, Msg)


  def Disconnect(self):
    """ Set the message in the status bar when the app is disconnected """
    self.Pop()
    Msg = "Close connection"
    self.push(self.ContextId, Msg)
    




