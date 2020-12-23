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

class keyLedger():
    """A class for finding all keys pressed at any time."""
    def __init__(self):
        self.keysList = [] # A list of keycodes of keys being held as strings
        self.newKeysList = [] # A list of keycodes of keys that were newly held when update() was last run as strings
        self.freshKeysList = [] # A list of keycodes of keys being held as strings that is empty unless a new key was pressed when update was last run
    
    def update(self, keyEvent):
        """Take an event and and updates the list of held keys accordingly."""
        self.newKeysList = [] # They are no longer new
        self.freshKeysList = [] # They are no longer fresh

        if keyEvent.type == ecodes.EV_KEY:
            keyEvent = categorize(keyEvent)
            keycode = keyEvent.keycode # Cache value that we are about to use a lot
            keystate = keyEvent.keystate

            if keystate == keyEvent.key_down or keystate == keyEvent.key_hold: # If a new key has been pressed or a key we might have missed the down event for is being held
                if not keycode in self.keysList: # If this key (which is held) is not in our list of keys that are held
                    print(f"New key tracked: {keycode}")
                    self.keysList += [keycode, ] # Add list of our (one) keycode to list of held keys
                    self.newKeysList += [keycode, ] # and to our list of newly held keys

            elif keystate == keyEvent.key_up: # If a key has been released
                if keycode in self.keysList: # And if we have that key marked as held
                    print(f"Tracked key {keycode} released.")
                    self.keysList.remove(keycode) # Then we remove it from our list of held keys

                else:
                    print(f"Untracked key {keycode} released.")

            if not self.newKeysList == []:
                self.freshKeysList = self.keysList
                print(f"New keys are: {self.newKeysList}")
                print(f"Fresh keys are: {self.freshKeysList}")

    def getList(self, returnType = 0):
        """Returns the list of held keys in different forms based on returnType.
        
        returnType values :
        0 - Returns the list as it is stored, as a list of strings.
        1 - Returns a single string with keycodes separated by \"+\"s, for use when reading/writing a layer json file.        
        """
        if returnType == 0:
            return self.keysList

        elif returnType == 1:
            keyListParsed = ""
            
            for keycode in self.keysList:
                keyListParsed += keycode
                
                if not keycode is self.keysList[-1]:
                    keyListParsed += "+"

            return keyListParsed

        else:
            print(f"Unrecognized value for returnType: {returnType}, returning None, expect errors!")
            return None

    def getNew(self, returnType = 0):
        """Returns the list of newly held keys in different forms based on returnType.
        
        returnType values :
        0 - Returns the list as it is stored, as a list of strings.
        1 - Returns a single string with keycodes separated by \"+\"s, for use when reading/writing a layer json file.        
        """
        if returnType == 0:
            return self.newKeysList

        elif returnType == 1:
            keyListParsed = ""
            
            for keycode in self.newKeysList:
                keyListParsed += keycode
                
                if not keycode is self.newKeysList[-1]:
                    keyListParsed += "+"

            return keyListParsed

        else:
            print(f"Unrecognized value for returnType: {returnType}, returning None, expect errors!")
            return None

    def getFresh(self, returnType = 0):
        """Returns the fresh (changed last update() call) list of held keys in different forms based on returnType.
        
        returnType values :
        0 - Returns the list as it is stored, as a list of strings.
        1 - Returns a single string with keycodes separated by \"+\"s, for use when reading/writing a layer json file.        
        """
        if returnType == 0:
            return self.freshKeysList

        elif returnType == 1:
            keyListParsed = ""
            
            for keycode in self.freshKeysList:
                keyListParsed += keycode
                
                if not keycode is self.freshKeysList[-1]:
                    keyListParsed += "+"

            return keyListParsed

        else:
            print(f"Unrecognized value for returnType: {returnType}, returning None, expect errors!")
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
    lines[lineNum] = data
    out = open(filePath+'config', 'w')
    out.writelines(lines)
    out.close()

parser = argparse.ArgumentParser()
parser.add_argument("--layers", help="Show saved layer files", action="store_true")
parser.add_argument("--device", help="Change target device")
parser.add_argument("--add", help="Add new keys", action="store_true")
args = parser.parse_args()

layerDir = filePath + "/layers/"
scriptDir = filePath + "/scripts/"

print("Welcome to Keebie")

def getLayers(): # Lists all the json files in /layers and thier contents
    print("Available Layers: \n")
    layerFt = ".json"
    layerFi = {}
    layers = [i for i in os.listdir(layerDir) if os.path.splitext(i)[1] == layerFt]

    for f in layers:
        with open(os.path.join(layerDir,f)) as file_object:
            layerFi[f] = file_object.read()
    
    for i in layerFi:
        print(i+layerFi[i])

def addKey(keycodeTimeout = 1): # Shell for adding new macros
    ledger = keyLedger() # Reset the keyLedger

    command = input("Enter the command you would like to attribute to a key on your second keyboard \n")

    if command.startswith("layer:"):
        if os.path.exists(command.split(':')[-1]+".json") == False:
            createLayer(command.split(':')[-1]+".json")
            print("Created layer file: " + command.split(':')[-1]+".json")

    print(f"Please press the key combination you would like to assign the command to and hold it until the next prompt after {keycodeTimeout} seconds.")

    loopStartTime = None
    signal.signal(signal.SIGINT, signal_handler)
    for event in dev.read_loop():
        if loopStartTime == None:
            loopStartTime = time.time()

        ledger.update(event)

        if not time.time() - loopStartTime < keycodeTimeout:
            break

    inp = input(f"Assign {command} to [{ledger.getList(1)}]? [Y/n] ")
    if inp == 'Y' or inp == '':
        newMacro = {}
        newMacro[ledger.getList(1)] = command
        writeJson(config()[1], newMacro)
        print(newMacro)

    else:
        print("Addition cancelled.")

        rep = input("Would you like to add another Macro? [Y/n] ")

        if rep == 'Y' or rep == '':
            addKey()

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

def readJson(filename): # Reads the file contents of a layer
    with open(layerDir+filename) as f:
        data = json.load(f)

    return data 

def processKeycode(keycode):
    if keycode in readJson(config()[1]):
        value = readJson(config()[1])[keycode]

        if value.startswith("layer:"):
            if os.path.exists(layerDir+value.split(':')[-1] + ".json") == False:
                createLayer(value.split(':')[-1]+".json")
                print("Created layer file: " + value.split(':')[-1]+".json")
                writeConfig(1, value.split(':')[-1] + ".json")
                print("Switched to layer file: " + value.split(':')[-1] + ".json")
            else:
                writeConfig(1, value.split(':')[-1] + ".json")
                print("Switched to layer file: " + value.split(':')[-1] + ".json")

        elif value.startswith("script:"):
            print("Executing bash script: " + value.split(':')[-1])
            os.system('bash ' + scriptDir + value.split(':')[-1])

        elif value.startswith("py:"):
            print("Executing python script: " + value.split(':')[-1])
            os.system('python ' + scriptDir + value.split(':')[-1])

        elif value.startswith("py2:"):
            print("Executing python2 script: " + value.split(':')[-1])
            os.system('python2 ' + scriptDir + value.split(':')[-1])

        elif value.startswith("py3:"):
            print("Executing python3 script: " + value.split(':')[-1])
            os.system('python3 ' + scriptDir + value.split(':')[-1])
        
        elif value.startswith("exec:"):
            print("Executing file: " + value.split(':')[-1])
            os.system(scriptDir + value.split(':')[-1])
        
        else:
            print(keycode+": "+value)    
            os.system(value)

def keebLoop(): # Reading the keyboard
    signal.signal(signal.SIGINT, signal_handler)
    ledger = keyLedger() # Reset the keyLedger
    for event in dev.read_loop():

        ledger.update(event)
        
        if not ledger.getFresh(1) == "":
            print(f"\n------------")
            print(ledger.getFresh(1))

        processKeycode(ledger.getFresh(1))

dev = InputDevice(config()[0])

ledger = keyLedger()

if args.layers:
    getLayers()

elif args.add:
    dev.grab()
    writeConfig(1, "default.json")
    addKey()

elif args.device: # Does not support devices not in /dev/inputs/by-id/
    dev = InputDevice("/dev/input/by-id/"+args.device)
    
    if os.path.exists(layerDir+args.device+".json") == False:
        createLayer(args.device+".json")
        print("Created layer file: " + layerDir+args.device+".json")

    writeConfig(1, args.device+".json")
    print("Switched to layer file: " + args.device+".json")
    dev.grab()
    keebLoop()

else:
    dev.grab()
    writeConfig(1, "default.json")
    keebLoop()