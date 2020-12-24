#!/bin/python3
#Keebie by Elisha Shaddock UwU

from evdev import InputDevice, categorize, ecodes
import sys
import signal
import os
import json
import argparse
import time

filePath = os.path.abspath(os.path.dirname(sys.argv[0])) + "/" # Get the absolute path to the directory of this script for use when opening files

settings = { # A dict of settings to be used across the script
    "multiKeyMode": "combination",
    "forceBackground": False,
    "backgroundInversion": False
}

settingsPossible = { # A dict of lists of valid values for each setting
    "multiKeyMode": ["combination", "sequence"],
    "forceBackground": [True, False],
    "backgroundInversion": [True, False]
}

class keyLedger():
    """A class for finding all keys pressed at any time."""
    def __init__(self):
        self.keysList = [] # A list of keycodes of keys being held as strings
        self.newKeysList = [] # A list of keycodes of keys that were newly held when update() was last run as strings
        self.freshKeysList = [] # A list of keycodes of keys being held as strings that is empty unless a new key was pressed when update() was last run
    
    def update(self, keyEvent):
        """Take an event and and updates the list of held keys accordingly."""
        self.newKeysList = [] # They are no longer new
        self.freshKeysList = [] # They are no longer fresh

        if keyEvent.type == ecodes.EV_KEY: # If the event is a related to a key, as opposed to a mouse movement or something (At least I think thats what this does)
            keyEvent = categorize(keyEvent) # Convert our EV_KEY input event into a KeyEvent
            keycode = keyEvent.keycode # Cache value that we are about to use a lot
            keystate = keyEvent.keystate

            if keystate == keyEvent.key_down or keystate == keyEvent.key_hold: # If a new key has been pressed or a key we might have missed the down event for is being held
                if not keycode in self.keysList: # If this key (which is held) is not in our list of keys that are held
                    # print(f"New key tracked: {keycode}")
                    self.keysList += [keycode, ] # Add list of our (one) keycode to list of held keys
                    self.newKeysList += [keycode, ] # and to our list of newly held keys

            elif keystate == keyEvent.key_up: # If a key has been released
                if keycode in self.keysList: # And if we have that key marked as held
                    # print(f"Tracked key {keycode} released.")
                    self.keysList.remove(keycode) # Then we remove it from our list of held keys

                else:
                    print(f"Untracked key {keycode} released.") # If you see this that means we missed a key press, bad news. (But not to fatal.)

            if not self.newKeysList == []: # If new keys have pressed
                self.freshKeysList = self.keysList # Set fresh keys equal to helf keys
                # print(f"New keys are: {self.newKeysList}") # Print debug info
                # print(f"Fresh keys are: {self.freshKeysList}")

    def getList(self, returnType = 0):
        """Returns the list of held keys in different forms based on returnType.
        
        returnType values :
        0 - Returns the list as it is stored, as a list of strings.
        1 - Returns a single string with keycodes separated by \"+\"s, for use when reading/writing a layer json file.        
        """
        if returnType == 0: # If we just want the list
            return self.keysList # Return it

        elif returnType == 1: # If we want a string 
            keyListParsed = ""
            
            for keycode in self.keysList:
                keyListParsed += keycode # Build the string out of keycodes
                
                if not keycode is self.keysList[-1]: # If this isn't the last keycode
                    keyListParsed += "+" # Add a + to separate it from the previous keycode

            return keyListParsed # Return the parsed string 

        else: # If we don't recognize the return type
            print(f"Unrecognized value for returnType: {returnType}, returning None, expect errors!") # Say so
            return None

    def getNew(self, returnType = 0):
        """Returns the list of newly held keys in different forms based on returnType.
        
        returnType values :
        0 - Returns the list as it is stored, as a list of strings.
        1 - Returns a single string with keycodes separated by \"+\"s, for use when reading/writing a layer json file.        
        """
        if returnType == 0: # If we just want the list
            return self.newKeysList # Return it

        elif returnType == 1: # If we want a string 
            keyListParsed = ""
            
            for keycode in self.newKeysList:
                keyListParsed += keycode # Build the string out of keycodes
                
                if not keycode is self.newKeysList[-1]: # If this isn't the last keycode
                    keyListParsed += "+" # Add a + to separate it from the previous keycode

            return keyListParsed # Return the parsed string 

        else: # If we don't recognize the return type
            print(f"Unrecognized value for returnType: {returnType}, returning None, expect errors!") # Say so
            return None

    def getFresh(self, returnType = 0):
        """Returns the fresh (empty unless new keys were added last update()) list of held keys in different forms based on returnType.
        
        returnType values :
        0 - Returns the list as it is stored, as a list of strings.
        1 - Returns a single string with keycodes separated by \"+\"s, for use when reading/writing a layer json file.        
        """
        if returnType == 0: # If we just want the list
            return self.freshKeysList # Return it

        elif returnType == 1: # If we want a string 
            keyListParsed = ""
            
            for keycode in self.freshKeysList:
                keyListParsed += keycode # Build the string out of keycodes
                
                if not keycode is self.freshKeysList[-1]:
                    keyListParsed += "+" # Add a + to separate it from the previous keycode

            return keyListParsed # Return the parsed string 

        else: # If we don't recognize the return type
            print(f"Unrecognized value for returnType: {returnType}, returning None, expect errors!") # Say so
            return None

def signal_handler(signal, frame):
    sys.exit(0)

def config(): # Open the config file and return a list of it's line with leading and trailing spaces striped
    f=open(filePath+"config","r")                                     # Opens config file.

    if f.mode =='r':
        config = f.read().splitlines()
        for confLine in range(0, len(config)) : # Strip leading and trailing whitespaces from each line of the config
            config[confLine] = config[confLine].strip() 
        return config

def writeConfig(lineNum, data): # Writes some data to a line of the config file
    lines = open(filePath+'config', 'r').readlines()
    lines[lineNum] = data.strip() + "\n" # Ensure the data we are write will not interfere later lines
    out = open(filePath+'config', 'w')
    out.writelines(lines)
    out.close()

parser = argparse.ArgumentParser() # Set up command line arguments
parser.add_argument("--layers", help="Show saved layer files", action="store_true")
parser.add_argument("--device", help="Change target device")
parser.add_argument("--add", help="Add new keys", action="store_true")
args = parser.parse_args()

layerDir = filePath + "/layers/" # Cache the full path to the /layers directory
scriptDir = filePath + "/scripts/" # Cache the full path to the /scripts directory

print("Welcome to Keebie")

def getLayers(): # Lists all the json files in /layers and thier contents
    print("Available Layers: \n")
    layerFt = ".json"
    layerFi = {}
    layers = [i for i in os.listdir(layerDir) if os.path.splitext(i)[1] == layerFt] # Get a list of paths to all files that match our file extension

    for f in layers:
        with open(os.path.join(layerDir,f)) as file_object:
            layerFi[f] = file_object.read() # build a list of the files at those paths
    
    for i in layerFi:
        print(i+layerFi[i]) # And display thier contents to the user

def addKey(keycodeTimeout = 1): # Shell for adding new macros
    ledger = keyLedger() # Reset the keyLedger

    command = input("Enter the command you would like to attribute to a key on your second keyboard \n") # Get the command the user wishs to bind

    if command.startswith("layer:"): # If the user entered a layer switch command
        if os.path.exists(command.split(':')[-1]+".json") == False: # Check if the layer json file exsits
            createLayer(command.split(':')[-1]+".json") # If not create it
            print("Created layer file: " + command.split(':')[-1]+".json") # And notify the user

    print(f"Please press the key combination you would like to assign the command to and hold it for {keycodeTimeout} seconds until the next prompt.")

    loopStartTime = None
    signal.signal(signal.SIGINT, signal_handler)
    for event in device.read_loop():
        if loopStartTime == None: # because we don't want to start timing until the user has begun entering there key combiation
            loopStartTime = time.time()

        ledger.update(event) # Keep updateing the keyLedger with every new input

        if not time.time() - loopStartTime < keycodeTimeout: # Unless the time runs out
            break # Then we bear the loop

    inp = input(f"Assign {command} to [{ledger.getList(1)}]? [Y/n] ") # Ask the user if we (and they) got the command and binding right
    if inp == 'Y' or inp == '': # If we did 
        newMacro = {}
        newMacro[ledger.getList(1)] = command
        writeJson(config()[1], newMacro) # Write the binding into our layer json file
        print(newMacro) # And print it back

    else: # If we didn't
        print("Addition cancelled.") # Confirm we have cancelled the binding

    rep = input("Would you like to add another Macro? [Y/n] ") # Offer the user to add another binding

    if rep == 'Y' or rep == '': # If they say yes
        addKey() # Restart the shell

    else:
        exit()

def writeJson(filename, data): # Appends new data to a specified layer
    with open(layerDir+filename) as f:
        prevData = json.load(f)

    prevData.update(data)

    with open(layerDir+filename, 'w+') as outfile:
        json.dump(prevData, outfile, indent=3)

def createLayer(filename): # Creates a new layer with a given filename
    basedata = {"KEY_ESC": "layer:default"}

    with open(layerDir+filename, 'w+') as outfile:
        json.dump(basedata, outfile, indent=3)

def readJson(filename, dir = layerDir): # Reads the file contents of a layer (or any json file named filename in the directory dir)
    with open(dir+filename) as f:
        data = json.load(f)

    return data 

def getSettings(): # Reads the json file specified on the third line of config and sets the values of settings based on it's contents
    print(f"Loading settings from {config()[2]}") # Notify the user we are getting settings and tell them the file we are using to do so

    settingsFile = readJson(config()[2], filePath) # Get a dict of the keys and values in our settings file
    for setting in settings.keys(): # For every setting in our settings file
        if settingsFile[setting] in settingsPossible[setting]: # If the value in our settings file is valid
            # print(f"Found valid value: \"{settingsFile[setting]}\" for setting: \"{setting}\"")
            settings[setting] = settingsFile[setting] # write it into our settins

        else :
            print(f"Value: \"{settingsFile[setting]}\" for setting: \"{setting}\" is invalid, defaulting to {settings[setting]}") # Warn the user of invalid settings in the settings file
            
    print(f"Settings are {settings}") # Tell the user the settings we ended up with

def processKeycode(keycode): # Given a keycode that might be in the layer json file, check if it is and execut the appropriate commands
    if keycode in readJson(config()[1]): # If the keycode is in our layer's json file
        value = readJson(config()[1])[keycode] # Get the instructions associated with the keycode

        if value.startswith("layer:"): # If value is a layerswitch command
            if os.path.exists(layerDir+value.split(':')[-1] + ".json") == False: #if the layer has no json file
                createLayer(value.split(':')[-1]+".json") # Create one
                print("Created layer file: " + value.split(':')[-1]+".json") # Notify the user
                writeConfig(1, value.split(':')[-1] + ".json") # Switch to our new layer file
                print("Switched to layer file: " + value.split(':')[-1] + ".json") # Notify the user
            else:
                writeConfig(1, value.split(':')[-1] + ".json") # Switch the layer's json into our config
                print("Switched to layer file: " + value.split(':')[-1] + ".json") # Notify the user

        elif value.startswith("script:"): # If value is a bash file
            print("Executing bash script: " + value.split(':')[-1])
            os.system('bash ' + scriptDir + value.split(':')[-1])

        elif value.startswith("py:"): # If value is a generic python file
            print("Executing python script: " + value.split(':')[-1])
            os.system('python ' + scriptDir + value.split(':')[-1])

        elif value.startswith("py2:"): # If value is a python2 file
            print("Executing python2 script: " + value.split(':')[-1])
            os.system('python2 ' + scriptDir + value.split(':')[-1])

        elif value.startswith("py3:"): # If value is a python3 file
            print("Executing python3 script: " + value.split(':')[-1])
            os.system('python3 ' + scriptDir + value.split(':')[-1])
        
        elif value.startswith("exec:"): # If value is a generic executable
            print("Executing file: " + value.split(':')[-1])
            os.system(scriptDir + value.split(':')[-1])
        
        else: # If value is a shell command
            print(keycode+": "+value)
            os.system(value)

def keebLoop(): # Reading the keyboard
    signal.signal(signal.SIGINT, signal_handler)
    ledger = keyLedger() # Reset the keyLedger
    for event in device.read_loop(): # Start infinitely geting events from our keyboard
        ledger.update(event) # Update the keyLedger with those events
        processKeycode(ledger.getFresh(1)) # Check if ledger.freshKeysList matches a command in our layer's json file

device = InputDevice(config()[0]) # Get a reference to the keyboard on the first line of our config file

getSettings() # Get settings from the json file in config

if args.layers: # If the user passed --layers
    getLayers() # show the user all layer json files and thier contents

elif args.add: # If the user passed --add
    device.grab() # Ensure only we receive input from the board
    writeConfig(1, "default.json") # Ensure we are on the default layer
    addKey() # Launch the key addition shell

elif args.device: # If the user passed --device
    device = InputDevice("/device/input/by-id/"+args.device) # Get a reference to the specified keyboard
    
    if os.path.exists(layerDir+args.device+".json") == False: # If the keyboard doesn't yet have a layer json file
        createLayer(args.device+".json") # Create one
        print("Created layer file: " + layerDir+args.device+".json") # And notify the user

    writeConfig(1, args.device+".json") # Switch to the specified board's layer json file
    print("Switched to layer file: " + args.device+".json") # Notify the user
    device.grab() # Ensure only we receive input from the board
    keebLoop() # Begin Reading the keybaord for macros

else: # If the user passed nothing
    device.grab() # Ensure only we receive input from the board
    writeConfig(1, "default.json") # Ensure we are on the default layer
    keebLoop() # Begin Reading the keybaord for macros