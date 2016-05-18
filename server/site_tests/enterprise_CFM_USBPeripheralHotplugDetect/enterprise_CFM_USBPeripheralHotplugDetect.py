# Copyright (c) 2016 The Chromium OS Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import logging, os, time

from autotest_lib.client.common_lib.cros import tpm_utils
from autotest_lib.server import test, autotest

_WAIT_DELAY = 15
_USB_DIR = '/sys/bus/usb/devices'


class enterprise_CFM_USBPeripheralHotplugDetect(test.test):
    """Uses servo to hotplug and detect USB peripherals on CrOS and hotrod. It
    compares attached audio/video peripheral names on CrOS against what hotrod
    detects."""
    version = 1


    def _set_hub_power(self, on=True):
        """Setting USB hub power status

        @param on: To power on the servo usb hub or not.

        """
        reset = 'off'
        if not on:
            reset = 'on'
        self.host.servo.set('dut_hub1_rst1', reset)
        time.sleep(_WAIT_DELAY)


    def _get_usb_device_dirs(self):
        """Gets usb device dirs from _USB_DIR path.

        @returns list with number of device dirs else Non

        """
        usb_dir_list = list()
        cmd = 'ls %s' % _USB_DIR
        cmd_output = self.host.run(cmd).stdout.strip().split('\n')
        for d in cmd_output:
            usb_dir_list.append(os.path.join(_USB_DIR, d))
        return usb_dir_list


    def _get_usb_device_type(self, vendor_id):
        """Gets usb device type info from lsusb output based on vendor id.

        @vendor_id: Device vendor id.
        @returns list of device types associated with vendor id

        """
        details_list = list()
        cmd = 'lsusb -v -d ' + vendor_id + ': | head -150'
        cmd_out = self.host.run(cmd).stdout.strip().split('\n')
        for line in cmd_out:
            if (any(phrase in line for phrase in ('bInterfaceClass',
                    'wTerminalType'))):
                details_list.append(line.split(None)[2])

        return list(set(details_list))


    def _get_product_info(self, directory, prod_string):
        """Gets the product name from device path.

        @param directory: Driver path for USB device.
        @param prod_string: Device attribute string.
        @returns the output of the cat command

        """
        product_file_name = os.path.join(directory, prod_string)
        if self._file_exists_on_host(product_file_name):
            return self.host.run('cat %s' % product_file_name).stdout.strip()
        return None


    def _parse_device_dir_for_info(self, dir_list, peripheral_whitelist_dict):
        """Uses device path and vendor id to get device type attibutes.

        @param dir_list: Complete list of device directories.
        @returns cros_peripheral_dict with device names

        """
        cros_peripheral_dict = {'Camera': None, 'Microphone': None,
                                'Speaker': None}

        for d_path in dir_list:
            file_name = os.path.join(d_path, 'idVendor')
            if self._file_exists_on_host(file_name):
                vendor_id = self.host.run('cat %s' % file_name).stdout.strip()
                product_id = self._get_product_info(d_path, 'idProduct')
                vId_pId = vendor_id + ':' + product_id
                device_types = self._get_usb_device_type(vendor_id)
                if vId_pId in peripheral_whitelist_dict:
                    if 'Microphone' in device_types:
                        cros_peripheral_dict['Microphone'] = (
                                peripheral_whitelist_dict.get(vId_pId))
                    if 'Speaker' in device_types:
                        cros_peripheral_dict['Speaker'] = (
                                peripheral_whitelist_dict.get(vId_pId))
                    if 'Video' in device_types:
                        cros_peripheral_dict['Camera'] = (
                                peripheral_whitelist_dict.get(vId_pId))

        for device_type, is_found in cros_peripheral_dict.iteritems():
            if not is_found:
                cros_peripheral_dict[device_type] = 'Not Found'

        return cros_peripheral_dict


    def _file_exists_on_host(self, path):
        """Checks if file exists on host.

        @param path: File path
        @returns True or False

        """
        return self.host.run('ls %s' % path,
                             ignore_status=True).exit_status == 0


    def run_once(self, host, peripheral_whitelist_dict):
        """Main function to run autotest.

        @param host: Host object representing the DUT.

        """
        self.host = host

        tpm_utils.ClearTPMOwnerRequest(self.host)
        autotest.Autotest(self.host).run_test('enterprise_RemoraRequisition',
                                              check_client_result=True)

        self.host.servo.switch_usbkey('dut')
        self.host.servo.set('usb_mux_sel3', 'dut_sees_usbkey')
        time.sleep(_WAIT_DELAY)

        self._set_hub_power(True)
        usb_list_dir_on = self._get_usb_device_dirs()

        cros_peripheral_dict = self._parse_device_dir_for_info(usb_list_dir_on,
                peripheral_whitelist_dict)
        logging.debug('Peripherals detected by CrOS: %s', cros_peripheral_dict)

        autotest.Autotest(self.host).run_test(
                'enterprise_CFM_USBPeripheralDetect',
                cros_peripheral_dict=cros_peripheral_dict,
                check_client_result=True)

        tpm_utils.ClearTPMOwnerRequest(self.host)
