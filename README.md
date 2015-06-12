### CLIManager for FreeRTOS+CLI


Important note: Gtk+ 3.12 or later is required

This software is a command line interface tool developed to ease the use of the command line interface of projects based on FreeRTOS+CLI.
It's useful with projects having a large amount of different commands.  
(This software has been tested under OSX (10.9) and Linux).

#### Requirements:

Python Gtk+3 and pyparsing are necessary.  
Pyparsing can be found here: http://sourceforge.net/projects/pyparsing/  
for Gtk+3 on OSX, please visit https://wiki.gnome.org/Projects/GTK+/OSX/Building

__Gtk+ 3.12 or later is required__

#### Content of the project:
src: contains the source files of the project

demo: contains some c files coming from FreeRTOS+CLI demo that can be used as sample files to import.

#### Run:
To run the tool, just type __python CLIManager.py__ in the console.


#### First Use:
Before connecting the application to your FreeRTOS device, you have to import the commands that will be used through the CLI.
- click on "Import from source" in the File menu or on the "import" icon in the toolbar.
- select the source file (.c file) where all the commands are implemented. (e.g CLI-commands.c in FreeRTOS+CLI demo)
- commands are now loaded. You can choose to save the generated set of commands using "save as" in the File menu
- click on Connections then Select and choose the connection protocol
- click on Connections then Edit to set the connection parameters (IP and port)
- click on connect icon in the toolbar

To send commands, write the command in the interface (Text field in the upper part of the window) and then press 'Enter'.  
When commands are imported or loaded, a popover reminds the syntax. If only one command corresponds to what is typed, completion can be done by pressing 'Tab'.  
You can select commands from the commands list (List in the lower part of the window). Pressing 'Enter' will copy the command in the interface. You have to press 'Enter' to actually send the command.

You can use the "Clear" icon in the toolbar to clear the interface


#### Remarks:
- At the moment, all the commands definitions must be in the same source file. The tool can't concatenate the files yet.
- The tool can't work under windows mainly beacause UDP/TCP connections are handled in a different way.
