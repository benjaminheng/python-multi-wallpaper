# About #

This script runs in the background. It places an icon in your systray from which you can control the script. The script cycles wallpapers for your multi-monitor setup, with each monitor having a separate image. By default the script is configured for two 1080p monitors and to cycle wallpapers for the 2nd (rightmost) monitor only.

In its current state the script is quite hacky. Config options aren't elegantly laid out. Maybe I'll update it in the future, but it currently works well enough for my purposes.

# Prerequisites #

1. [PyWin32](http://sourceforge.net/projects/pywin32/)
2. [Pillow](https://pypi.python.org/pypi/Pillow/)

# Setup #

1. Install PyWin32.
2. Install Pillow. Pillow can be installed using pip with `pip install pillow`.
3. Set your desktop background's picture position to 'Tile'.
    - Right click desktop > Personalize > Desktop Background > Picture Position > Select "Tile"

# Configuration #

In the `__init__` function of the `Wallpaper` class, edit the following variables:

* monitors = \<number of monitors you have\>
* resolution = [[mon1width, mon1height], [mon2width, mon2height], etc.]

All the way at the bottom are some more user-definable variables:

* interval = \<seconds between wallpaper changes\>
* wallPath = \<absolute path to a dir where your wallpapers are stored\>
* staticWallpaper = \<absolute path to a wallpaper\>\*\*

\*\* I know having staticWallpaper is kind of pointless. Just call `Wallpaper.set_wallpaper` to set the wallpapers for both monitors before calling `Wallpaper.apply_wallpaper`. This is the first thing I'll change if I decide to update the script.

# Usage #

Ensure the script has the .pyw extension. Execute it and it'll place a icon in your systray.

Right click the icon, you have 3 options:

* Update Wallpapers: Forces the wallpapers to change.
* Delete Wallpaper #2: Deletes the current wallpaper on monitor 2 from the disk. You can easily duplicate this function for other monitors by editing the `menu_options` variable at the bottom and adding the appropriate function.
* Quit: Terminates the script.
