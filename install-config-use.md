# Keebie Installation, Configuration and Use on Ubuntu/Mint

Keebie allows you to map keys to actions, with the keys being keyboard-specific.
Keebie is written in python3 and heavily relies on
[python-evdev](https://python-evdev.readthedocs.io/en/latest/).

Note:

* you may need to setup custom permissions on your keyboard device;
* keebie probably does NOT work with wayland.

## Installation

I just cloned the repo:
```sh
gh repo clone asokolsky/Keebie
```

Install the prerequisites:
```sh
sudo apt install python3 python3-evdev inotify-tools
```

Run `make install` while in the repo directory. This creates
`/usr/share/keebie`.

To verify installation:

```
> which keebie
/usr/bin/keebie
> keebie -h
usage: keebie [-h] [--layers] [--detect] [--print-keys] [--add [layer]] [--settings]
              [--edit [layer]] [--new] [--remove [device]] [--pause] [--resume] [--stop]
              [--install] [--verbose] [--quiet]

options:
  -h, --help            show this help message and exit
  --layers, -l          Show saved layer files
  --detect, -d          Detect keyboard device file
  --print-keys, -k      Print a series of keystrokes
  --add [layer], -a [layer]
                        Adds new macros to the selected layer file (or default layer if
                        unspecified)
  --settings, -s        Edits settings file
  --edit [layer], -e [layer]
                        Edits specified layer file (or default layer if unspecified)
  --new, -n             Add a new device file
  --remove [device], -r [device]
                        Remove specified device, if no device is specified you will be prompted
  --pause, -P           Pause a running keebie instance that is processing macros
  --resume, -R          Resume a keebie instance paused by --pause
  --stop, -S            Stop a running keebie instance that is processing macros
  --install, -I         Install default files to your home's .config/ directory
  --verbose, -v         Print extra debugging information
  --quiet, -q           Print less
 ```

## Configuration

For every Keebie user:
```sh
keebie --install
```

This creates:

* `~/.config/keebie/settings.json`:
```json
{
  "multiKeyMode": "combination",
  "forceBackground": false,
  "backgroundInversion": false,
  "loopDelay": 0.1,
  "holdThreshold": 0.5,
  "flushTimeout": 0.33
}
```
* empty directory `.config/keebie/devices/`
* `~/.config/keebie/layers/default.json`
```json
{
  "leds": [],
  "vars": {
    "greeting": "Hello World"
  },
  "KEY_SPACE": "echo '%greeting%!'",
  "KEY_ESC": "layer:default"
 }
```
* empty directory `.config/keebie/scripts/`

By now you are ready to start using keebie and customize your keyboards.

## Using Keebie

Keebie works with devices (keyboards) and layers (key mappings).

### Device Operations

I connected (in advance) a small numpad usb keyboard and plan to customize its
key mappings.  I refer to this peripheral as a "small keyboard" or a
"numpad keyboard".

#### Detect Keyboard

To detect the keyboard:
```sh
keebie --detect
```
When I press a key on my small keyboard I get `/dev/input//event4`.

Alternatively, identify the USB device for your USB keyboard:

```
> lsusb
Bus 001 Device 001: ID 1d6b:0002 Linux Foundation 2.0 root hub
Bus 001 Device 002: ID c0f4:08f5 Usb KeyBoard Usb KeyBoard
Bus 001 Device 003: ID 046d:c52b Logitech, Inc. Unifying Receiver
Bus 001 Device 004: ID 04f2:b604 Chicony Electronics Co., Ltd Integrated Camera (1280x720@30)
Bus 001 Device 005: ID 06cb:009a Synaptics, Inc. Metallica MIS Touch Fingerprint Reader
Bus 001 Device 006: ID 8087:0aaa Intel Corp. Bluetooth 9460/9560 Jefferson Peak (JfP)
Bus 002 Device 001: ID 1d6b:0003 Linux Foundation 3.0 root hub
```
My keyboard is `Bus 001 Device 002: ID c0f4:08f5 Usb KeyBoard Usb KeyBoard`.
Then:
```sh
sudo python3 -m evdev.evtest
```
This will give you an idea of which event device is related to your keyboard.

#### Add a Keyboard

To add a new keyboard:
```sh
keebie --new
```
Here is my attempt to add my small keyboard which I call `numpad` to keebie:
```
alex@duo | ~/Projects/Keebie | asokolsky-dev ± > keebie --new
Welcome to Keebie
Setting up device
Please provide a name for for this devices initial layer (non-existent layers will be created, default.json by default): numpad
Gaining sudo to watch root owned files, sudo may prompt you for a password
have sudo
Please press a key on the desired input device...
7
A udev rule will be made next, sudo may prompt you for a password. Press enter to continue...
```

This created `~/.config/keebie/devices/event4.json`:
```json
{
  "initial_layer": "numpad",
  "event": "event4",
  "udev_tests": [
    "KERNEL==\"event4\""
  ],
  "udev_rule": "85-keebie-event4.rules"
}
```
and `~/.config/keebie/layers/numpad`:
```json
{
  "leds": [],
  "vars": {
    "greeting": "Hello World"
  },
  "KEY_SPACE": "echo '%greeting%!'",
  "KEY_ESC": "layer:default"
 }
```
and `/etc/udev/rules.d/85-keebie-event4.rules`:
```
UBSYSTEM=="input", KERNEL=="event4", MODE="0666", ENV{SYSTEMD_WANTS}="keebie.service"  TAG+="systemd"
```

#### Remove the Keyboard

To remove the keyboard:
```sh
keebie --remove
```

### Device Permissions

When you run keebie as a user, you can get an error:
```
PermissionError: [Errno 13] Permission denied: '/dev/input/event19'
```
In this case you may need to either:

* add user to the group `input` - preferred way of solving this problem,
requires reboot;
* or change permissions on the device - this change will only be effective for
the duration of the current session.

To add user to the group `input` and reboot:
```sh
sudo adduser $USER input
sudo reboot
```
To change permissions on the device for the user and group:
```sh
sudo chmod u+r /dev/input/eventX
sudo chmod g+r /dev/input/eventX
```

### Keebie Layer - Key Mappings

A layer in keebie is just a JSON file which maps keys to actions.

#### Keebie Layer Key

Key here is a string which starts with `KEY_` - see
`/usr/include/linux/input-event-codes.h` for possible values of keycodes.

To identify the symbol associate with the key of the interest:

* Run `sudo showkey --keycodes` to identify the keycode.
* Use `/usr/include/linux/input-event-codes.h` to identify the symbol
associated with the keycode from the previous step.

Alternatively run `sudo python3 -m evdev.evtest`, select your device and press
the key(s) of interest.

More on keyboard [scancodes and keycodes]((https://wiki.archlinux.org/title/Keyboard_input#Identifying_scancodes)).

My small keyboard with numlock ON sends the following keycodes:

Key|Keycode|Keycode Symbol
---|--------|----
`NumLock`|69|KEY_NUMLOCK
`/`|98|KEY_KPSLASH
`*`|55|KEY_KPASTERISK
`Backspace`|14|KEY_BACKSPACE
`7`|71|KEY_KP7
`8`|72|KEY_KP8
`9`|73|KEY_KP9
`-`|74|KEY_KPMINUS
`4`|75|KEY_KP4
`5`|76|KEY_KP5
`6`|77|KEY_KP6
`+`|78|KEY_KPPLUS
`1`|79|KEY_KP1
`2`|80|KEY_KP2
`3`|81|KEY_KP3
`Enter|96|`KEY_KPENTER
`0`|82|KEY_KP0
`.`|83|KEY_KPDOT

#### Keebie Action

Action can be:

* a shell command, e.g. `reboot` or `konsole &` or
[xdotool](https://github.com/jordansissel/xdotool) to simulate the keyboard
input;
* a shell script, e.g. `script:sync.sh`
* a python file, e.g. `py:foobar.py`;
* a reference to the new layer to assume, e.g. `layer:obs`

## Example Use

I decided to add file extension to layers to take advantage of syntax
highlighting, hence my `~/.config/keebie/devices/event4.json`:
```json
{
  "initial_layer": "numpad.json",
  "event": "event4",
  "udev_tests": [
    "KERNEL==\"event4\""
  ],
  "udev_rule": "85-keebie-event4.rules"
}
```

I plan to have the following layers:

* `numpad` - default productivity tasks;
* `obs` - obs tasks, get there by pressing `KEY_KPSLASH`, get back to `numpad`
by pressing `KEY_BACKSPACE`;
* `test` - more tasks, get there by pressing `KEY_KPASTERISK`, get back to
`numpad` by pressing `KEY_BACKSPACE`;

```
python3 keebie.py --layers
Welcome to Keebie
Available Layers:

test.json{
  "leds": [],
  "vars": {
    "greeting": "test"
  },
  "KEY_KPSLASH": "layer:obs",
  "KEY_KPASTERISK": "layer:test",
  "KEY_BACKSPACE": "layer:numpad",
  "KEY_KP0": "echo '%greeting%!'",
  "KEY_KP1": "echo '%greeting%!'",
}

numpad.json{
  "leds": [],
  "vars": {},
  "KEY_KPSLASH": "layer:obs",
  "KEY_KPASTERISK": "layer:test",
  "KEY_BACKSPACE": "layer:numpad",
  "KEY_KPMINUS": "/usr/bin/wpctl set-volume @DEFAULT_AUDIO_SINK@ 5%%-",
  "KEY_KPMINUS-KEY_KPMINUS": "/usr/bin/wpctl set-volume @DEFAULT_AUDIO_SINK@ 10%%-",
  "KEY_KPMINUS-KEY_KPMINUS-KEY_KPMINUS": "/usr/bin/wpctl set-mute @DEFAULT_AUDIO_SINK@ 1",
  "KEY_KPPLUS": "/usr/bin/wpctl set-volume -l 1.5 @DEFAULT_AUDIO_SINK@ 5%%+",
  "KEY_KPPLUS-KEY_KPPLUS": "/usr/bin/wpctl set-volume -l 1.5 @DEFAULT_AUDIO_SINK@ 10%%+",
  "KEY_KPPLUS-KEY_KPPLUS-KEY_KPPLUS": "/usr/bin/wpctl set-mute @DEFAULT_AUDIO_SINK@ 0",
  "KEY_KP0": "",
  "KEY_KP1": "",
  "KEY_KP2": "",
  "KEY_KP3": "",
  "KEY_KP4": "/usr/bin/cvlc /usr/share/sounds/freedesktop/stereo/audio-channel-front-left.oga vlc://quit",
  "KEY_KP5": "/usr/bin/cvlc /usr/share/sounds/freedesktop/stereo/audio-channel-front-center.oga vlc://quit",
  "KEY_KP6": "/usr/bin/cvlc /usr/share/sounds/freedesktop/stereo/audio-channel-front-right.oga vlc://quit",
  "KEY_KP7": "'",
  "KEY_KP8": "",
  "KEY_KP9": ""
}

default.json{
  "leds": [],
  "vars": {
    "greeting": "Hello World"
  },
  "KEY_SPACE": "echo '%greeting%!'",
  "KEY_ESC": "layer:default"
 }

obs.json{
  "leds": [],
  "vars": {
    "OBSWS": "obsws://127.0.0.1:4455/password"
  },
  "KEY_KPSLASH": "layer:obs",
  "KEY_KPASTERISK": "layer:test",
  "KEY_BACKSPACE": "layer:numpad",
  "KEY_KP0": "/usr/local/bin/obs-cmd -w %OBSWS% scene switch 'Scene'",
  "KEY_KPENTER": "/usr/local/bin/obs-cmd -w %OBSWS% scene switch 'Scene 2'"
}
```

Note:

* the use of `KEY_KPMINUS` / `KEY_KPPLUS` to control volume - see
[my notes on Mint](https://asokolsky.github.io/linux/mint.html#volume-control-cli)
* use of double and triple key clicks to invoke various commands - double click
speeds up volume adjustment, triple clicks invokes mute/unmute.
* use of [obs-cmd](https://github.com/grigio/obs-cmd) to switch OBS scenes -
see [my notes on obs-cmd](https://asokolsky.github.io/apps/obs/obs-cmd.html).

## TODO

Document use of:

* LEDs in the layer file
* translate one key sequence into another key sequence - is it even possible?
