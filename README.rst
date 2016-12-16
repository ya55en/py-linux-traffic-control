PyLTC
======

Python-based Linux Traffic Control setup utility.


Installation
-------------

!OBSOLETE! Installing using pip is underway but not yet in place. Your patience appreciated ;)

Check out this repository on your linux machine where you want to do traffic
control.

Please make sure you have root access while using the tool.


Examples of command line usage:
-------------------

```ltc.py``` provides a command line wrapper for the underlying Python
modules.

Getting the app version::

 # ./ltc.py -V  # note the capital 'V', lowercase means 'verbose'

Clearing the default lo interface::

 # ./ltc.py tc -c

Clearing the eth0 interface, with verbose output::

 # ./ltc.py tc --clear --iface eth0 -v

Setting up some dport classes::

 # ./ltc.py tc -c -v --dclass tcp:6000-6080:512kbit
 # ./ltc.py tc -c -v -i eth0 -dc tcp:6000-6080:512kbit -dc udp:5000-5080:2mbit:3%
 # ./ltc.py tc -c -v -i eth0 -dc tcp:6000-6080:512kbit -dc udp:5000-5080:2mbit:3% -sc tcp:2000-2080:256kbit -sc udp:3000-3080:1mbit:3%

Setting up some disciplines as defined in 4g-sym profile of a default config file::

 # ./ltc.py profile 4g-sym

Default config file locations are defined in the module's CONFIG_PATHS constant
for now (currently being set to ('./pyltc.profiles', '/etc/pyltc.profiles').


Setting up some disciplines as defined in 3g-sym profile of the given config file::

 # ./ltc.py profile 3g-sym -c /path/to/config.conf


Ingress Traffic Control
-------------------

Sample command for setting up ingress traffic control creating a new ifb device::

 # ./ltc.py tc -cvi eth0 --ingress -dc tcp:5000-5002:512kbit -dc udp:4000-4002:256kbit

The tool will create a new ifb device if none is found, or use the device with the highest
number if at least one is found.

If you want to use a specific ifb device, make sure you first create it with::

 # modprobe ifb numifbs=0
 # ip link set dev ifbX up  # substitute X with the first not-yet-existing ifb device number

and then give it to ltc.py as a value to the `--ingress` switch::

 # ./ltc.py tc -cvi eth0 --ingress ifb0 -dc tcp:8080-8088:256kbit:7%

Note that you cannot setup egress and ingress controll within the same command,
or within the same profile. (We may think on supporting this in the future,
though.)


Example config file content::

 ----cut here-----------------
 [4g-sym]
 clear
 iface eth0
 dclass tcp:6000-6999:512kbit
 
 [3g-sym]
 clear
 iface eth0
 dclass tcp:8000-8080:96kbit
 dclass udp:5000-5080:96kbit:3%
 sclass tcp:10000-29999:256kbit:1%
 ----cut here-----------------

Have fun! ;)
