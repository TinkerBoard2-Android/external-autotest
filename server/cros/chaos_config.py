# Copyright (c) 2012 The Chromium OS Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import ConfigParser
import logging
import os
import time
import xmlrpclib

from autotest_lib.site_utils.rpm_control_system import rpm_client

class APPowerException(Exception):
    pass


class ChaosAP(object):
    """ An instance of an ap defined in the chaos config file.

    This object is a wrapper that can be used to retrieve information
    about an AP in the chaos lab, and control its power.
    """
    # Keys used in the config file.
    CONF_SSID = 'ssid'
    CONF_BRAND = 'brand'
    CONF_MODEL = 'model'
    CONF_WAN_MAC = 'wan mac'
    CONF_WAN_HOST = 'wan_hostname'
    CONF_BSS = 'bss'
    CONF_BANDWIDTH = 'bandwidth'
    CONF_SECURITY = 'security'
    CONF_PSK = 'psk'
    CONF_FREQUENCY = 'frequency'


    def __init__(self, bss, config):
        self.bss = bss
        self.ap_config = config


    def get_ssid(self):
        return self.ap_config.get(self.bss, self.CONF_SSID)


    def get_brand(self):
        return self.ap_config.get(self.bss, self.CONF_BRAND)


    def get_model(self):
        return self.ap_config.get(self.bss, self.CONF_MODEL)


    def get_wan_mac(self):
        return self.ap_config.get(self.bss, self.CONF_WAN_HOST)


    def get_wan_host(self):
        return self.ap_config.get(self.bss, self.CONF_WAN_HOST)


    def get_bss(self):
        return self.ap_config.get(self.bss, self.CONF_BSS)


    def get_bandwidth(self):
        return self.ap_config.get(self.bss, self.CONF_BANDWIDTH)


    def get_security(self):
        return self.ap_config.get(self.bss, self.CONF_SECURITY)


    def get_psk(self):
        return self.ap_config.get(self.bss, self.CONF_PSK)


    def get_frequency(self):
        return self.ap_config.get(self.bss, self.CONF_FREQUENCY)


    def power_off(self):
        rpm_client.set_power(self.get_wan_host(), 'OFF')


    def power_on(self):
        rpm_client.set_power(self.get_wan_host(), 'ON')

        # Hard coded timer for now to wait for the AP to come alive
        # before trying to use it.  We need scanning code
        # to scan until the AP becomes available (crosbug.com/36710).
        time.sleep(60)


class ChaosAPList(object):
    """ Object containing information about all AP's in the chaos lab. """

    AP_CONFIG_FILE = 'wifi_interop_ap_list.conf'


    def __init__(self):
        self.ap_config = ConfigParser.RawConfigParser()
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            self.AP_CONFIG_FILE)

        logging.debug('Reading config from "%s"', path)
        self.ap_config.read(path)


    def get_ap_by_bss(self, bss):
        return ChaosAP(bss, self.ap_config)


    def next(self):
        bss = self._iterptr.next()
        return self.get_ap_by_bss(bss)


    def __iter__(self):
        self._iterptr = self.ap_config.sections().__iter__()
        return self
