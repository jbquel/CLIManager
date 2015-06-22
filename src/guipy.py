##############################################################################
#
# Command line interface manager (CLIManager) for FreeRTOS+CLI
# File: gui.py
# This file defines the user interface and its behavior. The following code is
# based on GTK3.
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

from gi.repository import Gtk, Gdk, Pango
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
      <menuitem action='CLIFontSelection' />
      <separator/>
      <menuitem action='HideAssistantPopover' />
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

    #create the treeview for the set of commands
    self.CmdSetTreeview = Gtk.TreeView.new_with_model(self.CommandsListstore)
    for i, Title in enumerate(["Command", " Nb Arguments", "Help string", "Help string"]):
      CmdSetRenderer = Gtk.CellRendererText()
      column = Gtk.TreeViewColumn(Title, CmdSetRenderer, text=i)
      self.CmdSetTreeview.append_column(column)

    self.AssistantPopoverActive = False

    ActionGroup = Gtk.ActionGroup("MenuActions")
    self.AddFileMenuActions(ActionGroup)
    self.AddConnectionsMenuActions(ActionGroup)
    self.AddOptionsMenuActions(ActionGroup)

    UIManager = self.CreateUIManager()
    UIManager.insert_action_group(ActionGroup)

    #Menu and toolbar
    self.Menubar = UIManager.get_widget("/MenuBar")
    self.Toolbar = UIManager.get_widget("/ToolBar")

    # Status bar
    self.AppStatusbar = Statusbar(self)

    #Scrolled windows
    self.CmdSetScrollWindow = Gtk.ScrolledWindow()
    self.CmdSetScrollWindow.set_vexpand(True)
    self.CLIScrollWindow = Gtk.ScrolledWindow()
    self.CLIScrollWindow.set_vexpand(True)
    self.CLIScrollWindow.set_hexpand(True)

    #Command Line Interface Textview
    self.CLITextview = Gtk.TextView()
    self.CLITextbuffer = self.CLITextview.get_buffer()
    self.CLITextbuffer.set_text("> ")

    self.CLIScrollWindow.add(self.CLITextview)
    # Both views share the same keypree event handler
    self.CLITextview.connect("key-press-event", self.KeyPressEnter)
    self.CmdSetTreeview.connect("key-press-event", self.KeyPressEnter)

    self.CLITextview.connect("button-press-event", self.OnButtonPressEvent)

    self.CLITextbuffer.connect("insert-text", self.InsertTextCallback)
    self.CLITextbuffer.connect("delete-range", self.DeleteTextCallback)
    self.CLITextbuffer.connect("end-user-action", self.EnduserAction)
    self.connect('check-resize', self.OnWindowResized)
 
    # Create the mark that identifies the beginning of the 
    self.CLITextbuffer.create_mark("CmdId", self.CLITextbuffer.get_end_iter(), True)

    #Layout of the main window
    self.grid.attach(self.Menubar, 0, 0, 8, 1)
    self.grid.attach(self.Toolbar, 0, 1, 8, 1)
    self.grid.attach(self.CLIScrollWindow, 0, 2, 8, 15)
    self.grid.attach(self.CmdSetScrollWindow, 0, 17, 8, 15)
    self.grid.attach(self.AppStatusbar, 0, 33, 8, 1)

    self.CmdSetScrollWindow.add(self.CmdSetTreeview)

    #The entry selected in the list is used to populate the command entry
    CommandSelected = self.CmdSetTreeview.get_selection()
    CommandSelected.connect("changed", self.OnCommandSelected)

    #Add the connection status to the main title of the window
    self.SetConnectionStatusInTitle()

    # Hide the column where the escape chars are displayed
    self.CmdSetTreeview.get_column(3).set_visible(False)

    #Set colors for the CLI
    self.SetCLIColor(self.CLIManager.GetCLIColorConfig())

    # Set font for the CLI
    self.CLIFont = Pango.FontDescription(self.CLIManager.GetCLIFontConfig())
    self.CLITextview.override_font(self.CLIFont)

    self.CLITextview.set_accepts_tab(True)
    self.CLITextview.grab_focus()

    # Init variables for command history
    self.CLIHistory = []
    self.CLIHistoryOffset = 0
	  
    self.show_all()


  def OnButtonPressEvent(self,widget,event):
    """ Set the focus on the CLI Textview when user click on it """
    self.CLITextview.grab_focus()
    return True	#Textview doesn't have to handle clicks


  def OnWindowResized(self, window):
    """ Ensure that the popover is always aligned with the text """
    self.UpdtateAssistantPopover("")


  def KeyPressEnter(self, widget, event):
    """ Handle key press events """

    # Prevent the user from deleting or inserting before the prompt 
    if event.keyval == Gdk.KEY_BackSpace or event.keyval == Gdk.KEY_Left:
      CmdStartMark = self.CLITextbuffer.get_mark("CmdId")
      CmdStartIter = self.CLITextbuffer.get_iter_at_mark(CmdStartMark)
      LastIter = self.CLITextbuffer.get_iter_at_mark(self.CLITextbuffer.get_insert())
      if LastIter.equal(CmdStartIter):
	return True
      else:
	return False

    # Keys related to command history
    if (event.keyval == Gdk.KEY_Up and widget.get_name() == "GtkTextView"):
      self.HistoryStepBackward()
      return True

    if (event.keyval == Gdk.KEY_Down and widget.get_name() == "GtkTextView"):
      self.HistoryStepForward()
      return True


    # Completion
    if event.keyval == Gdk.KEY_Tab:
      # Completion possible only if one suggested command
      if self.IsAssistantPopoverActive() and self.IsOneSuggestion():
	StartMark = self.CLITextbuffer.get_mark("CmdId")
	Start = self.CLITextbuffer.get_iter_at_mark(StartMark)
	End = self.CLITextbuffer.get_end_iter()

	String = self.GetCompletionString(self.CLITextbuffer.get_text(Start, End, False))
	if String is not None:	# No completion if nothing matches
	  self.CLITextbuffer.delete(Start, End)
	  self.CLITextbuffer.insert(Start, String)
	  self.UpdtateAssistantPopover("")
      return True # No tab displayed in the CLI

    # User pressed enter in the the CLI
    if event.keyval == Gdk.KEY_Return and widget.get_name() == "GtkTextView":
      StartMark = self.CLITextbuffer.get_mark("CmdId")
      start = self.CLITextbuffer.get_iter_at_mark(StartMark)
      end = self.CLITextbuffer.get_end_iter()
      Command = self.CLITextbuffer.get_text(start, end, False)

      # New prompt for next line
      self.CLITextbuffer.insert_at_cursor("\n> ",3)
      # Popover (if displayed) should be removed
      self.DestroyAssistantPopover()

      if self.CLIManager.ConManager.IsConnectionActive():
	self.fd = self.CLIManager.ConManager.Send(Command)

      self.CLITextview.scroll_to_mark(self.CLITextbuffer.get_insert(),0.0,False,0.5,0.5)

      # Create new mark at the beginning of the new command
      self.CLITextbuffer.delete_mark_by_name("CmdId")
      self.CLITextbuffer.create_mark("CmdId", self.CLITextbuffer.get_end_iter(), True)

      # Add command to history
      self.AddToHistory(Command)

      return True

    # User pressed enter to select a command from the command treeview
    if event.keyval == Gdk.KEY_Return and widget.get_name() == "GtkTreeView":
      self.CLITextview.grab_focus() # Switch to the CLI to allow user
      return True

    return False


  def GetCompletionString(self, pattern):
    """ Returns the row starting with the requested pattern """
    for Row in self.CommandsListstore:
      if Row[0].startswith(pattern):
	return Row[0]


  def InsertTextCallback(self, widget, location, text, length):
    """ Handle syntax assistant popover according to user input """
  
    StartMark = self.CLITextbuffer.get_mark("CmdId")
    Start = self.CLITextbuffer.get_iter_at_mark(StartMark)
    End = self.CLITextbuffer.get_end_iter()
        
    UserInput = self.CLITextbuffer.get_text(Start, End, False)

    Line = UserInput + text	# group the whole input
    CurrentLine =  Line.split() # split to get the command without parameters

    self.FillSyntaxAssistantContent(CurrentLine)


  def DeleteTextCallback(self, buffer, start, end):
    """ Handle syntax assistant popover when some text is deleted """
    StartMark = self.CLITextbuffer.get_mark("CmdId")
    Start = self.CLITextbuffer.get_iter_at_mark(StartMark)
    End = self.CLITextbuffer.get_end_iter()
    End.backward_char() #Last char is being suppressed

    UserInput = self.CLITextbuffer.get_text(Start, End, False)

    # When no input on the line no assistant popover should be displaayed
    if UserInput == "":
      self.DestroyAssistantPopover()
      return

    CurrentLine =  UserInput.split() # split to get the command without parameters

    self.FillSyntaxAssistantContent(CurrentLine)


  def FillSyntaxAssistantContent(self, Line):
    """ Fills the syntax assistant popover with suggestions according to user input """
    AssistantPopoverContent = ""
    ShowPopover = False

    for Row in self.CommandsListstore:
      if Row[0].startswith(Line[0]):
	ShowPopover = True
	# Exact match no need to show assistant anymore
	if Row[0] == Line[0] and Row[1] == 0:
	  ShowPopover = False

	# Command input complete but the popover will display the parameters
	elif Row[0] == Line[0] and Row[1] != 0:
	  # Parse the Help string to extract parameters if possible
	  Parser = CmdParser()
	  ParamList = Parser.ParseHelpString(Row[2], Row[1])
	  
	  if ParamList != None:
	    if len(ParamList) != 0:
	      for Param in ParamList:
		if AssistantPopoverContent != "":
		  AssistantPopoverContent += " "
		AssistantPopoverContent += "<b><i>[ " + Param + " ]</i></b>"
	    else:
	    # Special case. No argument found in the help string but
	    # the nb of declared arguments is not 0
	      AssistantPopoverContent += "<b><i>[ ... ]</i></b>"
    
	# The command name is not complete yet
	else:
	  # Parse the help string to extract command parameters if possible
	  Parser = CmdParser()
	  ParamList = Parser.ParseHelpString(Row[2], Row[1])

	  if AssistantPopoverContent != "":
	    AssistantPopoverContent += "\n"
	  AssistantPopoverContent += '<b>' + Row[0] + "</b>"
	  if ParamList != None:
	    if len(ParamList) != 0:
	      for Param in ParamList:
		AssistantPopoverContent += " " + "<i>[ " + Param + " ]</i>"
	    else:
		AssistantPopoverContent += " " + "<i>[ ... ]</i>"
		
    if ShowPopover == True:
      if self.AssistantPopoverActive == True:
	# Just update the popover
	self.UpdtateAssistantPopover(AssistantPopoverContent)
      else:
	# Create and display the popover
	self.DisplayAssistantPopover(AssistantPopoverContent)
    else:
      	self.DestroyAssistantPopover()


  def EnduserAction(self, buffer):
    """ Ensure popover pointing tip correct alignment and popover position after user input """

    # Always keep the alignement with the last iter
    if self.AssistantPopoverActive == True:
      self.UpdtateAssistantPopover("")

    # If line is empty, the assistant popover should disappear
    StartMark = self.CLITextbuffer.get_mark("CmdId")
    Start = self.CLITextbuffer.get_iter_at_mark(StartMark)
    End = self.CLITextbuffer.get_end_iter()
    if self.CLITextbuffer.get_text(Start, End, False) == "":
      self.DestroyAssistantPopover()


  def OnCommandSelected(self, Selection):
    """ Called when an entry is selected in the list of commands """

    Model, TreeIter = Selection.get_selected()
    if TreeIter != None:
      CmdStartMark = self.CLITextbuffer.get_mark("CmdId")
      Start = self.CLITextbuffer.get_iter_at_mark(CmdStartMark)
      end = self.CLITextbuffer.get_end_iter()
      self.CLITextbuffer.delete(Start, end) # replace what was typed by the command
      self.CLITextbuffer.insert(Start, Model[TreeIter][0])

      self.UpdtateAssistantPopover("")


  def DisplayAssistantPopover(self, text):
    """ Create and show the assistant popover """

    if self.CLIManager.GetHideSyntaxAssistantParam() is False:
      self.Popover = Gtk.Popover.new(self.CLITextview)
      self.PopoverLabel = Gtk.Label()
      self.PopoverLabel.set_markup(text)
      self.Popover.add(self.PopoverLabel)

      Pos = self.CLITextbuffer.get_end_iter()
      Location = self.CLITextview.get_iter_location(Pos)
      WinLocation = Location
      WinLocation.x, WinLocation.y = self.CLITextview.buffer_to_window_coords(Gtk.TextWindowType.TEXT,Location.x,Location.y)

      self.Popover.set_pointing_to(WinLocation)
      self.Popover.set_modal(False)   # The popover doesn't take user interaction
      self.Popover.set_position(Gtk.PositionType.BOTTOM)

      self.Popover.show_all()

      self.AssistantPopoverActive = True;


  def DestroyAssistantPopover(self):
    """ Destroy th assistant pover and reset the associated flag """
    if self.AssistantPopoverActive == True:
      self.Popover.destroy()
    self.AssistantPopoverActive = False


  def UpdtateAssistantPopover(self, text):
    """ Update the popover content and pointing tip position """
    if self.AssistantPopoverActive == True:
      if text != "":  # Label not updated when empty string
	self.PopoverLabel.set_markup(text)

      Pos = self.CLITextbuffer.get_end_iter()
      Location = self.CLITextview.get_iter_location(Pos)
      # convert the buffer coords to window coords so the popover is always visible
      # even when the window is scrolled
      WinLocation = Location
      WinLocation.x, WinLocation.y = self.CLITextview.buffer_to_window_coords(Gtk.TextWindowType.TEXT,Location.x,Location.y)
      # Update pointing tip position
      self.Popover.set_pointing_to(WinLocation)


  def IsAssistantPopoverActive(self):
    """ Tells if the assistant popover is currently displayed """
    return self.AssistantPopoverActive


  def IsOneSuggestion(self):
    """ Tells if there is only one command corresponding to what is typed """
    text = self.PopoverLabel.get_text()
    # Check if there's more than one line in the label
    if "\n" in text:
      return False
    else:
      return True


  def AddToHistory(self, command):
    """ Add a command to history. Called after the user sent a command """

    if command != "": # Do not insert blank lines
      self.CLIHistory.append(command)
      self.CLIHistoryOffset = len(self.CLIHistory)  # Update offset value


  def HistoryStepBackward(self):
    """ Make a step backward in the history and display the entry """

    if self.CLIHistoryOffset > 0:
      self.CLIHistoryOffset -= 1
      CmdStartMark = self.CLITextbuffer.get_mark("CmdId")
      Start = self.CLITextbuffer.get_iter_at_mark(CmdStartMark)
      end = self.CLITextbuffer.get_end_iter()
      self.CLITextbuffer.delete(Start, end) # what was typed will be replaced by history entry
      self.CLITextbuffer.insert(Start, self.CLIHistory[(self.CLIHistoryOffset)])  # Insert entry

      self.UpdtateAssistantPopover("")  # Update assistant popover if displayed


  def HistoryStepForward(self):
    """ Make a step forward in the history and display the entry """

    if self.CLIHistoryOffset <= (len(self.CLIHistory) - 1):
      self.CLIHistoryOffset += 1
      if self.CLIHistoryOffset == len(self.CLIHistory): # Offset incremented just before
	Entry = ""  # Not an entry in the history
      else:
	Entry = self.CLIHistory[self.CLIHistoryOffset]
    else:   # Do not increment offset
      Entry = ""

    CmdStartMark = self.CLITextbuffer.get_mark("CmdId")
    Start = self.CLITextbuffer.get_iter_at_mark(CmdStartMark)
    end = self.CLITextbuffer.get_end_iter()
    self.CLITextbuffer.delete(Start, end) # replace what was typed by the command
    self.CLITextbuffer.insert(Start, Entry)

    if Entry == "":
      self.DestroyAssistantPopover()  # Destroy popover if any
    else:
      self.UpdtateAssistantPopover("")  # Update Popover


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
            ("CLIColor", None, "CLI color"),
	    ("CLIFontSelection", None, "CLI font", None, None, self.OnOptionSelectFont) ])


    EscapeChar = Gtk.ToggleAction("HideEscapeChar", "Hide escape sequences", \
				      None, None)
    EscapeChar.connect("toggled", self.OnOptionEscapeCharToggled)
    EscapeChar.set_active(self.CLIManager.GetHideEscapeParam())
    ActionGroup.add_action(EscapeChar)

    SyntaxAssistant = Gtk.ToggleAction("HideAssistantPopover", "Hide syntax assistant", \
				      None, None)
    SyntaxAssistant.connect("toggled", self.OnOptionSyntaxAssistantToggled)
    SyntaxAssistant.set_active(self.CLIManager.GetHideSyntaxAssistantParam())
    ActionGroup.add_action(SyntaxAssistant)

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


  def OnOptionSelectFont(self,widget):
    """ Called when the user select a font for the CLI """
    FontDialog = Gtk.FontChooserDialog("CLI font", self)
    FontDialog.set_font_desc(self.CLIFont)
    FontDialog.show()
    Response = FontDialog.run()

    if Response == Gtk.ResponseType.OK:
      self.CLIFont = FontDialog.get_font_desc()
      FontName = FontDialog.get_font()
      self.CLIManager.SetCLIFontConfig(FontName)  # Save as user preference

      self.CLITextview.override_font(self.CLIFont)  # Update CLI font

    FontDialog.destroy()


  def ParseColor(self, color):
    """ Parse colors to set Bg and Fg colors according to selected color scheme """
    _color = Gdk.RGBA()
    _color.parse(color)
    return _color


  def SetCLIColor(self, ColorStyle):
    """ Called when the CLI color must be changed """

    if ColorStyle == "ColorNone":
      self.CLITextview.override_background_color(Gtk.StateFlags.NORMAL, self.ParseColor("white"))
      self.CLITextview.override_color(Gtk.StateFlags.NORMAL, self.ParseColor("black"))

    elif ColorStyle == "ColorSea":
      self.CLITextview.override_background_color(Gtk.StateFlags.NORMAL, self.ParseColor("#123A4A"))
      self.CLITextview.override_color(Gtk.StateFlags.NORMAL, self.ParseColor("turquoise2"))

    elif ColorStyle == "ColorConsole":
      self.CLITextview.override_background_color(Gtk.StateFlags.NORMAL, self.ParseColor("black"))
      self.CLITextview.override_color(Gtk.StateFlags.NORMAL, self.ParseColor("white"))


  def OnOptionEscapeCharToggled(self, widget):
    """ Called when the hide escape char option state is changed """

    if widget.get_active():
      self.CLIManager.SetHideEscapeParam(True)
      self.SetVisibleColumn(True)
    else:
      self.CLIManager.SetHideEscapeParam(False)
      self.SetVisibleColumn(False)


  def SetVisibleColumn(self, Param):
    """ Set the visible help column according to the option state """
    if Param is True:
      #The column without escape chars (3) is set to visible whereas the other is not
      self.CmdSetTreeview.get_column(2).set_visible(False)
      self.CmdSetTreeview.get_column(3).set_visible(True)
    else:
      #The column with escape chars (2) is set to visible whereas the other is not
      self.CmdSetTreeview.get_column(2).set_visible(True)
      self.CmdSetTreeview.get_column(3).set_visible(False)


  def OnOptionSyntaxAssistantToggled(self,widget):
    """ Called when the syntax assistant popover option state is changed """
    if widget.get_active():
      self.CLIManager.SetHideSyntaxAssistantParam(True)
      self.DestroyAssistantPopover()  # Option disabled so the popover should be destroyed immediately
    else:
      self.CLIManager.SetHideSyntaxAssistantParam(False)


  def OnMenuClear(self, widget):
    """ Called when the clear button from the toolbar is pressed """	
    # Empty the whole textview
    Start, End = self.CLITextbuffer.get_bounds()
    self.CLITextbuffer.delete(Start, End)
    self.CLITextbuffer.insert_at_cursor("> ",2)

    # Update the mark
    self.CLITextbuffer.delete_mark_by_name("CmdId")
    self.CLITextbuffer.create_mark("CmdId", self.CLITextbuffer.get_end_iter(), True) 
	

  def OnMenuConnectionTypeChanged(self, widget, current):
    """ Called when the connection type to be used has changed """
    if current.get_name() == "SelectUDP":
      self.CLIManager.ConManager.SetConnectionType("UDP")
    elif current.get_name() == "SelectTCP":
      self.CLIManager.ConManager.SetConnectionType("TCP")


  def DataHandler(self, data):
    """ Callback to handle data received from the socket """

    CmdStartMark = self.CLITextbuffer.get_mark("CmdId")
    Start = self.CLITextbuffer.get_iter_at_mark(CmdStartMark)
    end = self.CLITextbuffer.get_end_iter()
    self.CLITextbuffer.delete(Start, end)
    self.CLITextbuffer.insert(Start, data)
    self.CLITextbuffer.insert_at_cursor("\n> ",3)

    # Update the mark
    self.CLITextbuffer.delete_mark_by_name("CmdId")
    self.CLITextbuffer.create_mark("CmdId", self.CLITextbuffer.get_end_iter(), True) 

    self.CLITextview.scroll_to_mark(self.CLITextbuffer.get_insert(),0.0,True,0.5,0.5)


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
    self.ImportFrom('List')


  def OnMenuImportFromSource(self, widget):
    """ Called when the user request to import a file from sources """
    self.ImportFrom('Source')


  def ImportFrom(self, FileType):
    """ Called when a list of commands should be loaded to the gtk liststore """

    if FileType == 'Source':
      DialogTitle = "Select source file"
      # Filters for the file chooser
      FilterMain = Gtk.FileFilter()
      FilterMain.set_name("C files")
      FilterMain.add_pattern("*.c")

      FilterAll = Gtk.FileFilter()
      FilterAll.set_name("All")
      FilterAll.add_pattern("*")

    elif FileType == 'List':
      DialogTitle = "Select list of commands file (.set)"
      # Filters for the file chooser
      FilterMain = Gtk.FileFilter()
      FilterMain.set_name(".set")
      FilterMain.add_pattern("*.set")

      FilterAll = Gtk.FileFilter()
      FilterAll.set_name("All")
      FilterAll.add_pattern("*")

    Dialog = Gtk.FileChooserDialog(DialogTitle, self,
             Gtk.FileChooserAction.OPEN,
            (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
             Gtk.STOCK_OPEN, Gtk.ResponseType.OK))

    Dialog.add_filter(FilterMain)
    Dialog.add_filter(FilterAll)

    Response = Dialog.run()
    Filename = Dialog.get_filename() # Filename is nonetype when cancel button pressed
    Dialog.destroy()  # Dialog not needed anymore

    if Response == Gtk.ResponseType.OK:

      #Check if a set is already loaded
      if self.CLIManager.IsCommandsSetLoaded():
	AddToListDialog = AppendToListDialog(self)
	AddToListDialog.show()
	AppendResponse = AddToListDialog.run()
	AddToListDialog.destroy() # Dialog not needed anymore

	if AppendResponse == Gtk.ResponseType.CANCEL:
	  return # Import cancelled

	if AppendResponse == Gtk.ResponseType.NO:
	  #liststore should be emptied first
	  self.CommandsListstore.clear()
	  self.CLIManager.SetCommandsSetLoaded(False)

      #parse the file and load the generated list
      Parser = CmdParser()
      Parser.CmdParse(Filename, FileType, self.CommandsListstore)

      self.CLIManager.SetHideEscapeCharColumn(self.CommandsListstore)
      self.SetVisibleColumn(self.CLIManager.GetHideEscapeParam())

      self.CLIManager.SetCommandsSetLoaded(True)
      self.AppStatusbar.FileImported(Filename)


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


class AppendToListDialog(Gtk.Dialog):
  """ Dialog for offering to append the commands to the current list if one are already loaded """    

  def __init__(self, parent):
    Gtk.Dialog.__init__(self, "Append to current list?", parent, 0,
		       (Gtk.STOCK_YES, Gtk.ResponseType.YES,
			Gtk.STOCK_NO, Gtk.ResponseType.NO,
			Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL))

    self.set_default_size(350, 130)

    LabelMain = Gtk.Label()
    LabelMain.set_markup("\n\n<b>A list of commands is already loaded</b>")

    LabelLine2 = Gtk.Label("\nWould you like to add the new commands to the current list?")
    LabelLine3 = Gtk.Label("(Duplicates will be automatically removed)")

    Box = self.get_content_area()
    Box.add(LabelMain)
    Box.add(LabelLine2)
    Box.add(LabelLine3)
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
    Msg = "List imported from: " + os.path.basename(filename)
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
    

