## CLIManager
CLI tool for FreeRTOS+CLI

This software is developed to ease the use of the command line interface of projects based on FreeRTOS+CLI.
It's useful with projects having a large amount of different commands.


This software has been tested under Linux and OSX (10.9).

Python Gtk+3 and pyparsing are necessary.
Pyparsing can be found here: http://sourceforge.net/projects/pyparsing/
for Gtk+3 on OSX, please visit https://wiki.gnome.org/Projects/GTK+/OSX/Building


#### Content of the project:
src: contains the sources

demo: contains some c files coming from FreeRTOS+CLI demo that can be used as sample files to import 

#### Run:
python CLIManager.py


#### First Use:
Before connecting the application with your FreeRTOS device, you have to import the commands that will be used through the CLI.
- click on "Import from source" in the File menu or on the "import" icon in the toolbar.
- select the source file (.c file) where all the commands are implemented. (e.g CLI-commands.c in FreeRTOS+CLI demo)
- commands are now loaded. You can choose to save the generated set of commands using "save as" in the File menu
- click on Connections then Select and choose the connection protocol
- click on Connections then Edit to set the connection parameters (IP and port)
- click on connect icon in the toolbar

To send commands, either write the command in the entry box and press enter or use the table with all the commands as a reminder of the syntax. Both pressing enter or pressing "Send" button send the command
Use the "Clear" icon in the toolbar to clear the interface
Use the "Hide escape sequences" option to remove '\r' and '\n' from the help string

Note: at the moment, all the commands definitions must be in the same source file
