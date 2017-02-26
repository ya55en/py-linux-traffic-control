(This file can be viewed using the online ReST editor at https://livesphinx.herokuapp.com/.)

PyLTC
======

Python-based Linux Traffic Control setup utility.



Installation
-------------

!OBSOLETE! Installing using pip is underway but not yet in place. Your patience appreciated ;)

Check out this repository on your linux machine where you want to do traffic
control.

Please make sure you have root access while using the tool.


Examples for command line usage
--------------------------------

ltc.py provides a command line wrapper for the underlying Python
modules. (No need to mention that ``./ltc.py --help`` is your best friend ;) )

Some simple examples:
*********************

Getting the tool version::

 $ ./ltc.py -V  # note the capital 'V', lowercase '-v' means 'verbose'

Clearing the default ``lo`` interface::

 $ sudo ./ltc.py simnet --clear

Clearing the eth0 interface, with verbose output::

 $ sudo ./ltc.py simnet -c --interface eth0 -v

Note that the two commands above will also clear the ``ifb`` device used for ingress control.
If you want to clear only the upload (egress) chain, do::

 $ sudo ./ltc.py simnet -c --interface eth0 --upload -v

Setting up some upload classes (dport and sport)::

 $ sudo ./ltc.py simnet -c -v -u tcp:dport:6000-6080:512kbit
 $ sudo ./ltc.py simnet -c -v -i eth0 -u tcp:dport:6000-6080:512kbit udp:sport:5000-5080:2mbit:3%
 $ sudo ./ltc.py simnet -c -v -i eth0 -u tcp:dport:6000-6080:512kbit udp:sport:5000-5080:2mbit:3% tcp:sport:2000-2080:256kbit udp:dport:3000-3080:1mbit:3%


Explaining the class specifiers
*******************************

Traffic control class specifiers are the (zero or more) values of the ``--download`` and ``--upload`` command line switches. They follow this format:

 ``PROTOCOL:PORTTYPE:RANGE:RATE:JITTER``

For example:

 ``tcp:dport:16000-24000:512kbit:5%%``

- ``PROTOCOL``, ``PORTTYPE`` and ``RANGE`` are required.

- ``PORTTYPE`` is one of ``sport``, ``dport``, ``lport``, ``rport``, their meaning explained:

 - ``sport`` and ``dport`` mean *source-port* and *destination-port*, resp.
 - ``lport`` and ``rport`` mean *local-port* and *remote-port*, which
   should be used as follows: use ``lport`` when you know the port (or port range) of traffic at the machine being configured for traffic control; use ``rport`` when you know the port (or port range) of traffic at the remote machine handling the other side of the traffic connection.

 For example, if about to shaping download traffic and knowing the port of the server we download from, then this will be an ``rport`` case; if uploading to a remote server and knowing its port, then again this is ``rport`` case (first one translates to ``sport`` and the second to ``dport`` but you don't need to bother thinking about this).


- ``RANGE`` is a dash-delimited range of ports MINPORT-MAXPORT (inclusive),
a single port or the keyword ``all``.

- ``RATE`` is the amount of data to limit the class to -- see the ``RATE``
  section of ``man tc`` for specific details on all the available options.

Some examples:

- ``--upload tcp:rport:8000-8099:512kbit:2%%`` -- shape *upload* (egress) *tcp* traffic traveling to *remote* (destination) port range *8000-8099* to *512kbit* and introduce artificial loss of *2%*.

- ``--download udp:rport:10000-49999:2mbit`` -- shape *download* (ingress) *udp* traffic traveling to *local* (destination) port range *10000-49999* to *2mbit*.

- ``--upload udp:rport:all:1mbit`` -- shape all *upload* egress *udp* traffic traveling to *local* (destination) to *1 Mbit/sec*.

You can combine several such class specifiers into a single command line, like this::

 sudo ./ltc.py simnet -c -v -i eth0 --upload tcp:dport:6000-6080:512kbit udp:sport:5000-5080:2mbit:3% --download ucp:lport:5000:50000:3mbit tcp:rport:80:9%

Note that if you specify an ``all`` ports class for some of the two protocols and a given direction, it doesn't make sense to specify any other class for that protocol and direction.


Download/Ingress Traffic Control
*********************************

Sample command for setting up download (ingress) traffic control creating a new ifb device::

 $ sudo ./ltc.py tc -cvi eth0 --download tcp:dport:5000-5002:512kbit udp:dport:4000-4002:256kbit

The tool will create a new ifb device if none is found, or use the device with the highest
number if at least one is found.

If you want to use a specific ifb device, just pass it as an argument to the ``--ifbdevice`` switch::

and then give it to ``ltc.py`` as a value to the ``--ifbdevice`` option::

 $ sudo ./ltc.py tc -cvi eth0 --ifbdevice ifb0 --download tcp:dport:8080-8088:256kbit:7%

Pyltc creates that device if not existing yet, executing for you under the hood something like::

 $ sudo modprobe ifb numifbs=0
 $ sudo ip link set dev ifbX up  # substitute X with the first not-yet-existing ifb device number

Setting up both upload (egress) and download (ingress) traffic control with the same command is now possible, e.g.::

 $ sudo ./ltc.py tc -cvi eth0 --download tcp:dport:8080-8088:256kbit:7% --upload tcp:sport:20000-49999:256kbit:7%

**Important notes about config files:**

  - All classes you want to set up have to appear in one single command line. (If too long, then
    consider to keep them in a profile configuration -- see next section.)

  - Commands that configure network devices and/or the kernel traffic control chains have to be
    executed with root access level.


Profile configuration files
----------------------------

pyltc command line has an alternative arguments parser which expects a single positional argument which is
the name of a *profile*. *Profiles* are stored in profile configuration files with a syntax shown in the
sample below. (Comments in profile config start with either a semicolon ``';'`` or hash sign ``'#'``.)

Default config file locations are defined in the module's ``CONFIG_PATHS`` constant
for now (currently being set to ``('./pyltc.profiles', '/etc/pyltc.profiles')``.

To invoke ``ltc.py`` in that mode, you'll do something like::

 $ sudo ./ltc.py profile -c /path/to/myconf.profile 3g-sym

or if the file is on one of the default locations, simply::

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

**Important notes about config files:**

  - Leading white space is significant:

    * section header lines and other normal lines *must NOT* have any leading whitespace;
    * lines that contain several traffic control class definitions (and are thus quite long)
      can be broken into several lines, but now leading whitespace is *mandatory* for all
      sub-lines.

  - Comments can appear on a dedicated line as well as after significant content.

  - Sections span up to the beginning of a next section or to the EOF.

  - There's no default section - significant lines before the first sections are treated as
    wrong syntax.

Functional Testing
------------------

New functional test framework has been added with v. 0.3.0.

Prerequisites
**************

The live tests are based on ``iperf``. You will need ``iperf`` installed (NOT ``iperf3``).
On debian-based distros installing it would look like::

 $ sudo apt-get install iperf

How to run the tests
********************

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

Note: most of the example code below can also be found as python modules located at the ``./examples/`` folder.

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

The ``marshal()`` call at the end will actually configure the kernel with the given htb *root qdisc*
and htb *qdisc class*, as well as adding the filter.

Details on what happens in the above code:

.. code:: python

 # This is the facade where you get interface objects from:
 from pyltc.core.facade import TrafficControl

 # We will replace the default target builder with one that only prints commands on stdout:
 from pyltc.core.tfactory import printing_target_factory

 # Required: initializes the state of the framework:
 TrafficControl.init()

 # We get an object that represents the local network interface ('lo')
 # (for real use you'll want something like 'eth0'):
 iface = TrafficControl.get_interface('lo', target_factory=printing_target_factory)

 # The ITarget.clear() method builds a command that removes any previously attached
 # qdiscs to the egress root hook of the Linux kernel.
 iface.egress.clear()

 # We now attach a qdisc which is going to be the root qdisc for the egress chain:
 rootqd = iface.egress.set_root_qdisc('htb')

 # We create a qdisc class attached to the root qdisc. kw arguments are passed
 # direvtly to the qdisc in the form 'key1 value1 key2 value2'.
 qdclass = iface.egress.add_class('htb', rootqd, rate='384kbit')

 # We create a u32 filter with condition "ip protocol 17 0xff" attached to the root qdisc
 # and directing mathching packets to the qdisc class we just created above:
 filter = iface.egress.add_filter('u32', rootqd, cond="ip protocol 17 0xff", flownode=qdclass)

 # Marshalling the commands built for our case will simply dump them on stdout, as the
 # factory define above -- ``tc_file_target_factory`` -- does only that.
 iface.egress.marshal()

 # Use pyltc.core.tfactory.default_target_factory to configure the framework to use
 # TcCommandTarget, which will during ``marshal()`` actually execute those commands.
 # Note that you need root privileges to configure the kernel.

A more complex example that illustrates download (ingress) control:

.. code:: python

 from pyltc.core.facade import TrafficControl
 from pyltc.core.netdevice import DeviceManager

 # Use any factory that suits your goal or omit this to use the default command-executing tc factory:
 from pyltc.core.tfactory import printing_target_factory

 TrafficControl.init()

 # This target factory provides a target that only prints on stdout:
 iface = TrafficControl.get_interface('lo', target_factory=printing_target_factory)

 # Setting up an ifb device for the ingress control
 # (We need a convenience method to ease this setup!)
 ifbdev_name = 'ifb0'

 # If this one raises "Device already exists: 'ifb0'", then try with 'ifb1', 'ifb2', etc.
 DeviceManager.ensure_device(ifbdev_name)
 ifbdev = TrafficControl.get_interface(ifbdev_name, target_factory=printing_target_factory)

 iface.ingress.set_redirect(iface, ifbdev)

 # Configuring and marshal the egress tc chain:
 iface.egress.clear()
 rootqd = iface.egress.set_root_qdisc('htb')
 qdclass = iface.egress.add_class('htb', rootqd, rate='384kbit')
 filter = iface.egress.add_filter('u32', rootqd, cond="ip protocol 17 0xff", flownode=qdclass)
 iface.egress.marshal()

 # Configuring and marshal the egress tc chain:
 iface.ingress.clear()
 rootqd = iface.ingress.set_root_qdisc('htb')
 qdclass = iface.ingress.add_class('htb', rootqd, rate='384kbit')
 filter = iface.ingress.add_filter('u32', rootqd, cond="ip protocol 17 0xff", flownode=qdclass)
 iface.ingress.marshal()


Using the ``simnet`` wrapper
*****************************

Our goal with ``pyltc`` is to provide a platform allowing for easily create, use and share LTC
recipes both with command line interface and programmatically.

The current functionality is separated into a plugin named ``simnet`` (for "*sim*-ulate *net*-work").
There is a wrapping class with methods ``configure()``, ``setup()`` and ``marshal()``. The class is
``pyltc.plugins.simnet.SimNetPlugin``. The idea is to some day have an ``AbstractPlugin`` class with
a well defined interface, have ``SimNetPlugin`` implement that and let other people implement their
own plugins.

So here's how to use ``SimNetPlugin``: after initializing the framework builders' state with
``TrafficControl.init()``, the next thing to do it to obtain an instance of the plugin class via
a call to ``TrafficControl.get_plugin()``.

You would set common parameters like ``--clear`` or ``--verbose`` using the plugin ``configure()``
method. The plugin ``setup()`` method adds recipes for setting up either ``upload`` or ``download``
disciplines.

Finally, call the plugin ``marshal()`` method to get the setup actually executed against the kernel
using ``tc``.

Here's an example of using the plugin wrapper:

.. code:: python

 from pyltc.core.facade import TrafficControl

 TrafficControl.init()
 simnet = TrafficControl.get_plugin('simnet')
 simnet.configure(interface='lo', ifbdevice='ifb0', clear=True)
 simnet.setup(upload=True, protocol='tcp', porttype='dport', range='8000-8080', rate='512kbit', jitter='7%')
 simnet.setup(download=True, protocol='tcp', range='all', jitter='5%')
 simnet.marshal()


For an example of how to use other target builders than the default, please refer to
``tests.plugins_tests.test_wrapping``.

**Load a config file profile:**

You can programmatically load a profile from a config file using the ``load_profile()`` simnet method like this:

.. code:: python

 from os.path import abspath, dirname, join as pjoin
 from pyltc.core.facade import TrafficControl

 TrafficControl.init()
 # No printing factory; this time marshal() will attempt to configure the kernel:
 simnet = TrafficControl.get_plugin('simnet')
 simnet.configure(clear=True, verbose=True, ifbdevice='ifb2')  # as usual, first set general options
 simnet.load_profile('4g-sym-egress', config_file='/path/to/my.profile')  # configure using the profile.
 simnet.marshal()


Have fun! ;)
