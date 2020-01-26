# Copyright 2018 The Chromium OS Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import logging

from autotest_lib.client.common_lib import error
from autotest_lib.client.common_lib.cros import tpm_utils
from autotest_lib.server import autotest
from autotest_lib.server import test
from autotest_lib.server import utils


class rlz_CheckPing(test.test):
    """ Tests we are sending the CAF and CAI RLZ pings for first user."""
    version = 1

    _CLIENT_TEST = 'desktopui_CheckRlzPingSent'

    def _check_rlz_brand_code(self):
        """Checks that we have an rlz brand code."""
        try:
            self._host.run('cros_config / brand-code')
        except error.AutoservRunError as e:
            raise error.TestFail('DUT is missing brand_code: %s.' %
                                 e.result_obj.stderr)


    def _set_vpd_values(self, retries=3):
        """
        Sets the required vpd values for the test.

        @param retries: number of times to retry to write to vpd.

        """
        for i in range(retries):
            try:
                self._host.run('vpd -i RW_VPD -s should_send_rlz_ping=1')
                break
            except error.AutoservRunError as e:
                logging.exception('Failed to write should_send_rlz_ping to vpd')
                if i == retries-1:
                    raise error.TestFail('Failed to set should_send_rlz_ping '
                                         'VPD value on the DUT: %s' %
                                         e.result_obj.stderr)
        for i in range(retries):
            try:
                self._host.run('dump_vpd_log --force')
                break
            except error.AutoservRunError as e:
                logging.exception('Failed to dump vpd log')
                if i == retries - 1:
                    raise error.TestFail('Failed to dump vpd log: '
                                         '%s' % e.result_obj.stderr)


    def _check_rlz_vpd_settings_post_ping(self):
        """Checks that rlz related vpd settings are correct after the test."""
        def should_send_rlz_ping():
            """Ask vpd (on the DUT) whether we are ready to send rlz ping"""
            return int(self._host.run('vpd -i RW_VPD -g '
                                      'should_send_rlz_ping').stdout)

        utils.poll_for_condition(lambda: should_send_rlz_ping() == 0,
                                 timeout=60)

        result = self._host.run('vpd -i RW_VPD -g rlz_embargo_end_date',
                                ignore_status=True)
        if result.exit_status == 0:
            raise error.TestFail('rlz_embargo_end_date still present in vpd.')


    def run_once(self, host, ping_timeout=30, logged_in=True):
        """Main test logic"""
        self._host = host
        if 'veyron_rialto' in self._host.get_board():
            raise error.TestNAError('Skipping test on rialto device.')

        self._check_rlz_brand_code()

        # Clear TPM owner so we have no users on DUT.
        tpm_utils.ClearTPMOwnerRequest(self._host)

        # Setup DUT to send rlz ping after a short timeout.
        self._set_vpd_values()
        self._host.reboot()

        # Login, do a Google search, check for CAF event in RLZ Data file.
        client_at = autotest.Autotest(self._host)
        client_at.run_test(self._CLIENT_TEST, ping_timeout=ping_timeout,
                           logged_in=logged_in)
        client_at._check_client_test_result(self._host, self._CLIENT_TEST)

        self._check_rlz_vpd_settings_post_ping()
