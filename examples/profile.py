"""
Programatically setup simnet from a config profile.

"""
from os.path import abspath, dirname, join as pjoin
MY_CONFIG_FILE = pjoin(abspath(dirname(__file__)), 'my.profile')

from pyltc.core.facade import TrafficControl

# Instead of the default target builder, we will use one that only prints commands on stdout:
from pyltc.core.tfactory import printing_target_factory


TrafficControl.init()
simnet = TrafficControl.get_plugin('simnet', target_factory=printing_target_factory)
simnet.configure(clear=True, verbose=True, ifbdevice='ifb2')  # as usual, first set general options
simnet.load_profile('4g-upload', config_file=MY_CONFIG_FILE)  # configure using the profile.
simnet.marshal()
