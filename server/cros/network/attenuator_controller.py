# Copyright (c) 2014 The Chromium OS Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import logging
import os

from autotest_lib.client.common_lib import error


SYS_GPIO_PATH = '/sys/class/gpio/'
SYS_PINMUX_PATH = '/sys/kernel/debug/omap_mux/'
OMAP_MUX_GPIO_MODE = 'OMAP_MUX_MODE7'

MAX_VARIABLE_ATTENUATION = 95

# Index of GPIO banks. Each GPIO bank is 32-bit long.
GPIO_BANK0 = 0
GPIO_BANK1 = 1
GPIO_BANK2 = 2


class GpioPin(object):
    """Contains relevant details about a GPIO pin."""
    def __init__(self, bank, bit, pinmux_file, pin_name):
        """Construct a GPIO pin object.

        @param bank: int GPIO bank number (from 0-2 on BeagleBone White).
        @param bit: int bit offset in bank (from 0-31 on BeagleBone White).
        @param pinmux_file: string name of pinmux file.  This file is used to
                set the mode of a pin.  For instance, some pins are part of
                UART interfaces in addition to being GPIO capable.
        @param pin_name: string name of pin for debugging.

        """
        self.offset = str(bank * 32 + bit)
        self.pinmux_file = os.path.join(SYS_PINMUX_PATH, pinmux_file)
        self.pin_name = pin_name
        self.value_file = os.path.join(SYS_GPIO_PATH, 'gpio' + self.offset,
                                       'value')
        self.export_file = os.path.join(SYS_GPIO_PATH, 'export')
        self.unexport_file = os.path.join(SYS_GPIO_PATH, 'unexport')
        self.direction_file = os.path.join(SYS_GPIO_PATH, 'gpio' + self.offset,
                                           'direction')

# Variable attenuators are controlled by turning GPIOs on and off.  GPIOs
# are arranged in 3 banks on the BeagleBone White, 32 pins to a bank.  We
# pick groups of 8 pins such that the pins are physically near to each other
# to form the inputs to a given variable attenuator.  These inputs spell
# a binary word, which corresponds to the generated attenuation in dB.  For
# instance, turning on bits 0, 3, and 5 in a group:
#
#      attenuation = (1 << 0) + (1 << 3) + (1 << 5) = 0x25 = 37 dB
#
# Bits are listed in ascending order in a group (bit 0 first).  There are
# four groups of bits, one group per attenuator.
#
# Note that there is also a fixed amount of loss generated by the attenuator
# that we account for in the constant for the fixed loss along the path
# for a given antenna.
#
# On hosts with 4 attenuators, these are arranged so that attenuators 0/1
# control the main/aux antennas of a radio, and 2/3 control the main/aux
# lines of a second radio.  For hosts with only two attenuators, there
# should also be only a single phy.
#
# These mappings are specific to:
#  hardware: BeagleBone board (revision A3)
#  operating system: Angstrom Linux v2011.11-core (Core edition)
#  image version:
#      Angstrom-Cloud9-IDE-eglibc-ipk-v2011.11-core-beaglebone-2011.11.16
VARIABLE_ATTENUATORS = {
        0: [GpioPin(GPIO_BANK1, 31, 'gpmc_csn2', 'GPIO1_31'),
            GpioPin(GPIO_BANK1, 30, 'gpmc_csn1', 'GPIO1_30'),
            GpioPin(GPIO_BANK1, 5,  'gpmc_ad5',  'GPIO1_5'),
            GpioPin(GPIO_BANK1, 4,  'gpmc_ad4',  'GPIO1_4'),
            GpioPin(GPIO_BANK1, 1,  'gpmc_ad1',  'GPIO1_1'),
            GpioPin(GPIO_BANK1, 0,  'gpmc_ad0',  'GPIO1_0'),
            GpioPin(GPIO_BANK1, 29, 'gpmc_csn0', 'GPIO1_29'),
            GpioPin(GPIO_BANK2, 22, 'lcd_vsync', 'GPIO2_22'),
           ],
        1: [GpioPin(GPIO_BANK1, 6,  'gpmc_ad6',      'GPIO1_6'),
            GpioPin(GPIO_BANK1, 2,  'gpmc_ad2',      'GPIO1_2'),
            GpioPin(GPIO_BANK1, 3,  'gpmc_ad3',      'GPIO1_3'),
            GpioPin(GPIO_BANK2, 2,  'gpmc_advn_ale', 'TIMER4'),
            GpioPin(GPIO_BANK2, 3,  'gpmc_oen_ren',  'TIMER7'),
            GpioPin(GPIO_BANK2, 5,  'gpmc_ben0_cle', 'TIMER5'),
            GpioPin(GPIO_BANK2, 4,  'gpmc_wen',      'TIMER6'),
            GpioPin(GPIO_BANK1, 13, 'gpmc_ad13',     'GPIO1_13'),
           ],
        2: [GpioPin(GPIO_BANK1, 12, 'gpmc_ad12',  'GPIO1_12'),
            GpioPin(GPIO_BANK0, 23, 'gpmc_ad9',   'EHRPWM2B'),
            GpioPin(GPIO_BANK0, 26, 'gpmc_ad10',  'GPIO0_26'),
            GpioPin(GPIO_BANK1, 15, 'gpmc_ad15',  'GPIO1_15'),
            GpioPin(GPIO_BANK1, 14, 'gpmc_ad14',  'GPIO1_14'),
            GpioPin(GPIO_BANK0, 27, 'gpmc_ad11',  'GPIO0_27'),
            GpioPin(GPIO_BANK2, 1,  'mcasp0_fsr', 'GPIO2_1'),
            GpioPin(GPIO_BANK0, 22, 'gpmc_ad11',  'EHRPWM2A'),
           ],
        3: [GpioPin(GPIO_BANK2, 24, 'lcd_pclk',       'GPIO2_24'),
            GpioPin(GPIO_BANK2, 23, 'lcd_hsync',      'GPIO2_23'),
            GpioPin(GPIO_BANK2, 25, 'lcd_ac_bias_en', 'GPIO2_25'),
            GpioPin(GPIO_BANK0, 10, 'lcd_data14',     'UART5_CTSN'),
            GpioPin(GPIO_BANK0, 11, 'lcd_data15',     'UART5_RTSN'),
            GpioPin(GPIO_BANK0, 9,  'lcd_data13',     'UART4_RTSN'),
            GpioPin(GPIO_BANK2, 17, 'lcd_data11',     'UART3_RTSN'),
            GpioPin(GPIO_BANK0, 8,  'lcd_data12',     'UART4_CTSN'),
           ],
}


# This map represents the fixed loss overhead on a given antenna line.
# The map maps from:
#     attenuator hostname -> attenuator number -> frequency -> loss in dB.
HOST_TO_FIXED_ATTENUATIONS = {
        'chromeos1-grover-host1-attenuator': {
                0: {2437: 53, 5220: 56, 5765: 56},
                1: {2437: 54, 5220: 56, 5765: 59},
                2: {2437: 54, 5220: 57, 5765: 57},
                3: {2437: 54, 5220: 57, 5765: 59}},
        'chromeos1-grover-host2-attenuator': {
                0: {2437: 55, 5220: 59, 5765: 59},
                1: {2437: 53, 5220: 55, 5765: 55},
                2: {2437: 56, 5220: 60, 5765: 59},
                3: {2437: 56, 5220: 58, 5765: 58}},
        'chromeos1-grover-host3-attenuator': {
                0: {2437: 54, 5220: 59, 5765: 57},
                1: {2437: 54, 5220: 57, 5765: 57},
                2: {2437: 54, 5220: 58, 5765: 57},
                3: {2437: 54, 5220: 57, 5765: 57}},
        'chromeos1-grover-host4-attenuator': {
                0: {2437: 54, 5220: 58, 5765: 58},
                1: {2437: 54, 5220: 58, 5765: 58},
                2: {2437: 54, 5220: 58, 5765: 58},
                3: {2437: 54, 5220: 57, 5765: 57}},
        'chromeos1-grover-host5-attenuator': {
                0: {2437: 50, 5220: 53, 5765: 54},
                1: {2437: 52, 5220: 57, 5765: 57},
                2: {2437: 50, 5220: 55, 5765: 53},
                3: {2437: 52, 5220: 55, 5765: 55}},
        'chromeos1-grover-host6-attenuator': {
                0: {2437: 54, 5220: 56, 5765: 57},
                1: {2437: 54, 5220: 56, 5765: 58},
                2: {2437: 54, 5220: 56, 5765: 57},
                3: {2437: 54, 5220: 57, 5765: 58}},
        }


class AttenuatorController(object):
    """Represents a BeagleBone controlling several variable attenuators.

    This device is used to vary the attenuation between a router and a client.
    This allows us to measure throughput as a function of signal strength and
    test some roaming situations.  The throughput vs signal strength tests
    are referred to rate vs range (RvR) tests in places.

    @see BeagleBone System Reference Manual (RevA3_1.0):
        http://beagleboard.org/static/beaglebone/a3/Docs/Hardware/BONE_SRM.pdf
    @see Texas Instrument's GPIO Driver Guide
        http://processors.wiki.ti.com/index.php/GPIO_Driver_Guide

    """

    @property
    def supported_attenuators(self):
        """@return iterable of int attenuators supported on this host."""
        return self._fixed_attenuations.keys()


    def __init__(self, host):
        """Construct a AttenuatorController.

        @param host: Host object representing the remote BeagleBone.

        """
        super(AttenuatorController, self).__init__()
        self._host = host
        hostname = host.hostname
        if hostname.find('.') > 0:
            hostname = hostname[0:hostname.find('.')]
        if hostname not in HOST_TO_FIXED_ATTENUATIONS.keys():
            raise error.TestError('Unexpected RvR host name %r.' % hostname)
        self._fixed_attenuations = HOST_TO_FIXED_ATTENUATIONS[hostname]
        logging.info('Configuring GPIO ports on attenuator host.')
        for attenuator in self.supported_attenuators:
            for gpio_pin in VARIABLE_ATTENUATORS[attenuator]:
                self._enable_gpio_pin(gpio_pin)
                self._setup_gpio_pin(gpio_pin)
        self.set_variable_attenuation(0)


    def _approximate_frequency(self, attenuator_num, freq):
        """Finds an approximate frequency to freq.

        In case freq is not present in self._fixed_attenuations, we use a value
        from a nearby channel as an approximation.

        @param attenuator_num: attenuator in question on the remote host.  Each
                attenuator has a different fixed path loss per frequency.
        @param freq: int frequency in MHz.
        @returns int approximate frequency from self._fixed_attenuations.

        """
        old_offset = None
        approx_freq = None
        for defined_freq in self._fixed_attenuations[attenuator_num].keys():
            new_offset = abs(defined_freq - freq)
            if old_offset is None or new_offset < old_offset:
                old_offset = new_offset
                approx_freq = defined_freq

        logging.debug('Approximating attenuation for frequency %d with '
                      'constants for frequency %d.', freq, approx_freq)
        return approx_freq


    def _enable_gpio_pin(self, gpio_pin):
        """Enable a pin's GPIO function.

        @param gpio_pin: GpioPin object.

        """
        self._host.run('echo 7 > %s' % gpio_pin.pinmux_file)
        # Example contents of pinmux sysfile:
        #  name: lcd_pclk.lcd_pclk (0x44e108e8/0x8e8 = 0x0000), b NA, t NA
        #  mode: OMAP_PIN_OUTPUT | OMAP_MUX_MODE0
        #  signals: lcd_pclk | NA | NA | NA | NA | NA | NA | NA
        desired_prefix = 'mode:'
        result = self._host.run('cat %s' % gpio_pin.pinmux_file)
        for line in result.stdout.splitlines():
            if not line.startswith(desired_prefix):
                continue
            line = line[len(desired_prefix):]
            modes = [mode.strip() for mode in line.split('|')]
            break
        else:
            raise error.TestError('Failed to parse pinmux file')

        if OMAP_MUX_GPIO_MODE not in modes:
            raise error.TestError('Error setting pin %s to GPIO mode' %
                                  gpio_pin.pin_name)


    def _setup_gpio_pin(self, gpio_pin, enable=True):
        """Export or unexport a GPIO pin.

        GPIO pins must be exported before becoming usable.

        @param gpio_pin: GpioPin object.
        @param enable: bool True to export this pin.

        """
        if enable:
            sysfile = gpio_pin.export_file
        else:
            sysfile = gpio_pin.unexport_file
        self._host.run('echo %s > %s' % (gpio_pin.offset, sysfile),
                       ignore_status=True)
        if enable:
            # Set it to output
            self._host.run('echo out > %s' % gpio_pin.direction_file)


    def close(self):
        """Close this BB host and turn off all variabel attenuation."""
        self.set_variable_attenuation(0)
        self._host.close()


    def set_total_attenuation(self, atten_db, frequency_mhz,
                              attenuator_num=None):
        """Set the total attenuation on one or all attenuators.

        @param atten_db: int level of attenuation in dB.  This must be
                higher than the fixed attenuation level of the affected
                attenuators.
        @param frequency_mhz: int frequency for which to calculate the
                total attenuation.  The fixed component of attenuation
                varies with frequency.
        @param attenuator_num: int attenuator to change, or None to
                set all variable attenuators.

        """
        affected_attenuators = self.supported_attenuators
        if attenuator_num is not None:
            affected_attenuators = [attenuator_num]
        for attenuator in affected_attenuators:
            freq_to_fixed_loss = self._fixed_attenuations[attenuator]
            approx_freq = self._approximate_frequency(attenuator,
                                                      frequency_mhz)
            variable_atten_db = atten_db - freq_to_fixed_loss[approx_freq]
            self.set_variable_attenuation(variable_atten_db,
                                          attenuator_num=attenuator)


    def set_variable_attenuation(self, atten_db, attenuator_num=None):
        """Set the variable attenuation on one or all attenuators.

        @param atten_db: int non-negative level of attenuation in dB.
        @param attenuator_num: int attenuator to change, or None to
                set all variable attenuators.

        """
        if atten_db > MAX_VARIABLE_ATTENUATION:
            raise error.TestError('Requested variable attenuation greater '
                                  'than maximum. (%d > %d)' %
                                  (atten_db, MAX_VARIABLE_ATTENUATION))

        if atten_db < 0:
            raise error.TestError('Only positive attenuations are supported. '
                                  '(requested %d)' % atten_db)

        affected_attenuators = self.supported_attenuators
        if attenuator_num is not None:
            affected_attenuators = [attenuator_num]
        for attenuator in affected_attenuators:
            bit_field = atten_db
            for gpio_pin in VARIABLE_ATTENUATORS[attenuator]:
                bit_value = bit_field & 1
                self._host.run('echo %d > %s' %
                               (bit_value, gpio_pin.value_file))
                bit_field = bit_field >> 1
