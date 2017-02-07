
py-linux-traffic-control changes
=================================

v. 0.4.6 (2017-01-24)
--------------------------
- Added support for lport/rport port type;
- Added support for loading a simnet profile programmatically;
- Changed default plugin name from ``tc`` to ``simnet``;
- Provided working examples on using the framework (within the ./examples/ directory);
- Simplified the argument parsing code, including the ifb setup logic.


v. 0.4.4 (2017-01-24)
--------------------------
- Refactored the core and the ``thehunmonkgroup`` plugin into a more loosly
  coupled system;
- Renamed the ``thehunmonkgroup`` into ``simnet`` and provided a wrapper class
  for easy setup of rate+jitter recipes programmatically.


v. 0.4.2 (2017-01-14)
--------------------------
- Significant refactoring of the core framework.
- New way to describe tc classes using --download (for ingress) and --upload (for egress)
  command line arguments. They also accept multiple tokens each defining a separate class.
- Both upload and download setups are now supported within the same command line.
- New names for other arguments.
- Improved handling of ifb (and any other network) devices using a new DeviceManager.
- Improved integration test suite with richer simulation tests that can run w/o root privileges.
- Updated README with simple examples of using the framework from python.


v. 0.3.1 (2016-12-26)
--------------------------
- Ingress filtering reverted to single ematch filter (vs. using N single-port u32 filters).
- Imrpovements of the functional testing framework.


v. 0.3.0 (2016-12-23)
--------------------------
- Functional testing framework introduced based on iperf.
- Supporting 'all' keyword for port ranges in sclass/dclass option values,
  which is interpreted as applying shaping to all ports for that protocol
  (tcp or udp). 


v. 0.2.2 (2016-12-16)
--------------------------

- Comments are supported by the profile confing parser.


v. 0.2.1 (2016-12-16)
--------------------------

- The monolithic pyltc.py has been broken to a set of sub-modules.
- Added support for a single port in a dclass/sclass definition.


v. 0.1.5 (2016-12-12)
--------------------------

Q & D, proof-of-concept support for ingress traffic control.


v. 0.1.4 (YD, 2016-12-09)
--------------------------

This is the first version considered for real usage.

What's new:

* the "clear" option now works even if no --dcalss or --sclass given;

* both udp and tcp protocols are supported, thus the new spec token looks like this::

  PROTOCOL:RANGE:RATE:JITTER

  For example::

  tcp:8000-8080:512kbit:5%

  As before, RATE or JITTER may be missing, but at least one of the two must be there.

* Initial version of config file profiles support is implemented.
  We first used the standard .ini parser but it does not support multiple options
  with the same name (e.g. repeated dclass or sclass) so we wrote our own, which
  took time, as I explained yesterday.


The command line now allows EITHER using a profile from a config file, OR giving the
arguments to the parser. The first is triggered by a sub-command 'profile', the
second with sub-comand 'tc'. This all may change if we come up with better names and/or
better schemes.
