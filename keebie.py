#!/bin/python3
#Keebie by Elisha Shaddock UwU

from evdev import InputDevice, categorize, ecodes
import sys
import signal
import os
import json
import argparse

filePath = os.path.abspath(os.path.dirname(sys.argv[0])) + "/" # Get the absolute path to the directory of this script for use when opening files
print(filePath)

def signal_handler(signal, frame):
    sys.exit(0)

def config():
    f=open(filePath+"config","r")                                     # Opens config file.
    if f.mode =='r':
        config = f.read().splitlines()
        for confLine in range(0, len(config)) : # Strip leading and trailing whitespaces from each line of the config
            config[confLine] = config[confLine].strip() 
        return config

def writeConfig(lineNum, data):
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

def getLayers(): # Lists all the json files in /layers
    print("Available Layers: \n")
    layerFt = ".json"
    layerFi = {}
    layers = [i for i in os.listdir(layerDir) if os.path.splitext(i)[1] == layerFt]

    for f in layers:
        with open(os.path.join(layerDir,f)) as file_object:
            layerFi[f] = file_object.read()
    
    for i in layerFi:
        print(i+layerFi[i])

def addKey(): # shell for adding new macros
    command = input("Enter the command you would like to attribute to a key on your second keyboard \n")
    print("Please press the key you would like to assign the command to...")
    if command.startswith("layer:"):
        if os.path.exists(command.split(':')[-1]+".json") == False:
            createLayer(command.split(':')[-1]+".json")
            print("Created layer file: " + command.split(':')[-1]+".json")
            
    for event in dev.read_loop():
        if event.type == ecodes.EV_KEY:
            key = categorize(event)
            if key.keystate == key.key_down:
                inp = input("Assign "+command+" to ["+key.keycode+"]? [Y/n] ")
                if inp == 'Y' or inp == '':
                    newMacro = {}
                    newMacro[key.keycode] = command
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

def createLayer(filename):
    basedata = {"KEY_ESC": "layer:default"}

    with open(layerDir+filename, 'w+') as outfile:
        json.dump(basedata, outfile, indent=3)

def readJson(filename): # reads the file contents of a layer
    with open(layerDir+filename) as f:
        data = json.load(f)
    return data 

def keebLoop(): # reading the keyboard
    signal.signal(signal.SIGINT, signal_handler)
    for event in dev.read_loop():
        if event.type == ecodes.EV_KEY:
            key = categorize(event)
            if key.keystate == key.key_down:
                for keys in readJson(config()[1]):
                    value = readJson(config()[1])[keys]
                    if key.keycode == keys:
                        if value.startswith("layer:"):
                            if os.path.exists(layerDir+value.split(':')[-1] + ".json") == False:
                                createLayer(value.split(':')[-1]+".json")
                                print("Created layer file: " + value.split(':')[-1]+".json")
                                writeConfig(1, value.split(':')[-1] + ".json")
                                print("Switched to layer file: " + value.split(':')[-1] + ".json")
                                break
                            else:
                                writeConfig(1, value.split(':')[-1] + ".json")
                                print("Switched to layer file: " + value.split(':')[-1] + ".json")
                                break
                        elif value.startswith("script:"):
                            os.system('bash ' + scriptDir + value.split(':')[-1])
                            print("Executing bash script: " + value.split(':')[-1])
                            break
                        elif value.startswith("py:"):
                            os.system('python ' + scriptDir + value.split(':')[-1])
                            print("Executing python script: " + value.split(':')[-1])
                            break
                        elif value.startswith("py2:"):
                            os.system('python2 ' + scriptDir + value.split(':')[-1])
                            print("Executing python2 script: " + value.split(':')[-1])
                            break
                        elif value.startswith("py3:"):
                            os.system('python3 ' + scriptDir + value.split(':')[-1])
                            print("Executing python3 script: " + value.split(':')[-1])
                            break
                        elif value.startswith("exec:"):
                            os.system(scriptDir + value.split(':')[-1])
                            print("Executing file: " + value.split(':')[-1])
                            break
                        else:
                            os.system(value)
                            print(keys+": "+value)

dev = InputDevice(config()[0])

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