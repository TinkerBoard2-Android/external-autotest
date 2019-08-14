# Copyright 2019 The Chromium OS Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

"""A Batch of of Bluetooth Classic sanity tests"""


from autotest_lib.server.cros.bluetooth.bluetooth_adapter_quick_tests import \
     BluetoothAdapterQuickTests

from autotest_lib.server.site_tests.bluetooth_AdapterPairing.bluetooth_AdapterPairing  import bluetooth_AdapterPairing
from autotest_lib.server.site_tests.bluetooth_AdapterHIDReports.bluetooth_AdapterHIDReports  import bluetooth_AdapterHIDReports

class bluetooth_AdapterCLSanity(BluetoothAdapterQuickTests,
        bluetooth_AdapterPairing,
        bluetooth_AdapterHIDReports):
    """A Batch of Bluetooth Classic sanity tests. This test is written as a batch
       of tests in order to reduce test time, since auto-test ramp up time is
       costly. The batch is using BluetoothAdapterQuickTests wrapper methods to
       start and end a test and a batch of tests.

       This class can be called to run the entire test batch or to run a
       specific test only
    """

    test_wrapper = BluetoothAdapterQuickTests.quick_test_test_decorator
    batch_wrapper = BluetoothAdapterQuickTests.quick_test_batch_decorator

    @test_wrapper('Pairing Test', devices=['MOUSE'])
    def cl_adapter_pairing_test(self):
        device = self.devices['MOUSE']
        self.pairing_test(device)

    @test_wrapper('Pairing Suspend Resume Test', devices=['MOUSE'])
    def cl_adapter_pairing_suspend_resume_test(self):
        device = self.devices['MOUSE']
        self.pairing_test(device, suspend_resume=True)

    @test_wrapper('HID Reports Test', devices=['MOUSE'])
    def cl_HID_reports_test(self):
        device = self.devices['MOUSE']
        self.run_hid_reports_test(device)

    @test_wrapper('HID Reports Suspend Resume Test', devices=['MOUSE'])
    def cl_HID_reports_suspend_resume_test(self):
        device = self.devices['MOUSE']
        self.run_hid_reports_test(device, suspend_resume=True)

    @test_wrapper('HID Reports Reboot Test', devices=['MOUSE'])
    def cl_HID_reports_reboot_test(self):
        device = self.devices['MOUSE']
        self.run_hid_reports_test(device, reboot=True)

    @test_wrapper('Connect Disconnect Loop Test', devices=['MOUSE'])
    def cl_connect_disconnect_loop_test(self):
        device = self.devices['MOUSE']
        self.connect_disconnect_loop(device=device, loops=3)

    @batch_wrapper('Classic Sanity')
    def cl_sanity_batch_run(self, num_iterations=1, test_name=None):
        """Run the Classic sanity test batch or a specific given test.
           The wrapper of this method is implemented in batch_decorator.
           Using the decorator a test batch method can implement the only its
           core tests invocations and let the decorator handle the wrapper,
           which is taking care for whether to run a specific test or the
           batch as a whole, and running the batch in iterations

           @param num_iterations: how many interations to run
           @param test_name: specifc test to run otherwise None to run the
                             whole batch
        """
        self.cl_adapter_pairing_test()
        self.cl_adapter_pairing_suspend_resume_test()
        self.cl_HID_reports_test()
        self.cl_HID_reports_suspend_resume_test()
        self.cl_HID_reports_reboot_test()
        self.cl_connect_disconnect_loop_test()

    def run_once(self, host, num_iterations=1, test_name=None):
        """Run the batch of Bluetooth Classic sanity tests

        @param host: the DUT, usually a chromebook
        @param num_iterations: the number of rounds to execute the test
        @test_name: the test to run, or None for all tests
        """

        # Initialize and run the test batch or the requested specific test
        self.quick_test_init(host, use_chameleon=True)
        self.cl_sanity_batch_run(num_iterations, test_name)
        self.quick_test_cleanup()
