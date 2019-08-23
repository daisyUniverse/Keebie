#Keebie by Elisha Shaddock UwU

from evdev import InputDevice, categorize, ecodes
import sys
import signal
import os
import json

def signal_handler(signal, frame):
    sys.exit(0)

def config():
    f=open("config","r")                                     # Opens config file.
    if f.mode =='r':
        config = f.read().splitlines()
        return config

def writeConfig(lineNum, data):
    lines = open('config', 'r').readlines()
    lines[lineNum] = data
    out = open('config', 'w')
    out.writelines(lines)
    out.close()

args = len(sys.argv) - 1
arg = sys.argv[args]
dev = InputDevice(config()[0])
layerDir = os.getcwd() + "/layers/"
scriptDir = os.getcwd() + "/scripts/"
dev.grab()

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
                            writeConfig(1, value.split(':')[-1] + ".json")
                            print("Switched to layer file: " + value.split(':')[-1] + ".json")
                            break
                        elif value.startswith("script:"):
                            os.system('bash ' + scriptDir + value.split(':')[-1] + '.sh')
                            print("Executing bash script: " + value.split(':')[-1] + '.sh')
                            break
                        elif value.startswith("py:"):
                            os.system('python ' + scriptDir + value.split(':')[-1] + '.py')
                            print("Executing python script: " + value.split(':')[-1] + '.py')
                            break
                        else:
                            os.system(value)
                            print(keys+": "+value)

if arg == '-l' or arg == '--layers': # check args
    getLayers()
elif arg == '-a' or arg == '--add':
    addKey()
elif arg == '-h' or arg == '--help':
    print("-l, --list | List all saved layer files")
    print("-a, --add  | add new macro to the current layer")
    print("-h, --help | I wonder.")
    print("\n #MACRO PREFIX# ")
    print(" (use these in --add mode) \n")
    print("layer:layername     | create a new layer file, and assign a key to switch to that layer")
    print("script:scriptname   | launches <scriptname.sh> from your scripts folder")
    print("py:pythonscriptname | launches <pythonscriptname.py> from your scripts folder")
    print("\n")
else:
    keebLoop()

