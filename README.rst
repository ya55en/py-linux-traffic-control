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
-------------------------------

ltc.py provides a command line wrapper for the underlying Python
modules.

Getting the app version::

 # ./ltc.py -V  # note the capital 'V', lowercase means 'verbose'

Clearing the default lo interface::

 # ./ltc.py tc -c

Clearing the eth0 interface, with verbose output::

 # ./ltc.py tc --clear --interface eth0 -v

Setting up some upload classes (dport and sport)::

 # ./ltc.py tc -c -v -u tcp:dport:6000-6080:512kbit
 # ./ltc.py tc -c -v -i eth0 -u tcp:dport:6000-6080:512kbit udp:dport:5000-5080:2mbit:3%
 # ./ltc.py tc -c -v -i eth0 -u tcp:dport:6000-6080:512kbit udp:dport:5000-5080:2mbit:3% tcp:sport:2000-2080:256kbit udp:sport:3000-3080:1mbit:3%

Setting up some disciplines as defined in 4g-sym profile of a default config file::

 # ./ltc.py profile 4g-sym

Default config file locations are defined in the module's CONFIG_PATHS constant
for now (currently being set to ('./pyltc.profiles', '/etc/pyltc.profiles').


Setting up some disciplines as defined in 3g-sym profile of the given config file::

 # ./ltc.py profile 3g-sym -c /path/to/config.conf


Ingress Traffic Control
-----------------------

Sample command for setting up download (ingress) traffic control creating a new ifb device::

 # ./ltc.py tc -cvi eth0 --download tcp:dport:5000-5002:512kbit udp:dport:4000-4002:256kbit

The tool will create a new ifb device if none is found, or use the device with the highest
number if at least one is found.

If you want to use a specific ifb device, make sure you first create it with::

 # modprobe ifb numifbs=0
 # ip link set dev ifbX up  # substitute X with the first not-yet-existing ifb device number

and then give it to ltc.py as a value to the *--ingress* switch::

 # ./ltc.py tc -cvi eth0 --ifbdevice ifb0 --download tcp:dport:8080-8088:256kbit:7%

Seting up both upload (egress) and download (ingress) traffic control is now possible, e.g.::

 # ./ltc.py tc -cvi eth0 --download tcp:dport:8080-8088:256kbit:7% --upload tcp:sport:20000-49999:256kbit:7%

Comments in profile config files are denoted by semicolon ';' or hash sign '#'.

Profile configuration files
----------------------------

Sample profile config file content::

 ; Simulating outbound 4G network confitions
 [4g-sym]
 clear
 iface eth0 ; the primary interface
 upload tcp:dport:6000-6999:512kbit

 ; Simulating inbound 4G network confitions
 [4g-sym]
 clear
 iface eth0 ; the primary interface
 download
    ; !IMPORTANT: Note the indent of the two class definitions!
    tcp:dport:6000-6999:2mbit
    tcp:dport:8000-8099:1mbit

 # Simulating outbound 3G network confitions
 [3g-sym]
 clear
 iface eth0  # the primary interface
 upload tcp:dport:8000-8080:96kbit
 download
   tcp:dport:8000-8080:96kbit
   udp:dport:5000-5080:96kbit:3%
   tcp:sport:10000-29999:256kbit:1%


Functional Testing
------------------

New functional test framework has been added with v. 0.3.0.

*************
Prerequisites
*************

The live tests are based on ``iperf``. You will need iperf (NOT ``iperf3``).
On debian-based distros installing it would look like::

 $ sudo apt-get install iperf

**********
How to run
**********

To run the current test suite, root start it from the project root with::

$ sudo python3 tests/integration/live_tests.py

The suite will execute a series of iperf-based measurements. The overall time is about 6-8 min.


This is a first iteration for functional testing, improvements will be needed for sure.
This however will help keep the tool in good shape!

Important TODOs:

- Support sclass setups. Currently iperf works in a way that the server always 'downloads'
  and thus only dclass shaping is applicable.

- Support ingress and egress shaping in the same test scenario.

Have fun! ;)

Using ``pyltc`` framework from python
-------------------------------------

You can leverage the pyltc core framework to create your own traffic control recipes.

Here is a simple example::

 from pyltc.core.facade import TrafficControl

 TrafficControl.init()

 iface = TrafficControl.get_iface('eth0')
 iface.egress.clear()
 rootqd = iface.egress.add_root_qdisc('htb')
 qdclass = iface.egress.add_class('htb', rootqd, rate='384kbit')
 filter = iface.egress.add_filter('u32')
 iface.egress.marshal()

The ``marshal()`` call at the end will try to configure the kernel with the given root qdisc and a qdisc class, as well as adding the filter.

More on the framework usage coming soon!
