# Keebie

More keyboards = faster hacking



#### What does it do:

Keebie is basically a small script for assigning and executing commands on a theoretically unlimited number of keyboards. So you can make the spacebar search for a window and paste something. Or make the M button run a script. Or even crazier things like triple tapping a key combination to execute a command.



#### How to set up:

 - If somebody has made available a package for your OS go ahead install it and move on.

 - If not you can download the source and run `make install`. Make sure you have `python3`, `python3-evdev`, and `inotify-tools` (or your package manager's equivalents) installed.

 - If you would like to build a package of Keebie download the source, [install fpm](https://fpm.readthedocs.io/en/latest/installing.html), and run `make pkg pkg_type="<type>"`.

 Once you've installed Keebie you should run `keebie --new` to set up a macro device.



#### Options:

 - `--layers`, `-l`
   - Display the contents of all layer files.

 - `--detect`, `-d`
   - Tell you the path to a device you press a key on.

 - `--add [layer]`, `-a [layer]`
   - Launch a shell to add a macro to a layer, if no layer is specified this adds to `default.json`.
   - This requires that at least one device has been set up with `--edit`
   - See layer syntax section below for more information on special syntax for doing things other than commands.

 - `--settings`, `-s`
   - Launch a shell to edit your settings, see the settings section below

 - `--edit [layer]`, `-e [layer]`
   - Launch a shell to edit a layer and its macros, if no layer is specified this adds to `default.json`.

 - `--new`, `-n`
   - Launch a shell to set up a device for use with Keebie, also make a udev rule to give access to the device which will require you to give a password to sudo.
   - You should run this should first upon installation.

 - `--remove [device]`, `-r [device]`
   - Launch into a shell to remove device file and udev rule, if you don't specify a device you will be prompted for one.

 - `--verbose`, `-v`
   - Makes Keebie more verbose, good for debugging.

 - `--pause`, `-P`
   - Pause keebie (if a normal instance is running).
 
 - `--resume`, `-R`
   - Resume keebie (if a normal instance is running).
 
 - `--stop`, `-S`
   - Stop keebie (if a normal instance is running).
 
 - `--install`, `-I`
   - Install default files to your home's `.config/` directory (this gets done automatically if they arn't present).

 - `-h`, `--help`
   - Print usage information.



#### Settings:

Keebie has a few settings that may be edited with `--settings` (or `-s`), here is what the settings are.

 - `multiKeyMode`
   - Decides how Keebie handles multiple held keys.
     - `combination`: How you would expect things to work, held keys are treated together.
     - `sequence`: Held keys are treated together based on the order they were held in. Its weird but might help to cram more macros onto a keyboard.

 - `forceBackground`
   - `True`: All commands should be run in the background (as opposed to waiting for them to finish before continuing).
   - `False`: Commands are left unchanged (for now).

 - `backgroundInversion`
   - `True`: Make all background commands are made to run in the foreground an vice-versa. If combined with `forceBackground` is `True` all commands run in the foreground.
   - `False`: Commands are left unchanged.

 - `loopDelay`
   - Decides how often Keebie reads devices. Higher values lead to less responsive macros, lower values lead to higher CPU usage, setting this to 0 will eat a lot of CPU time.

 - `holdThreshold`
   - How many seconds a key combination must be held without adding or removing keys in order for it to be recoreded as held.

 - `flushTimeout`
   - How many seconds to wait for more keystrokes before deciding a keystroke sequence has ended.



#### Layer syntax:

Keebie interprets some special syntax listed below

 - `layer:<layername>`
   - This will switch to the specified layer, when entering this into the `--add` shell you will be prompted to set up the layer.

 - `<script type>:<script name>`
   - This will launch different types of scripts in `~/.config/keebie/scripts/`.
   - Script types are as follows.
      - `script` will launch the named script with `bash`.
      - `py` will launch the named script with `python`.
      - `py2` will launch the named script with `python2`.
      - `py3` will launch the named script with `python3`.
      - `exec` will execute the named file without an interpreter.
