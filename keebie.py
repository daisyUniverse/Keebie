#!/usr/bin/env python3
#Keebie by Robin Universe & Friends

from evdev import InputDevice, categorize, ecodes
import sys
import signal
import os
import json
import argparse
import time
import subprocess
import shutil



# Utilities

print_debugs = False # Whether we should print debug information

def dprint(*args, **kwargs): # Print debug info (or don't)
    if print_debugs == True :
        print(*args, **kwargs)



# Global vars

installDataDir = "/usr/share/keebie/" # Path where default user configuration files and more and are installed
dataDir = os.path.expanduser("~") + "/.config/keebie/" # Path where user configuration files should be stored
dprint(dataDir)

layerDir = dataDir + "layers/" # Cache the full path to the /layers directory
deviceDir = dataDir + "devices/" # Cache the full path to the /devices directory
scriptDir = dataDir + "scripts/" # Cache the full path to the /scripts directory



# Signal handling

def signal_handler(signal, frame):
    end()

def end(ungrab=True): # Properly close the device file and exit the script
    if ungrab == True: # If we need to clean up grabbed macroDevices
        ungrabMacroDevices() # Ungrab all devices
        closeDevices() # Cleanly close all devices
    sys.exit(0) # Exit without error



# Key Ledger

class keyLedger():
    """A class for finding all keys pressed at any time."""
    def __init__(self, name="unnamed ledger"):
        self.name = name # Name of the ledger for debugging

        self.keysList = [] # A list of keycodes of keys being held as strings
        self.newKeysList = [] # A list of keycodes of keys that were newly held when update() was last run as strings
        self.freshKeysList = [] # A list of keycodes of keys being held as strings that is empty unless a new key was pressed when update() was last run
    
    def update(self, keyEvent):
        """Take an event and and updates the lists of keys accordingly."""
        self.newKeysList = [] # They are no longer new
        self.freshKeysList = [] # They are no longer fresh

        if keyEvent.type == ecodes.EV_KEY: # If the event is a related to a key, as opposed to a mouse movement or something (At least I think thats what this does)
            keyEvent = categorize(keyEvent) # Convert our EV_KEY input event into a KeyEvent
            keycode = keyEvent.keycode # Cache value that we are about to use a lot
            keystate = keyEvent.keystate

            if type(keycode) == list: # If the keycode is a list of keycodes (it can happen) 
                keycode = keycode[0] # Select the first one

            if keystate == keyEvent.key_down or keystate == keyEvent.key_hold: # If a new key has been pressed or a key we might have missed the down event for is being held
                if not keycode in self.keysList: # If this key (which is held) is not in our list of keys that are held
                    dprint(f"{self.name}) New key tracked: {keycode}")
                    self.keysList += [keycode, ] # Add list of our (one) keycode to list of held keys
                    self.newKeysList += [keycode, ] # and to our list of newly held keys

            elif keystate == keyEvent.key_up: # If a key has been released
                if keycode in self.keysList: # And if we have that key marked as held
                    dprint(f"{self.name}) Tracked key {keycode} released.")
                    self.keysList.remove(keycode) # Then we remove it from our list of held keys

                else:
                    print(f"{self.name}) Untracked key {keycode} released.") # If you see this that means we missed a key press, bad news. (But not fatal.)

            if settings["multiKeyMode"] == "combination": # If running in combination mode
                self.keysList.sort() # Sort key lists deterministically
                self.newKeysList.sort()

            if not self.newKeysList == []: # If new keys have pressed
                self.freshKeysList = self.keysList # Set fresh keys equal to helf keys
                dprint(f"{self.name}) New keys are: {self.newKeysList}") # Print debug info
                dprint(f"{self.name}) Fresh keys are: {self.freshKeysList}")

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
                
                if not keycode is self.freshKeysList[-1]: # If this isn't the last keycode
                    keyListParsed += "+" # Add a + to separate it from the previous keycode

            return keyListParsed # Return the parsed string 

        else: # If we don't recognize the return type
            print(f"Unrecognized value for returnType: {returnType}, returning None, expect errors!") # Say so
            return None



# Macro device

class macroDevice():
    """A class for managing devices."""
    def __init__(self, deviceJson):
        self.name = deviceJson.split(".json")[0] # Name of device for debugging

        jsonData = readJson(deviceJson, deviceDir) # Cache the data held in the device json file
        self.initialLayer = jsonData["initial_layer"] # Layer for the device the start on
        self.eventFile = "/dev/input/" + jsonData["event"] # The input event file
        self.udevTests = jsonData["udev_tests"] # Strings for udev matching

        self.currentLayer = self.initialLayer # Layer this device is currently on
        self.ledger = keyLedger(self.name) # A keyLedger to track input events on his devicet
        self.device = None # will be an InputEvent instance

    def addUdevRule(self, priority = 85):
        """Generate a udev rule for this device."""
        path = f"{priority}-keebie-{self.name}" # Name of the file for the rule (file extension added by the script)
        rule = ""

        for test in self.udevTests: # For all the udev tests
            rule += test + ", " # Add them together with commas
            dprint(rule)

        subprocess.run(["sudo", "sh", installDataDir + "/setup_tools/udevRule.sh", rule, path]) # Run the udev setup script with sudo

    def grabDevice(self):
        """Grab the device and set self.device to the grabbed device."""
        print("grabbing device " + self.name)
        self.device = InputDevice(self.eventFile) # Set self.device to the device of self.eventFile
        self.device.grab() # Grab the device

        self.setLeds() # Set the leds based on the current layer

    def ungrabDevice(self):
        """Ungrab the device."""
        print("ungrabbing device " + self.name)
        self.device.ungrab() # Do the thing that got said twice

    def close(self):
        """Try to close the device file gracefully."""
        print("closing device " + self.name)
        if self.device.fd > -1:
            try:
                os.close(self.device.fd)
            finally:
                self.device.fd = -1

    def read(self, process=True):
        """Read all queued events (if any), update the ledger, and process the keycodes (or don't)."""
        try: # Try to...
            for event in self.device.read(): # Read queued events from the device
                self.ledger.update(event) # Update the key ledger
                if process == True: # If we are processing the ledger
                    self.processLedger() # Process the newly updated ledger

        except BlockingIOError: # If no events are available
            pass

    def setLeds(self):
        """Set device leds bassed on current layer."""
        if "leds" in readJson(self.currentLayer): # If the current layer specifies LEDs
            leds = self.device.capabilities()[17] # Get a list of LEDs the device has

            onLeds = readJson(self.currentLayer)["leds"] # Get a list of LEDs to turn on
            dprint(f"device {self.name} setting leds {onLeds} on")

            for led in leds: # For all LEDs on the board
                if led in onLeds: # If the LED is to be set on
                    self.device.set_led(led, 1) # Set it on
                else:
                    self.device.set_led(led, 0) # Set it off
        else:
            print(f"Layer {readJson(self.currentLayer)} has no leds property, writing empty")
            writeJson(self.currentLayer, {"leds": []}) # Write an empty list for LEDs into the current layer
            leds = self.device.capabilities()[17] # Get a list of LEDs the device has

            for led in leds: # For all LEDs on the board
                self.device.set_led(led, 0) # Set it off

    def processLedger(self):
        """Given a keycode that might be in the current layer json file, check if it is and execute the appropriate commands"""
        keycode = self.ledger.getFresh(1) # Get a string of fresh keys
        if keycode == "": # If there are no fresh keys
            return
        
        dprint(f"{self.name} is processing {keycode} in layer {self.currentLayer}") # Print debug info

        if keycode in readJson(self.currentLayer): # If the keycode is in our current layer's json file
            value = readJson(self.currentLayer)[keycode] # Get the instructions associated with the keycode
            value = parseVars(value, self.currentLayer) # Parse any varables that may appear in the command

            if value.startswith("layer:"): # If value is a layerswitch command
                if os.path.exists(layerDir+value.split(':')[-1] + ".json") == False: # If the layer has no json file
                    createLayer(value.split(':')[-1]+".json") # Create one
                    print("Created layer file: " + value.split(':')[-1]+".json") # Notify the user
                    self.currentLayer = value.split(':')[-1] + ".json" # Switch to our new layer file
                    print("Switched to layer file: " + value.split(':')[-1] + ".json") # Notify the user

                else:
                    self.currentLayer = value.split(':')[-1] + ".json" # Set self.current layer to the target layer
                    print("Switched to layer file: " + value.split(':')[-1] + ".json") # Notify the user

                self.setLeds() # Set LEDs based on the new current layer

            else:
                if value.strip().endswith("&") == False and settings["forceBackground"]: # If value is not set in run in the background and our settings say to force running in the background
                    value += " &" # Force running in the background
                    
                if value.strip().endswith("&") == False and settings["backgroundInversion"]: # If value is not set to run in the background and our settings say to invert background mode
                    value += " &" # Force running in the background
                
                elif value.strip().endswith("&") and settings["backgroundInversion"]: # Else if value is set to run in the background and our settings say to invert background mode
                    value = value.rstrip(" &") # Remove all spaces and &s from the end of value, there might be a better way but this is the best I've got

                scriptTypes = { # A dict of script types and thier interpreters with a trailing space
                    "script": "bash ",
                    "py": "python ",
                    "py2": "python2 ",
                    "py3": "python3 ",
                    "exec": "",
                }

                isScript = False # If the value is a script

                for scriptType in scriptTypes.keys(): # For recognized script types
                    if value.startswith(scriptType + ":"): # Check if value is one of said script types
                        print(f"Executing {scriptTypes[scriptType]}script {value.split(':')[-1]}") # Notify the user we re running a script
                        value = scriptTypes[scriptType] + scriptDir + value.split(':')[-1] # Set value to executable format
                        isScript = True # Set that this is a script
                        break # Break the loop
                
                if isScript == False: # If this is not a script (i.e. it is a shell command)
                    print(keycode+": "+value) # Notify the user of the command
                
                os.system(value) # Execute value

    def clearLedger(self):
        """Clear this devices ledger."""
        try: # Try to...
            for event in self.device.read(): # For all queued events
                pass # Completely ignore them
        
        except BlockingIOError: # If there arn't any queued events
            pass # Ignore that too
        
        self.ledger = keyLedger(self.name) # Reset the ledger


macroDeviceList = [] # List of macroDevice instances

standardLeds = { # A dict of standard LED ids and thier names
    0: "num lock",
    1: "caps lock",
    2: "scroll lock",
}

def setupMacroDevices():
    """Setup a macroDevice instance based on the contents of deviceDir."""
    global macroDeviceList # Globalize macroDeviceList
    deviceJsonList = [deviceJson for deviceJson in os.listdir(deviceDir) if os.path.splitext(deviceJson)[1] == ".json"] # Get list of json files in deviceDir
    
    dprint(deviceJsonList) # Print debug info

    for deviceJson in deviceJsonList: # For all json files in deviceDir
        macroDeviceList += [macroDevice(deviceJson), ] # Setup a macroDevice instance for all files and save them to macroDeviceList

def grabMacroDevices():
    """Grab all devices with macroDevices."""
    for device in macroDeviceList:
        device.grabDevice()

def ungrabMacroDevices():
    """Ungrab all devices with macroDevices."""
    for device in macroDeviceList:
        device.ungrabDevice()

def closeDevices():
    """Close all devices."""
    for device in macroDeviceList:
        device.close()

def mergeDeviceLedgers():
    """Merge the key ledgers of all macroDevices into one and return it."""
    returnLedger = keyLedger() # Create an empty key ledger
    
    for device in macroDeviceList: # For all macroDevices
        returnLedger.keysList += device.ledger.keysList # Add the devices held keys to the retunrn ledger
        returnLedger.newKeysList += device.ledger.newKeysList # Add the devices new keys to the retunrn ledger
        returnLedger.freshKeysList += device.ledger.freshKeysList # Add the devices fresh keys to the retunrn ledger

    return returnLedger # Return the ledger we built

def clearDeviceLedgers():
    """Clear all device ledgers."""
    for device in macroDeviceList:
        device.clearLedger()

def readDevices(process=True):
    """Read and optionally process all devices events."""
    for device in macroDeviceList:
        device.read(process)



# JSON

def readJson(filename, dir = layerDir): # Reads the file contents of a layer (or any json file named filename in the directory dir)
    with open(dir+filename) as f:
        data = json.load(f)

    return data 

def writeJson(filename, data, dir = layerDir): # Appends new data to a specified layer (or any json file named filename in the directory dir)
    try: # Try to...
        with open(dir+filename) as f: # Open an existing file
            prevData = json.load(f) # And copy store its data
    except FileNotFoundError: # If the file doesn't exist
        prevData = {}

    prevData.update(data)

    with open(dir+filename, 'w+') as outfile:
        json.dump(prevData, outfile, indent=3)

def popDictRecursive(dct, keyList): # Given a dict and list of key names of dicts follow said list into the dicts recursivly and pop the finall result, it's hard to explain 
    if len(keyList) == 1:
        dct.pop(keyList[0])

    elif len(keyList) > 1:
        popDictRecursive(dct[keyList[0]], keyList[1:])

def popJson(filename, key, dir = layerDir): # Removes the key key and it's value from a layer (or any json file named filename in the directory dir)
    with open(dir+filename) as f:
        prevData = json.load(f)

    if type(key) == str:
        prevData.pop(key)
    elif type(key) == list:
        popDictRecursive(prevData, key)

    with open(dir+filename, 'w+') as outfile:
        json.dump(prevData, outfile, indent=3)



# Layer file

def createLayer(filename): # Creates a new layer with a given filename
    shutil.copyfile(installDataDir + "/data/layers/default.json", layerDir + filename) # Copy the provided default layer file from installedDataDir to specified filename



# Settings file

settings = { # A dict of settings to be used across the script
    "multiKeyMode": "combination",
    "forceBackground": False,
    "backgroundInversion": False,
	"loopDelay": 0.0167,
}

settingsPossible = { # A dict of lists of valid values for each setting (or if first element is type then list of acceptable types in descending priority)
    "multiKeyMode": ["combination", "sequence"],
    "forceBackground": [True, False],
    "backgroundInversion": [True, False],
	"loopDelay": [type, float, int],
}

def getSettings(): # Reads the json file specified on the third line of config and sets the values of settings based on it's contents
    print(f"Loading settings from {dataDir}/settings.json") # Notify the user we are getting settings and tell them the file we are using to do so

    settingsFile = readJson("settings.json", dataDir) # Get a dict of the keys and values in our settings file
    for setting in settings.keys(): # For every setting we expect to be in our settings file
        if type == settingsPossible[setting][0]: # If first element is type
            if type(settingsFile[setting]) in settingsPossible[setting]: # If the value in our settings file is valid
                dprint(f"Found valid typed value: \"{type(settingsFile[setting])}\" for setting: \"{setting}\"")
                settings[setting] = settingsFile[setting] # Write it into our settings
            else :
                print(f"Value: \"{settingsFile[setting]}\" for setting: \"{setting}\" is of invalid type, defaulting to {settings[setting]}") # Warn the user of invalid settings in the settings file
        else:
            if settingsFile[setting] in settingsPossible[setting]: # If the value in our settings file is valid
                dprint(f"Found valid value: \"{settingsFile[setting]}\" for setting: \"{setting}\"")
                settings[setting] = settingsFile[setting] # Write it into our settings
            else :
                print(f"Value: \"{settingsFile[setting]}\" for setting: \"{setting}\" is invalid, defaulting to {settings[setting]}") # Warn the user of invalid settings in the settings file

    dprint(f"Settings are {settings}") # Debug info



# Keypress processing

def parseVars(commandStr, layer): # Given a command from the layer json file replace vars with their values and return the string
    # Vars we will need in the loop
    returnStr = "" # The string to be retuned
    escaped = False # If we previously encountered an escape char
    escapeChar = "\\" # What is out escape char
    varChars = ("%", "%") # What characters start and end a varable name
    inVar = False # If we are in a varable name
    varName = "" # What the varables name is so far

    for char in commandStr : # Iterate over the cars of the input
        if escaped == True : # If char is escaped add it unconditionally and reset escaped
            returnStr += char
            escaped = False
            continue

        if escaped == False and char == escapeChar : # If char is en unescaped escape char set escaped
            escaped = True
            continue

        if inVar == False and char == varChars[0] : # If we arn't in a varable and chars is the start of one set inVar
            inVar = True
            continue

        if inVar == True and char == varChars[1] : # If we are in a varable and char ends it parse the varables value, add it to returnStr if valid, and reset inVar and varName
            try :
                returnStr += readJson(layer)["vars"][varName]
            except KeyError :
                print(f"unknown var {varName} in command {commandStr}, skiping command")
                return ""

            inVar = False
            varName = ""
            continue

        if inVar == True : # If we are in a varable name add char to varName
            varName += char
            continue

        returnStr += char # If none of the above (because we use continue) add char to returnStr

    return returnStr # All done, return the result



# Shells

def getLayers(): # Lists all the json files in /layers and thier contents
    print("Available Layers: \n")
    layerFt = ".json"
    layerFi = {}
    layers = [i for i in os.listdir(layerDir) if os.path.splitext(i)[1] == layerFt] # Get a list of paths to all files that match our file extension

    for f in layers:
        with open(os.path.join(layerDir,f)) as file_object:
            layerFi[f] = file_object.read() # Build a list of the files at those paths
    
    for i in layerFi:
        print(i+layerFi[i]) # And display thier contents to the user
    end()

def detectKeyboard(path = "/dev/input/by-id/"): # Detect what file a keypress is coming from
    print("Please press a key on the desired input device...")
    time.sleep(.5) # Small delay to avoid detecting the device you started the script with
    dev = ""
    while dev == "": # Wait for this command to output the device name, loops every 1s
        dev = subprocess.check_output("inotifywatch " + path +"/* -t 1 2>&1 | grep " + path + " | awk 'NF{ print $NF }'", shell=True ).decode('utf-8').strip()
    return dev

def addKey(layer, key = None, command = None, keycodeTimeout = 1): # Shell for adding new macros
    ledger = keyLedger() # Reset the keyLedger

    if key == None and command == None:
        relaunch = True
    else:
        relaunch = False
    
    if command == None:
        command = input("Enter the command you would like to attribute to a key on your second keyboard \n") # Get the command the user wishs to bind

        if command.startswith("layer:"): # If the user entered a layer switch command
            if os.path.exists(command.split(':')[-1]+".json") == False: # Check if the layer json file exsits
                createLayer(command.split(':')[-1]+".json") # If not create it
                print("Created layer file: " + command.split(':')[-1]+".json") # And notify the user

                print("standard LEDs:")
                for led in standardLeds.items(): # For all LEDs on most boards
                    print(f"-{led[0]}: {led[1]}") # List it

                onLeds = input("Please choose what LEDs should be enable on this layer (comma and/or space separated list)") # Prompt the user for a list of LED numbers
                onLeds = onLeds.replace(",", " ").split() # Split the input list

                onLedsInt = []
                for led in onLeds: # For all strs in the split list
                    onLedsInt.append(int(led)) # Cast the str to int and add it to a list

                writeJson(command.split(':')[-1]+".json", {"leds": onLedsInt}) # Write the input list to the layer file

    if key == None:
        print(f"Please press the key combination you would like to assign the command to and hold it for {keycodeTimeout} seconds until the next prompt.")

        loopStartTime = None
        signal.signal(signal.SIGINT, signal_handler)

        clearDeviceLedgers() # Clear all device ledgers

        started = False # Whether the timer is started
        while True: # Start an endless loop
            readDevices(False) # Read all devices (but don't process keycodes)
            if started == False and not mergeDeviceLedgers().getList(0) == []: # If the timer hasn't started yet and keys are being pressed
                started = True # Start the timer
                loopStartTime = time.time() # Set time stamp for comparison

            if not loopStartTime == None and not time.time() - loopStartTime < keycodeTimeout: # Unless the time runs out
                break # Then we break the loop    

        key = mergeDeviceLedgers().getList(1)

    inp = input(f"Assign {command} to [{key}]? [Y/n] ") # Ask the user if we (and they) got the command and binding right
    if inp == 'Y' or inp == '': # If we did 
        newMacro = {}
        newMacro[key] = command
        writeJson(layer, newMacro) # Write the binding into our layer json file
        print(newMacro) # And print it back

    else: # If we didn't
        print("Addition cancelled.") # Confirm we have cancelled the binding

    if relaunch:
        rep = input("Would you like to add another Macro? [Y/n] ") # Offer the user to add another binding

        if rep == 'Y' or rep == '': # If they say yes
            addKey(layer) # Restart the shell

        end()

def editSettings(): # Shell for editing settings
    settingsFile = readJson("settings.json", dataDir) # Get a dict of the keys and values in our settings file
    
    settingsList = [] # Create a list for key-value pairs of settings 
    for setting in settings.items(): # For every key-value pair in our settings dict
        settingsList += [setting, ] # Add the pair to our list of seting pairs

    print("Choose what value you would like to edit.") # Ask the user to choose which setting they wish to edit
    for settingIndex in range(0, len(settingsList)): # For the index number of every setting pair in our list of setting pairs
        print(f"-{settingIndex + 1}: {settingsList[settingIndex][0]}   [{settingsList[settingIndex][1]}]") # Print an entry for every setting, as well as a number associated with it and it's current value
    
    selection = input("Please make you selection: ") # Take the users input as to which setting they wish to edit
    
    try: # Try to...
        intSelection = int(selection) # Convert the users input from str to int
    
    except ValueError: # If the conversion to int fails
        print("Exiting...") # Tell the user we are exiting
        end(False) # And do so

    if intSelection in range(1, len(settingsList) + 1): # If the users input corresponds to a listed setting
        settingSelected = settingsList[int(selection) - 1][0] # Store the selected setting's name
        print(f"Editing item \"{settingSelected}\"") # Tell the user we are thier selection
    
    else: # If the users input does not correspond to a listed setting
        print("Input out of range, exiting...") # Tell the user we are exiting
        end(False) # And do so

    if type == settingsPossible[settingSelected][0]: # If first element of settingsPossible is type
        print(f"Enter a value {settingSelected} that is of one of these types.")
        for valueIndex in range(1, len(settingsPossible[settingSelected])): # For the index number of every valid type of the users selected setting
            print("- " + settingsPossible[settingSelected][valueIndex].__name__) # Print an entry for every valid type
            
        selection = input("Please enter a value: ") # Prompt the user for input

        if selection == "": # If none is provided
            print("Exiting...")
            end(False) # Exit

        for typePossible in settingsPossible[settingSelected]: # For all valid types
            dprint(typePossible)
            if typePossible == type: # If it is type
                continue
            try: # Try to...
                selection = typePossible(selection) # Cast the users input to the type
                break
            except ValueError: # If casting fails
                pass
        
        if type(selection) in settingsPossible[settingSelected]: # If we have successfully casted to a valid type
            writeJson("settings.json", {settingSelected: selection}, dataDir) # Write the setting into the settings file
            print(f"Set \"{settingSelected}\" to \"{selection}\"")
        else:
            print("Input can't be casted to a supported type, exiting...") # Complain about the bad input
            end(False) # And exit

    else:
        print(f"Choose one of {settingSelected}\'s possible values.") # Ask the user to choose which value they want to assign to their selected setting
        for valueIndex in range(0, len(settingsPossible[settingSelected])): # For the index number of every valid value of the users selected setting
            print(f"-{valueIndex + 1}: {settingsPossible[settingSelected][valueIndex]}", end = "") # Print an entry for every valid value, as well as a number associate, with no newline
            if settingsPossible[settingSelected][valueIndex] == settings[settingSelected]: # If a value is the current value of the selected setting
                print("   [current]") # Tell the user and add a newline

            else:
                print() # Add a newline

        selection = input("Please make you selection: ") # Take the users input as to which value they want to assign to their selected setting

        try: # Try to...
            intSelection = int(selection) # Convert the users input from str to int
            if intSelection in range(1, len(settingsPossible[settingSelected]) + 1): # If the users input corresponds to a listed value
                valueSelected = settingsPossible[settingSelected][int(selection) - 1] # Store the selected value
                writeJson("settings.json", {settingSelected: valueSelected}, dataDir) # Write it into our settings json file
                print(f"Set \"{settingSelected}\" to \"{valueSelected}\"") # And tell the user we have done so
            
            else: # If the users input does not correspond to a listed value
                print("Input out of range, exiting...") # Tell the user we are exiting
                end(False) # And do so

        except ValueError: # If the conversion to int fails
            print("Exiting...") # Tell the user we are exiting
            end(False) # And do so

    getSettings() # Refresh the settings in our settings dict with the newly changed setting

    rep = input("Would you like to change another setting? [Y/n] ") # Offer the user to edit another setting

    if rep == 'Y' or rep == '': # If they say yes
        editSettings() # Restart the shell

    else:
        end(False)

def editLayer(layer = "default.json"): # Shell for editing a layer file (default by default)
    LayerDict = readJson(layer, layerDir) # Get a dict of keybindings in the layer file
    
    keybindingsList = [] # Create a list for key-value pairs of keybindings
    for keybinding in LayerDict.items(): # For every key-value pair in our layers dict
        keybindingsList += [keybinding, ] # Add the pair to our list of keybinding pairs

    print("Choose what binding you would like to edit.") # Ask the user to choose which keybinding they wish to edit
    for bindingIndex in range(0, len(keybindingsList)): # For the index number of every binding pair in our list of binding pairs
        if keybindingsList[bindingIndex][0] == "leds":
            print(f"-{bindingIndex + 1}: Edit LEDs")
        elif keybindingsList[bindingIndex][0] == "vars":
            print(f"-{bindingIndex + 1}: Edit layer varables")
        else:
            print(f"-{bindingIndex + 1}: {keybindingsList[bindingIndex][0]}   [{keybindingsList[bindingIndex][1]}]") # Print an entry for every binding, as well as a number associated with it and it's current value
    
    selection = input("Please make you selection: ") # Take the users input as to which binding they wish to edit
    
    try: # Try to...
        intSelection = int(selection) # Comvert the users input from str to int
        if intSelection in range(1, len(keybindingsList) + 1): # If the users input corresponds to a listed binding
            bindingSelected = keybindingsList[int(selection) - 1][0] # Store the selected bindings's key
            print(f"Editing item \"{bindingSelected}\"") # Tell the user we are editing their selection
        
        else: # If the users input does not correspond to a listed binding
            print("Input out of range, exiting...") # Tell the user we are exiting
            end() # And do so

    except ValueError: # If the conversion to int fails
        print("Exiting...") # Tell the user we are exiting
        end() # And do so

    if bindingSelected == "leds":
        print("standard LEDs:")
        for led in standardLeds.items(): # For all LEDs on most boards
            print(f"-{led[0]}: {led[1]}") # List it

        onLeds = input("Please choose what LEDs should be enable on this layer (comma and/or space separated list)") # Prompt the user for a list of LED numbers
        onLeds = onLeds.replace(",", " ").split() # Split the input list

        onLedsInt = []
        for led in onLeds: # For all strs in the split list
            onLedsInt.append(int(led)) # Cast the str to int and add it to a list

        writeJson(layer, {"leds": onLedsInt}) # Write the input list to the layer file

    elif bindingSelected == "vars":
        varsDict = readJson(layer, layerDir)["vars"] # Get a dict of layer vars in the layer file
        
        varsList = [] # Create a list for key-value pairs of layer vars
        for var in varsDict.items(): # For every key-value pair in our layer vars dict
            varsList += [var, ] # Add the pair to our list of layer var pairs

        print("Choose what varable you would like to edit.") # Ask the user to choose which var they wish to edit
        for varIndex in range(0, len(varsList)): # For the index number of every var pair in our list of var pairs
            print(f"-{varIndex + 1}: {varsList[varIndex][0]}   [{varsList[varIndex][1]}]")
            
        selection = input("Please make you selection: ") # Take the users input as to which var they wish to edit
    
        try: # Try to...
            intSelection = int(selection) # Comvert the users input from str to int
            if intSelection in range(1, len(varsList) + 1): # If the users input corresponds to a listed var
                varSelected = varsList[int(selection) - 1][0] # Store the selected var's key
                print(f"Editing item \"{varSelected}\"") # Tell the user we are editing their selection
            
            else: # If the users input does not correspond to a listed var
                print("Input out of range, exiting...") # Tell the user we are exiting
                end() # And do so

        except ValueError: # If the conversion to int fails
            print("Exiting...") # Tell the user we are exiting
            end() # And do so

        print(f"Choose am action to take on {varSelected}.") # Ask the user to choose what they want to do with their selected var
        # Prompt the user with a few possible actions
        print("-1: Delete varable.")
        print("-2: Edit varable name.")
        print("-3: Edit varable value.")
        print("-4: Cancel.")

        selection = input("Please make you selection: ") # Take the users input as to what they want to do with their selected var

        try: # Try to...
            intSelection = int(selection) # Convert the users input from str to int

            if intSelection == 1: # If the user selected delete
                popJson(layer, ["vars", varSelected]) # Remove the var
            elif intSelection == 2: # If the user selected edit name
                varName = input("Please input new name: ") # Ask the user for a new name
                varsDict.update({varName: varsDict[varSelected]}) # Add new name and value to varDict
                writeJson(layer, {"vars": varsDict}) # Set layer's vars to varDict
                popJson(layer, ["vars", varSelected]) # Note: if the user replaces the original name with the same name this will delete the binding
            elif intSelection == 3: # If the user selected edit value
                varVal = input("Please input new value: ") # Ask the user for a new value
                varsDict.update({varSelected: varVal}) # Update name to new value in varDict
                writeJson(layer, {"vars": varsDict}) # Set layer's vars to varDict
            elif intSelection == 4: # If the user selected cancel
                pass # Pass back to the previous level

            else: # If the users input does not correspond to a listed value
                print("Input out of range, exiting...") # Tell the user we are exiting
                end() # And do so

        except ValueError: # If the conversion to int fails
            print("Exiting...") # Tell the user we are exiting
            end() # And do so

    else:
        print(f"Choose am action to take on {bindingSelected}.") # Ask the user to choose what they want to do with their selected binding
        # Prompt the user with a few possible actions
        print("-1: Delete binding.")
        print("-2: Edit binding key.")
        print("-3: Edit binding command.")
        print("-4: Cancel.")

        selection = input("Please make you selection: ") # Take the users input as to what they want to do with their selected binding

        try: # Try to...
            intSelection = int(selection) # Convert the users input from str to int

            if intSelection == 1: # If the user selected delete
                popJson(layer, bindingSelected) # Remove the binding
            elif intSelection == 2: # If the user selected edit key
                addKey(command = LayerDict[bindingSelected]) # Launch the key addition shell and preserve the command
                popJson(layer, bindingSelected) # Note: if the user replaces the original key with the same key this will delete the binding
            elif intSelection == 3: # If the user selected edit command
                addKey(key = bindingSelected) # Launch the key addition shell and preserve the key
            elif intSelection == 4: # If the user selected cancel
                pass # Pass back to the previous level

            else: # If the users input does not correspond to a listed value
                print("Input out of range, exiting...") # Tell the user we are exiting
                end() # And do so

        except ValueError: # If the conversion to int fails
            print("Exiting...") # Tell the user we are exiting
            end() # And do so

    rep = input("Would you like to edit another binding? [Y/n] ") # Offer the user to edit another binding

    if rep == 'Y' or rep == '': # If they say yes
        editLayer() # Restart the shell

    else:
        end()

def newDevice(name = None, eventPath = "/dev/input"):
    """Add a new json file to devices/."""
    eventFile = detectKeyboard(eventPath) # Promt the user for a device
    eventFile = os.path.basename(eventFile) # Get the devices filename from its filepath

    # allUdevProperties = subprocess.check_output("udevadm info -a --name=/dev/input/" + eventFile + " | grep -P \"[^=\s]+==\\\"[^=\s]+\\\"\"", shell=True).decode('utf-8')

    # udevProperties = []
    # for property in allUdevProperties.splitlines():
    #     udevProperties += [str(property).strip(), ]

    input(f"\nDevice is {eventFile}, please press enter to continue...") # Ensure the stdin is empty

    # for propertyIndex in range(0, len(udevProperties)):
    #     print(f"-{propertyIndex + 1}: {udevProperties[propertyIndex]}")

    # selectedProperties = input("Please select properties by thier numbers (comma and/or space separated list), if unsure look for \"ATTRS{idVendor}\" and \"ATTRS{idProduct}\"")
    # selectedProperties = selectedProperties.replace(",", " ").split()

    # selectedPropertiesInts = []
    # for property in selectedProperties:
    #     selectedPropertiesInts.append(int(property))

    # dprint(selectedPropertiesInts)

    # selectedPropertiesList = []
    # for propertyIndex in range(1, len(udevProperties) + 1):
    #     if propertyIndex in selectedPropertiesInts:
    #         selectedPropertiesList += [udevProperties[propertyIndex - 1], ]

    selectedPropertiesList = [f"KERNEL==\"{eventFile}\""] # Make an udev rule matching the device file

    deviceJsonDict = { # Construct the device data dict
        "initial_layer": "default.json",
        "event": eventFile,
        "udev_tests": selectedPropertiesList,
    }

    writeJson(eventFile + ".json", deviceJsonDict, deviceDir) # Write device data into a json file

    macroDevice(eventFile + ".json").addUdevRule() # Create a mcro device and make a udev rule, the user will be prompted for sudo

    end(False)



# Setup

def firstUses(): # Setup to be run when a user first runs keebie
    shutil.copytree(installDataDir + "data/", dataDir) # Copy template configuration files to user
    print(f"configuration files copied from {installDataDir}/data/ to {dataDir}") # And inform the user



# Arguments

parser = argparse.ArgumentParser() # Set up command line arguments

parser.add_argument("--layers", "-l", help="Show saved layer files", action="store_true")
parser.add_argument("--detect", "-d", help="Detect keyboard device file", action="store_true")

try:
    parser.add_argument("--add", "-a", help="Adds new macros to the selected layer file (or default layer if unspecified)", nargs="?", default=False, const="default.json", metavar="layer", choices=[i for i in os.listdir(layerDir) if os.path.splitext(i)[1] == ".json"])
except FileNotFoundError :
    parser.add_argument("--add", "-a", help="Adds new macros to the selected layer file (or default layer if unspecified)", nargs="?", default=False, const="default.json", metavar="layer")

parser.add_argument("--settings", "-s", help="Edits settings file", action="store_true")

try:
    parser.add_argument("--edit", "-e", help="Edits specified layer file (or default layer if unspecified)", nargs="?", default=False, const="default.json", metavar="layer", choices=[i for i in os.listdir(layerDir) if os.path.splitext(i)[1] == ".json"])
except FileNotFoundError :
    parser.add_argument("--edit", "-e", help="Edits specified layer file (or default layer if unspecified)", nargs="?", default=False, const="default.json", metavar="layer")

parser.add_argument("--new", "-n", help="Add a new device file", action="store_true")

parser.add_argument("--verbose", "-v", help="Print extra debugging information", action="store_true")

args = parser.parse_args()

print_debugs = args.verbose


# Main code

print("Welcome to Keebie")

signal.signal(signal.SIGINT, signal_handler)

if not os.path.exists(dataDir): # If the user we are running as does not have user configuration files
    print("You are running keebie without user configuration files installed") # Inform the user
    firstUses() # Run first time user setup

setupMacroDevices() # Setup all devices

getSettings() # Get settings from the json file in config


if args.layers: # If the user passed --layers
    getLayers() # Show the user all layer json files and their contents

elif args.add: # If the user passed --add
    grabMacroDevices()
    addKey(args.add) # Launch the key addition shell

elif args.settings: # If the user passed --settings
    editSettings() # Launch the setting editing shell

elif args.detect: # If the user passed --detect
    print(detectKeyboard("/dev/input/")) # Launch the keyboard detection function

elif args.edit: # If the user passed --edit
    grabMacroDevices()
    editLayer(args.edit) # Launch the layer editing shell

elif args.new: # If the user passed --new
    newDevice()

else: # If the user passed nothing
    time.sleep(.5)
    grabMacroDevices() # Grab all the devices

    while True : # Enter an infinite loop
        readDevices() # Read all devices and process the keycodes
        time.sleep(settings["loopDelay"]) # Sleep so we don't eat the poor little CPU