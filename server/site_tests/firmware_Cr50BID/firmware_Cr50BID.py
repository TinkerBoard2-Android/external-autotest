# Copyright 2017 The Chromium OS Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import logging

from autotest_lib.client.common_lib import error
from autotest_lib.client.common_lib.cros import cr50_utils
from autotest_lib.server.cros import filesystem_util
from autotest_lib.server.cros.faft.cr50_test import Cr50Test


class firmware_Cr50BID(Cr50Test):
    """Verify cr50 board id behavior on a board id locked image.

    Check that cr50 will not accept mismatched board ids when it is running a
    board id locked image.

    Set the board id on a non board id locked image and verify cr50 will
    rollback when it is updated to a mismatched board id image.

    @param cr50_dbg_image_path: path to the node locked dev image.
    """
    version = 1

    MAX_BID = 0xffffffff

    # The universal image can be run on any system no matter the board id.
    UNIVERSAL = 'universal'
    # The board id locked can only run on devices with the right chip board id.
    BID_LOCKED = 'board_id_locked'
    # Full support required for this test was added in different MP releases.
    # - BID support was added in 0.0.21.
    # - Keeping the rollback state after AP boot was added in 0.3.4.
    # - Complete support for SPI PLT_RST straps was added in 0.3.18
    # Use 3.18, so the test can detect rollback and run on any board.
    BID_SUPPORT = '0.3.18'

    BID_MISMATCH = ['Board ID mismatched, but can not reboot.']
    BID_ERROR = 5
    SUCCESS = 0

    # BID_BASE_TESTS is a list with the the board id and flags to test for each
    # run. Each item in the list is a list of [board_id, flags, exit status].
    # exit_status should be BID_ERROR if the board id and flags should not be
    # compatible with the board id locked image.
    #
    # A image without board id will be able to run on a device with all of the
    # board id and flag combinations.
    #
    # When using a non-symbolic board id, make sure the length of the string is
    # greater than 4. If the string length is less than 4, usb_updater will
    # treat it as a symbolic string
    # ex: bid of 0 needs to be given as '0x0000'. If it were given as '0', the
    # board id value would be interpreted as ord('0')
    #
    # These base tests are be true no matter the board id, mask, or flags. If a
    # value is None, then it will be replaced with the test board id or flags
    # while running the test.
    BID_BASE_TESTS = [
        [None, None, SUCCESS],

        # Cr50 images are board id locked with flags. If we use 0 for the BID
        # flags, there should be an error.
        [None, 0, BID_ERROR],

        # All 1s in the board id flags should be acceptable no matter the
        # actual image flags
        [None, MAX_BID, SUCCESS],
    ]

    # Settings to test all of the cr50 BID responses. The dictionary conatins
    # the name of the BID verification as the key and a list as a value.
    #
    # The value of the list is the image to start running the test with then
    # the method to update to the board id locked image as the value.
    #
    # If the start image is 'board_id_locked', we won't try to update to the
    # board id locked image.
    BID_TEST_TYPE = [
        # Verify that the board id locked image rejects invalid board ids
        ['get/set', BID_LOCKED],

        # Verify the cr50 response when doing a normal update to a board id
        # locked image. If there is a board id mismatch, cr50 should rollback
        # to the image that was already running.
        ['rollback', UNIVERSAL],

        # TODO (mruthven): add support for verifying recovery
        # Certain devices are not able to successfully jump to the recovery
        # image when the TPM is locked down. We need to find a way to verify the
        # DUT is in recovery without being able to ssh into the DUT.
    ]

    def initialize(self, host, cmdline_args, basic=False, full_args={}):
        # Restore the original image and board id during cleanup.
        super(firmware_Cr50BID, self).initialize(host, cmdline_args, full_args,
                                                 restore_cr50_image=True,
                                                 restore_cr50_board_id=True)
        if self.servo.main_device_is_ccd():
            raise error.TestNAError('Use a flex cable instead of CCD cable.')

        if not self.cr50.has_command('bid'):
            raise error.TestNAError('Cr50 image does not support board id')

        self.image_versions = {}

        self.save_board_id_locked_image()
        self.save_universal_image()

        # Add tests to the test list based on the running board id infomation
        self.build_tests(basic)


    def add_test(self, board_id, flags, expected_result):
        """Add a test case to the list of tests

        The test will see if the board id locked image behaves as expected with
        the given board_id and flags.

        Args:
            board_id: A symbolic string or hex str representing the board id.
            flags: a int value for the flags
            expected_result: SUCCESS if the board id and flags should be
                accepted by the board id locked image. BID_ERROR if it should be
                rejected.
        """
        logging.info('Test Case: image board id %s with chip board id %s:%x '
                     'should %s', self.test_bid_str, board_id, flags,
                     'fail' if expected_result else 'succeed')
        self.tests.append([board_id, flags, expected_result])


    def add_board_id_tests(self):
        """Create a list of tests based on the board id and mask.

        For each bit set to 1 in the board id image mask, Cr50 checks that the
        bit in the board id infomask matches the image board id. Create a
        couple of test cases based on the test mask and board id to verify this
        behavior.
        """
        mask_str = bin(self.test_mask).split('b')[1]
        mask_str = '0' + mask_str if len(mask_str) < 32 else mask_str
        mask_str = mask_str[::-1]
        zero_index = mask_str.find('0')
        one_index = mask_str.find('1')

        # The hex version of the board id should be accepted.
        self.add_test(hex(self.test_bid_int), self.test_flags, self.SUCCESS)

        # Flip a bit we don't care about to make sure it is accepted
        if zero_index != -1:
            test_bid = self.test_bid_int ^ (1 << zero_index)
            self.add_test(hex(test_bid), self.test_flags, self.SUCCESS)


        if one_index != -1:
            # Flip a bit we care about to make sure it is rejected
            test_bid = self.test_bid_int ^ (1 << one_index)
            self.add_test(hex(test_bid), self.test_flags, self.BID_ERROR)
        else:
            # If there is not a 1 in the board id mask, then we don't care about
            # the board id at all. Flip all the bits and make sure setting the
            # board id still succeeds.
            test_bid = self.test_bid_int ^ self.MAX_BID
            self.add_test(hex(test_bid), self.test_flags, self.SUCCESS)


    def add_flag_tests(self):
        """Create a list of tests based on the test flags.

        When comparing the flag field, cr50 makes sure all 1s set in the image
        flags are also set as 1 in the infomask. Create a couple of test cases
        to verify cr50 responds appropriately to different flags.
        """
        flag_str = bin(self.test_flags).split('b')[1]
        flag_str_pad = '0' + flag_str if len(flag_str) < 32 else flag_str
        flag_str_pad_rev = flag_str_pad[::-1]
        zero_index = flag_str_pad_rev.find('0')
        one_index = flag_str_pad_rev.find('1')

        # If we care about any flag bits, setting the flags to 0 should cause
        # a rejection
        if self.test_flags:
            self.add_test(self.test_bid_sym, 0, self.BID_ERROR)

        # Flip a 0 to 1 to make sure it is accepted.
        if zero_index != -1:
            test_flags = self.test_flags | (1 << zero_index)
            self.add_test(self.test_bid_sym, test_flags, self.SUCCESS)

        # Flip a 1 to 0 to make sure it is rejected.
        if one_index != -1:
            test_flags = self.test_flags ^ (1 << one_index)
            self.add_test(self.test_bid_sym, test_flags, self.BID_ERROR)


    def build_tests(self, basic):
        """Add more test cases based on the image board id, flags, and mask"""
        self.tests = self.BID_BASE_TESTS
        if not basic:
            self.add_flag_tests()
            self.add_board_id_tests()
        logging.info('Running tests %r', self.tests)


    def save_universal_image(self, rw_ver=BID_SUPPORT):
        """Get the non board id locked image

        Save the universal image. Use the current cr50 image if it is not board
        id locked. If the original image is board id locked, download a release
        image from google storage.

        Args:
            rw_ver: The rw release version to use for the universal image.
        """
        release_info = self.download_cr50_release_image(rw_ver)
        self.universal_path, universal_ver = release_info

        logging.info('Running test with universal image %s', universal_ver)

        self.replace_image_if_newer(universal_ver[1], cr50_utils.CR50_PROD)
        self.replace_image_if_newer(universal_ver[1], cr50_utils.CR50_PREPVT)

        self.image_versions[self.UNIVERSAL] = universal_ver


    def replace_image_if_newer(self, universal_rw_ver, path):
        """Replace the image at path if it is newer than the universal image

        Copy the universal image to path, if the universal image is older than
        the image at path.

        Args:
            universal_rw_ver: The rw version string of the universal image
            path: The path of the image that may need to be replaced.
        """
        if self.host.path_exists(path):
            dut_ver = cr50_utils.GetBinVersion(self.host, path)[1]
            # If the universal version is lower than the DUT image, install the
            # universal image. It has the lowest version of any image in the
            # test, so cr50-update won't try to update cr50 at any point during
            # the test.
            install_image = (cr50_utils.GetNewestVersion(dut_ver,
                    universal_rw_ver) == dut_ver)
        else:
            # If the DUT doesn't have a file at path, install the image.
            install_image = True

        if install_image:
            # Disable rootfs verification so we can copy the image to the DUT
            filesystem_util.make_rootfs_writable(self.host)
            # Copy the universal image onto the DUT.
            dest, ver = cr50_utils.InstallImage(self.host, self.universal_path,
                    path)
            logging.info('Copied %s to %s', ver, dest)


    def save_board_id_locked_image(self):
        """Save the running image and get the board id information.

        Save the board id locked image. If the running image isn't board id
        locked, the test will be skipped.

        Raises:
            TestNAError if the running cr50 image is not board id locked.
        """
        version = self.get_saved_cr50_original_version()
        if not version[2]:
            raise error.TestNAError('The cr50 image is not board id locked')

        self.board_id_locked_path = self.get_saved_cr50_original_path()

        image_bid_info = cr50_utils.GetBoardIdInfoTuple(version[2])
        self.test_bid_int, self.test_mask, self.test_flags = image_bid_info
        self.test_bid_sym = cr50_utils.GetSymbolicBoardId(self.test_bid_int)
        self.test_bid_str = cr50_utils.GetBoardIdInfoString(version[2])

        if not self.test_flags:
            raise error.TestNAError('Image needs to have non-zero flags to run '
                                    'test')
        logging.info('Running test with bid locked image %s', version)
        self.image_versions[self.BID_LOCKED] = version


    def is_running_version(self, rw_ver, bid_str):
        """Returns True if the running image has the same rw ver and bid

        Args:
            rw_ver: rw version string
            bid_str: A symbolic or non-smybolic board id

        Returns:
            True if cr50 is running an image with the given rw version and
            board id.
        """
        running_rw = self.cr50.get_version()
        running_bid = self.cr50.get_active_board_id_str()
        # Convert the image board id to a non symbolic board id
        bid_str = cr50_utils.GetBoardIdInfoString(bid_str, symbolic=False)
        return running_rw == rw_ver and bid_str == running_bid


    def reset_state(self, image_type):
        """Update to the image and erase the board id.

        We can't erase the board id unless we are running a debug image. Update
        to the debug image so we can erase the board id and then rollback to the
        right image.

        Args:
            image_type: the name of the image we want to be running at the end
                        of reset_state: 'universal' or 'board_id_locked'. This
                        image name needs to correspond with some test attribute
                        ${image_type}_path

        Raises:
            TestFail if the board id was not erased
        """
        _, rw_ver, bid = self.image_versions[image_type]
        chip_bid = cr50_utils.GetChipBoardId(self.host)
        if self.is_running_version(rw_ver, bid) and (chip_bid ==
            cr50_utils.ERASED_CHIP_BID):
            logging.info('Skipping reset. Already running %s image with erased '
                'chip board id', image_type)
            return
        logging.info('Updating to %s image and erasing chip bid', image_type)

        self.eraseflashinfo_and_restore_image(self.get_saved_dbg_image_path())

        self.cr50_update(getattr(self, image_type + '_path'), rollback=True)

        # Verify the board id was erased
        if cr50_utils.GetChipBoardId(self.host) != cr50_utils.ERASED_CHIP_BID:
            raise error.TestFail('Could not erase bid')


    def updater_set_bid(self, bid, flags, exit_code):
        """Set the flags using usb_updater and verify the result

        Args:
            board_id: board id string
            flags: An int with the flag value
            exit_code: the expected error code. 0 if it should succeed

        Raises:
            TestFail if usb_updater had an unexpected exit status or setting the
            board id failed
        """

        original_bid, _, original_flags = cr50_utils.GetChipBoardId(self.host)

        if exit_code:
            exit_code = 'Error %d while setting board id' % exit_code

        try:
            cr50_utils.SetChipBoardId(self.host, bid, flags)
            result = self.SUCCESS
        except error.AutoservRunError, e:
            result = e.result_obj.stderr.strip()

        if result != exit_code:
            raise error.TestFail("Unexpected result setting %s:%x expected "
                                 "'%s' got '%s'" %
                                 (bid, flags, exit_code, result))

        # Verify cr50 is still running with the same board id and flags
        if exit_code:
            cr50_utils.CheckChipBoardId(self.host, original_bid, original_flags)


    def run_bid_test(self, image_name, bid, flags, bid_error):
        """Set the bid and flags. Verify a board id locked image response

        Update to the right image type and try to set the board id. Only the
        board id locked image should reject the given board id and flags.

        If we are setting the board id on a non-board id locked image, try to
        update to the board id locked image afterwards to verify that cr50 does
        or doesn't rollback. If there is a bid error, cr50 should fail to update
        to the board id locked image.


        Args:
            image_name: The image name 'universal', 'dev', or 'board_id_locked'
            bid: A string representing the board id. Either the hex or symbolic
                 value
            flags: A int value for the flags to set
            bid_error: The expected usb_update error code. 0 for success 5 for
                       failure
        """
        is_bid_locked_image = image_name == self.BID_LOCKED

        # If the image is not board id locked, it should accept any board id and
        # flags
        exit_code = bid_error if is_bid_locked_image else self.SUCCESS

        response = 'error %d' % exit_code if exit_code else 'success'
        logging.info('EXPECT %s setting bid to %s:%x with %s image',
                     response, bid, flags, image_name)

        # Erase the chip board id and update to the correct image
        self.reset_state(image_name)

        # Try to set the board id and flags
        self.updater_set_bid(bid, flags, exit_code)

        # If it failed before, it should fail with the same error. If we already
        # set the board id, it should fail because the board id is already set.
        self.updater_set_bid(bid, flags, exit_code if exit_code else 7)

        # After setting the board id with a non boardid locked image, try to
        # update to the board id locked image. Verify that cr50 does/doesn't run
        # it. If there is a mismatch, the update should fail and Cr50 should
        # rollback to the universal image.
        if not is_bid_locked_image:
            self.cr50_update(self.board_id_locked_path,
                             expect_rollback=(not not bid_error))


    def run_once(self):
        """Verify the Cr50 BID response of each test bid."""
        errors = []
        for test_type, image_name in self.BID_TEST_TYPE:
            logging.info('VERIFY: BID %s', test_type)
            for i, args in enumerate(self.tests):
                bid, flags, bid_error = args
                # Replace place holder values with the test values
                bid = bid if bid != None else self.test_bid_sym
                flags = flags if flags != None else self.test_flags
                message = '%s %d %s:%x %s' % (test_type, i, bid, flags,
                    bid_error)

                # Run the test with the given bid, flags, and result
                try:
                    self.run_bid_test(image_name, bid, flags, bid_error)
                    logging.info('Verified %s', message)
                except (error.TestFail, error.TestError) as e:
                    logging.info('FAILED %s with "%s"', message, e)
                    errors.append('%s with "%s"' % (message, e))
        if len(errors):
            raise error.TestFail('failed tests: %s', errors)
