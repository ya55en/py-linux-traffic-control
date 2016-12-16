PyLTC
======

Python-based Linux Traffic Control setup utility.


Installation
-------------

!OBSOLETE! Installing using pip is underway but not yet in place. Your patience appreciated ;)

Check out this repository on your linux machine where you want to do traffic
control.

Please make sure:

  (a) you have root access while using the tool;


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

(NEW!) Sample command for setting up ingress traffic control::

 # ./ltc.py tc -cvi eth0 --ingress setup -dc tcp:5000-5002:512kbit -dc udp:4000-4002:256kbit

Use 'setup' as an argument to --ingress the first time. For subsequent calls, use 'ifb0'::

 # ./ltc.py tc -cvi eth0 --ingress ifb0 -dc tcp:8080-8088:256kbit:7%
 
This is because ifb0 has been created for you the first time, and if you still keep using 'setup',
another ifb device will be created --  ifb1, then ifb2, etc. etc. Giving ifb0 to --ingress causes
the tool to reuse ifb0.

Note that you cannot setup egress and ingress controll at the same time. (We may think on
supporting this in the future, though.)


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
