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
modules. (No need to mention that ``./ltc.py --help`` is your best friend ;) )

Simple examples:
****************

Getting the app version::

 $ sudo ./ltc.py -V  # note the capital 'V', lowercase means 'verbose'

Clearing the default lo interface::

 $ sudo ./ltc.py tc --clear

Clearing the eth0 interface, with verbose output::

 $ sudo ./ltc.py tc -c --interface eth0 -v

Note that the two commands above will also clear the ``ifb`` device used for ingress control. If you want
to clear only the upload (egress) chain, do::

 $ sudo ./ltc.py tc -c --interface eth0 --upload -v

Setting up some upload classes (dport and sport)::

 $ sudo ./ltc.py tc -c -v -u tcp:dport:6000-6080:512kbit
 $ sudo ./ltc.py tc -c -v -i eth0 -u tcp:dport:6000-6080:512kbit udp:sport:5000-5080:2mbit:3%
 $ sudo ./ltc.py tc -c -v -i eth0 -u tcp:dport:6000-6080:512kbit udp:sport:5000-5080:2mbit:3% tcp:sport:2000-2080:256kbit udp:dport:3000-3080:1mbit:3%

Setting up some disciplines as defined in 4g-sym profile of a default config file::

 $ sudo ./ltc.py profile 4g-sym

Default config file locations are defined in the module's CONFIG_PATHS constant
for now (currently being set to ``('./pyltc.profiles', '/etc/pyltc.profiles')``.


Setting up some disciplines as defined in 3g-sym profile of the given config file::

 $ sudo ./ltc.py profile 3g-sym -c /path/to/config.conf


Ingress Traffic Control
***********************

Sample command for setting up download (ingress) traffic control creating a new ifb device::

 $ sudo ./ltc.py tc -cvi eth0 --download tcp:dport:5000-5002:512kbit udp:dport:4000-4002:256kbit

The tool will create a new ifb device if none is found, or use the device with the highest
number if at least one is found.

If you want to use a specific ifb device, make sure you first create it with::

 $ sudo modprobe ifb numifbs=0
 $ sudo ip link set dev ifbX up  # substitute X with the first not-yet-existing ifb device number

and then give it to ltc.py as a value to the ``--ifbdevice`` option::

 $ sudo ./ltc.py tc -cvi eth0 --ifbdevice ifb0 --download tcp:dport:8080-8088:256kbit:7%

Seting up both upload (egress) and download (ingress) traffic control is now possible, e.g.::

 $ sudo ./ltc.py tc -cvi eth0 --download tcp:dport:8080-8088:256kbit:7% --upload tcp:sport:20000-49999:256kbit:7%

Profile configuration files
----------------------------

pyltc command line has an alternative arguments parser which expects a single positional argument which is
the name of a *profile*. *Profiles* are stored in profile configuration files with a syntax shown in the
sample below. (Comments in profile config start with either a semicolon ``';'`` or hash sign ``'#'``.)

To invoke ``ltc.py`` in that mode, you'll do something like::

 $ sudo ./ltc.py profile -c /path/to/myconf.profile 3g-sym

or if the file is on one of the standard locations, simply::

 $ sudo ./ltc.py profile 3g-sym

Sample profile config file content::

 ; Simulating outbound 4G network confitions
 [4g-sym-out]
 clear
 interface eth0 ; the primary interface
 upload tcp:dport:6000-6999:512kbit

 ; Simulating inbound 4G network conditions
 [4g-sym-in]
 clear
 verbose
 interface eth0 ; the primary interface
 download
    ; !IMPORTANT: Note the indent of the two class definitions!
    tcp:dport:6000-6999:2mbit
    tcp:dport:8000-8099:1mbit

 # Simulating outbound 3G network conditions
 [3g-sym]
 clear
 interface eth0  # the primary interface
 upload tcp:dport:8000-8080:96kbit
 download
   tcp:dport:8000-8080:96kbit
   udp:dport:5000-5080:96kbit:3%
   tcp:sport:10000-29999:256kbit:1%


Functional Testing
------------------

New functional test framework has been added with v. 0.3.0.

Prerequisites
**************

The live tests are based on ``iperf``. You will need ``iperf`` installed (NOT ``iperf3``).
On debian-based distros installing it would look like::

 $ sudo apt-get install iperf

How to run
***********

Simulation Test Suite
~~~~~~~~~~~~~~~~~~~~~~

To run the current simulation test suite, start it from the project root with::

$ sudo python3 tests/integration/sim_tests.py

The simulation suite doesn't actually run any tc commands, but it makes sure that the pyltc tool generates
a recipe of commands as expected.

Such testing is not nearly as reliable as practical live tests, but it does cover practically all of the
functionality and it runs in less than a second. This makes it a pretty convenient way to quickly and
inexpensively test changes at the highest level.

Live Test Suite
~~~~~~~~~~~~~~~~
The Live Test Suite actually installs to the kernel different traffic control setups and then tests to see of the expected shaping effects actually exist. Everything is done on the local interface ``lo``, so your external connection will not be impaired.

To run the current live test suite, start it from the project root with::

 $ sudo python3 tests/integration/live_tests.py

The suite will execute a series of iperf-based measurements. The overall time is about 6-8 min.

This is a first iteration for functional testing, improvements will be needed for sure.
This however will help keep the tool in good shape!

Important TODOs:

- Support source port setups. Currently ``iperf`` works in a way that the server always 'downloads'
  and thus only tests destination port shaping.

- Support ingress and egress shaping in the same test scenario.


Using ``pyltc`` framework from python
-------------------------------------

Using the core framework
*************************

You can leverage the pyltc core framework to create your own traffic control recipes.

Here is a simple example:

.. code:: python

 from pyltc.core.facade import TrafficControl

 TrafficControl.init()

 iface = TrafficControl.get_interface('eth0')
 iface.egress.clear()
 rootqd = iface.egress.set_root_qdisc('htb')
 qdclass = iface.egress.add_class('htb', rootqd, rate='384kbit')
 filter = iface.egress.add_filter('u32', rootqd, cond="ip protocol 17 0xff", flownode=qdclass)
 iface.egress.marshal()

The ``marshal()`` call at the end will actually configure the kernel with the given htb *root qdisc* and
an htb *qdisc class*, as well as adding the filter.

Details on what happens in the above code:

.. code:: python

 # This is the facade where you get interface objects from:
 from pyltc.core.facade import TrafficControl

 # Required: initializes the state of the framework:
 TrafficControl.init()

 # Get an object that represents the network interface 'eth0':
 iface = TrafficControl.get_interface('eth0')

 # The ITarget.clear() method builds a command that removes any previously attached
 # qdiscs to the egress root hook of the Linux kernel:
 iface.egress.clear()

 # We now attach a qdisc which is going to be the root qdisc for the egress chain:
 rootqd = iface.egress.set_root_qdisc('htb')

 # We create a qdisc class attached to the root qdisc. kw arguments are passed directly
 # to the qdisc in the form 'key1 value1 key2 value2 ...'.  It is up to you to provide
 # correct arguments (if not, then tc will return the error the kernel is going to report).
 qdclass = iface.egress.add_class('htb', rootqd, rate='384kbit')

 # We create a u32 filter with condition "ip protocol 17 0xff" attached to the root qdisc
 # and directing matching packets to the qdisc class we just created above:
 filter = iface.egress.add_filter('u32', rootqd, cond="ip protocol 17 0xff", flownode=qdclass)

 # Marshaling the commands accumulated. In the standard case, this means an attempt
 # to configure the kernel using the ``tc`` binary is done. There are other options
 # (like saving the commands to a file).
 iface.egress.marshal()

A more complex example that illustrates download (ingress) control:

.. code:: python

 from pyltc.core.facade import TrafficControl
 from pyltc.core.netdevice import DeviceManager
 from pyltc.core.tfactory import tc_file_target_factory

 TrafficControl.init()

 # The target factory used here provides a target that only prints on stdout:
 iface = TrafficControl.get_interface('eth0', target_factory=tc_file_target_factory)

 # Setting up an ifb device for the ingress control
 # (We need a convenience method to ease this setup!)
 ifbdev_name = 'ifb1'

 # This one may raise "AssertionError: Device already exists: 'ifb0'" -- try with ifb1 (or ifb2, etc.)
 ifbdev_name = DeviceManager.device_add(ifbdev_name)
 ifbdev = TrafficControl.get_interface(ifbdev_name, target_factory=tc_file_target_factory)

 iface.ingress.set_redirect(iface, ifbdev)

 # Building and marshaling the egress tc chain:
 iface.egress.clear()
 rootqd = iface.egress.set_root_qdisc('htb')
 qdclass = iface.egress.add_class('htb', rootqd, rate='384kbit')
 filter = iface.egress.add_filter('u32', rootqd, cond="ip protocol 17 0xff", flownode=qdclass)
 # With the above used target factory, this will save the commands to a file:
 iface.egress.marshal()

 # Building and marshaling the egress tc chain:
 iface.ingress.clear()
 rootqd = iface.ingress.set_root_qdisc('htb')
 qdclass = iface.ingress.add_class('htb', rootqd, rate='384kbit')
 filter = iface.ingress.add_filter('u32', rootqd, cond="ip protocol 17 0xff", flownode=qdclass)
 # With the above used target factory, this will save the commands to a file:
 iface.ingress.marshal()


Using the ``simnet`` wrapper
*****************************

Our goal with pyltc is to provide a platform that allows for easily creating, using and sharing LTC recipes
both with and without command line wrapping.

The current functionality is separated into a plugin named ``simnet`` (for "simulate network conditions").
There is a wrapping class with methods ``configure()``, ``setup()`` and ``marshal()``. The class is
in ``pyltc.plugins.simnet.SimNetPlugin``. The idea is to have an ``AbstractPlugin`` class with a well
defined interface, have ``SimNetPlugin`` to implement that and let other people implement theirs.

So here's how to use ``SimNetPlugin``: After initializing the framework builders' state with
``TrafficControl.init()``, the next thing to do it to obtain an instance of the plugin class via a call
to ``TrafficControl.get_plugin()``.

You would set common parameters like ``--clear`` or ``--verbose`` using the plugin ``configure()``. The pluign
``setup()`` method adds recipes for setting up either _upload_ or _download_ disciplines.

Finally, call the plugin ``marshal()`` method to get the setup actually eecuted against the kernel using ``tc``.

Here's a real world example:

.. code:: python

 from pyltc.core.facade import TrafficControl


 TrafficControl.init()
 simnet = TrafficControl.get_plugin('simnet', self.target_factory)
 simnet.configure(interface='lo1', ifbdevice='ifb0', clear=True)
 simnet.setup(upload=True, protocol='tcp', porttype='dport', range='8000-8080', rate='512kbit', jitter='7%')
 simnet.setup(download=True, protocol='tcp', range='all', jitter='5%')
 simnet.marshal()


For an example of how to use other target builders than the default, please refer to
``tests.plugins_tests.test_wrapping``.


Have fun! ;)
