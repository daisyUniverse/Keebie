# Keebie

More keyboards = faster hacking



#### What does it do:

Keebie is basically a small script for assigning and executing commands on a second (or third, fourth, etc., the only limit should be how many ports you have) keyboard. So you can make the spacebar search for a window and paste something. Or make the M button run a script.



#### How to set up:

Okay so this point is still a little bit uh, well. Experimental. I am not very experienced with permissions systems in Linux and this involves that so if you know a better way of doing what I'm doing, please tell me. Anyways, with that out of the way, let's go over what you need to do to set this up.

- **Find the input file of your target keyboard**
  - You can do this by running `ls /dev/input/by-id/`, and looking for a name that looks like it matches. Test to see if you've found it by running `cat /dev/input/by-id/[the-device-you-think-it-is]`( this will most likely have event and/or kbd in the name ) There will likely be more than one. keep trying that command and pressing buttons on your target keyboard. once your console starts to output garbage when you press buttons on the target keyboard, you've found it. note that down.
  - If nothing in `/dev/input/by-id/` looks like the keyboard you want (as may happen if, for example, you have a PS/2 keyboard) then try looking in `/dev/input/by-path/` or `/dev/input/` following the same procedure as above, this will require much more trial and error but is functionally the same as using `/dev/input/by-id` as `/dev/input/by-id` and `/dev/input/by-path` are populated by links to files in `/dev/input/`.
- **Give yourself permission to access that device.**
  - This is that part I wasn't sure about. I suspect that the way I did it was wrong, but I'll give you the way I did it, and the way that seems like the right way but didn't work for me.
  - What I ended up doing was `sudo chmod a+rw /dev/input/by-id/[my-device-name]`.
  - What is typically done: most inputs should belong to a group ( usually `input`, but check by using `ls -l /dev/input/by-id/[my-device-name]` ), and you should be able to add yourself to whatever group the device belongs to by doing something like `usermod -a -G input yourusername`. In my case the device didn't seem to belong to any group except for root. In other cases even when the file belongs to input and the user is added to input error have still resulted.
- **Add your device file directory to the first line of the config file**

And that should have you up and ready to roll. If when you run the script, you get an error saying something about permission denied, something has gone wrong with step 2. Good luck lmao (try running the `chmod` command if you didn't before).



#### Usage:

Just dump the files anywhere and run `keebie.py` and if everything it up and running, you should be good to go. Test your second keyboard by pressing spacebar which is bound to a test message by default. To run with more keyboards, run the script again with the `--device <dev-id>` option for however many devices you want to add. 



#### Options:

`--device <device-id>` Launches the script attatched to specified device, creating a new layer file specifically for it if it doesn't already exist. Press ESC to return to default layer.

`--add`: Launches into the script addition shell to add a command to the default layer. Instructions should be pretty straightforward. Any commands entered will be launched when the key(s) you enter are pressed, and if you try to bind the same key twice your new value will overwrite the old one. There is some special syntax that can be used in this entry that will allow for special functions:

- `layer:<layername>`: Will create a layer file in  `/layers/`, and let you bind switching to it to any key
  - ( this will create a layer with a default layout of only having `ESC` return you to the default layer, you can add to it by launching the script, switching to it, then running `python keebie.py -a` again )
- `script:<scriptname.sh (options)>`: Will launch a `< scriptname.sh (options) >` from `/scripts/`
  - ( same as `bash ~/whereveryourfolderis/scripts/scriptname.sh (options)` )
- `py:<pythonscript.py (options)>`: Will launch `< pythonscript.py (options) >` from `/scripts/` 
  - ( same as `python ~/whereveryourfolderis/scripts/pythonscript.py (options)` )
- `py2:<pythonscript.py (options)>`: Will launch `< python2script.py (options) >` from `/scripts/` 
  - ( same as `python2 ~/whereveryourfolderis/scripts/pythonscript.py (options)` )
- `py3:<pythonscript.py (options)>`: Will launch `< python3script.py (options) >` from `/scripts/` 
  - ( same as `python3 ~/whereveryourfolderis/scripts/pythonscript.py (options)` )
- `exec:<executablefile (options)>`: Will launch `< executablefile (options) >` from `/scripts/` 
  - ( same as `~/whereveryourfolderis/scripts/executablefile (options)` )

`--layers`: Lists all layer files and all of their contents.

`--edit`: Launches into a shell to delete or edit key bindings.

`--settings`: Launches into the settings editing shell to change your settings. The setting you can change, and their values, are:

- `multiKeyMode`: How multiple held keys are handled. Please note that bindings created with either setting won't always work (or work the same) when using the other setting.
  - `combination`: Multiple held keys are treated the same regardless of the order the were pressed in. This is the default and is in line with how most other programs work.
  - `sequence`: The order in which key were pressed (and held!) is considered and allows for distinct bindings on the same set of keys based on the order they were pressed.
- `forceBackground`: Whether commands should be forced to run in the background.
  - `True`: Forces commands to run in the background by appending an `&` to the command if one is not present.
  - `False`: Does not affect commands. This is the default.
- `backgroundInversion`: Whether to invert background commands to non-background commands and vice-versa. This setting is processed after `forceBackground`, this means that if both are set to `True` all commands will be forced not to run in the background.
  - `True`: Inverts whether a command runs in the background by removing `&`s from the end of a command or, if no `&` is pressent, appending an `&` to the command.
  - `False`: Does not affect commands. This is the default.

`-h` or `--help`: Shows a short help message.



#### Some tips:

**Multi-script drifting**

​Put an `&` at the end of your commands. This will effectively make any commands you run through it into their own process and keep from any long winded scripts or error messages keeping the rest of your macros from responding. You can also use the `forceBackground` setting to force all commands to run in the their own process, or use the `backgroundInversion` setting to make all commands run in their own process *unless* an `&` in at the end of the command (this is more convenient if you want seprate processes by default).
