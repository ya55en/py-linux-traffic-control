PyLTC
-------

Python-based Linux Traffic Control setup utility.


Installation
-------------

!OBSOLETE! Installing using pip is underway but not yet in place. Your patience appreciated ;)

Just copy the pyltc.py module to a known directory on your linux machine where
you want to do traffic control.

After copying the module, please make sure:

  (a) you have root access while using the tool;
  (b) you make it executable for the below commands to work::

         # chmod +x ./pyltc.py


Examples of usage:
-------------------

Getting the app version::

 # ./pyltc.py -V  # note the capital 'V', lowercase means 'verbose'

Clearing the default lo interface::

 # ./pyltc.py tc -c

Clearing the eth0 interface, with verbose output::

 # ./pyltc.py tc --clear --iface eth0 -v

Setting up some dport classes::

 # ./pyltc.py tc -c -v --dclass tcp:6000-6080:512kbit
 # ./pyltc.py tc -c -v -i eth0 -dc tcp:6000-6080:512kbit -dc udp:5000-5080:2mbit:3%
 # ./pyltc.py tc -c -v -i eth0 -dc tcp:6000-6080:512kbit -dc udp:5000-5080:2mbit:3% -sc tcp:2000-2080:256kbit -sc udp:3000-3080:1mbit:3%

Setting up some disciplines as defined in 4g-sym profile of a default config file::

 # ./pyltc.py profile 4g-sym

Default config file locations are defined in the module's CONFIG_PATHS constant
for now (currently being set to ('./pyltc.conf', '/etc/pyltc.conf').


Setting up some disciplines as defined in 3g-sym profile of the given config file::

 # ./pyltc.py profile 3g-sym -c /path/to/config.conf


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
