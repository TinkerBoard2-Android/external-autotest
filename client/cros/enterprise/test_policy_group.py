# Copyright 2019 The Chromium OS Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
import unittest


from autotest_lib.client.cros.enterprise import policy_group
"""

d8888b. d88888b  .d8b.  d8888b. .88b  d88. d88888b
88  `8D 88'     d8' `8b 88  `8D 88'YbdP`88 88'
88oobY' 88ooooo 88ooo88 88   88 88  88  88 88ooooo
88`8b   88~~~~~ 88~~~88 88   88 88  88  88 88~~~~~
88 `88. 88.     88   88 88  .8D 88  88  88 88.
88   YD Y88888P YP   YP Y8888D' YP  YP  YP Y88888P

This is the unittest file for enterprise_policy_utils.
If you modify that file, you should be at minimum re-running this file.

Add and correct tests as changes are made to the utils file.

To run the tests, use the following command from your DEV box (outside_chroot):

src/third_party/autotest/files/utils$ python unittest_suite.py \
autotest_lib.client.cros.enterprise.test_policy_group --debug

Most of the test data are large dictionaries mocking real data. They are stored
in the ent_policy_unittest_data file (located in this directory).

"""


class TestPolicyGroup(unittest.TestCase):

    def setupFullPolicy(self):
        testPolicy = {'Extension1': {'Policy1': 'Value1'},
                      'Extension2': {'Policy2': 'Value2'}}
        testUserPolicy = {'Userpolicy1': 1}
        testDevicePolicy = {'SystemTimezone': 'v1'}
        testSuggestedUserPolicy = {'Suggested1': '1'}
        self.policy_group_object = policy_group.AllPolicies(True)
        self.policy_group_object.set_extension_policy(testPolicy)
        self.policy_group_object.set_policy('chrome', testUserPolicy, 'user')
        self.policy_group_object.set_policy('chrome', testDevicePolicy,
                                            'device')
        self.policy_group_object.set_policy('chrome', testSuggestedUserPolicy,
                                            'suggested_user')

    def test_Normal(self):
        policy_group.AllPolicies()
        self.assertEqual(1, 1)

    def test_extension(self):
        # Set the "actual" Extension policy
        extension_test = policy_group.AllPolicies(True)
        test_set = {'Extension1': {'Policy1': 'Hidden1'}}
        test_set2 = {'Extension1': {'Policy1': 'Displayed'}}

        # Set the "Visual" Extension policy (ie, What should be displayed)
        extension_test.set_extension_policy(test_set)
        extension_test.set_extension_policy(test_set2, True)

        # Verify its displayed correctly when the "visual" dict is requested.
        self.assertEqual(
            (extension_test.get_policy_as_dict(True)['extensionPolicies']
                ['Extension1']['Policy1']['value']),
            'Displayed')

        # Verify the DM Json remains correct.
        extension_test.updateDMJson()
        self.assertEqual((extension_test._DMJSON['google/chrome/extension']
                              ['Extension1']['Policy1']),
                          'Hidden1')

        # Test the == function will use the "Displayed" value for the check,
        # not the configured

        extension_test_received = policy_group.AllPolicies()
        received_set = {'Extension1':
                            {'Policy1':
                                {'scope': 'user',
                                 'level': 'mandatory',
                                 'value': 'Displayed',
                                 'source': 'cloud'}
                             }
                        }

        extension_test_received.set_extension_policy(received_set)

        self.assertTrue(extension_test == extension_test_received)

    def test_set_policy(self):
        policy_group_object = policy_group.AllPolicies(True)
        policy_group_object.set_policy('chrome',
                                       {'TestPolicy': 'TestValue'},
                                       'user')
        self.assertIn('TestPolicy', policy_group_object.chrome)
        # Testing the other values will be covered in the policy unittest
        self.assertEqual(policy_group_object.chrome['TestPolicy'].value,
                         'TestValue')

    def test_ExtPolicy(self):
        testPolicy = {'Extension1': {'Policy1': 'Value1'},
                      'Extension2': {'Policy2': 'Value2'}}
        policy_group_object = policy_group.AllPolicies(True)
        policy_group_object.set_extension_policy(testPolicy)
        for Extension in testPolicy:
            self.assertIn(Extension,
                          policy_group_object.extension_configured_data)
            for policy in testPolicy[Extension]:
                self.assertIn(policy,
                              policy_group_object.extension_configured_data[Extension])

    def test_get_policy_as_dict(self):
        self.setupFullPolicy()
        expected_policyDict = {
            'deviceLocalAccountPolicies': {},
            'extensionPolicies':
                {'Extension2':
                    {'Policy2':
                        {'scope': 'user',
                         'level': 'mandatory',
                         'value': 'Value2',
                         'source': 'cloud'}},
                 'Extension1':
                    {'Policy1':
                        {'scope': 'user',
                         'level': 'mandatory',
                         'value': 'Value1',
                         'source': 'cloud'}}},
            'chromePolicies':
                {'Suggested1':
                    {'scope': 'user',
                     'level': 'recommended',
                     'value': '1',
                     'source': 'cloud'},
                 'SystemTimezone':
                    {'scope': 'machine',
                     'level': 'mandatory',
                     'value': 'v1',
                     'source': 'cloud'},
                 'Userpolicy1':
                    {'scope': 'user',
                     'level': 'mandatory',
                     'value': 1,
                     'source': 'cloud'}}}
        self.assertEqual(self.policy_group_object.get_policy_as_dict(),
                         expected_policyDict)

    def test_UpdateDMJson(self):
        self.setupFullPolicy()
        self.policy_group_object.updateDMJson()
        expected_DMJson = {
            'invalidation_name': 'test_policy',
            'invalidation_source': 16,
            'google/chromeos/device':
                {'timezone': 'v1'},
            'current_key_index': 0,
            'google/chrome/extension':
                {'Extension2': {'Policy2': 'Value2'},
                 'Extension1': {'Policy1': 'Value1'}},
            'managed_users': ['*'],
            'google/chromeos/user':
                {'recommended': {'Suggested1': '1'},
                 'mandatory': {'Userpolicy1': 1}},
            'policy_user': None}
        self.assertEqual(self.policy_group_object._DMJSON, expected_DMJson)


if __name__ == '__main__':
    unittest.main()
