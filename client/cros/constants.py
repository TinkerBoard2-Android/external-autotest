# Copyright (c) 2012 The Chromium OS Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

# The names of expected mount-points, devices, magic files, etc on chrome os.

# Constants used by other constants.
USER_DATA_DIR = '/home/chronos'
WHITELIST_DIR = '/var/lib/whitelist'


# Rest of constants.
BROWSER = 'chrome'
BROWSER_EXE = '/opt/google/chrome/' + BROWSER

CHROME_CORE_MAGIC_FILE = '/mnt/stateful_partition/etc/collect_chrome_crashes'
CHROME_LOG_DIR = '/var/log/chrome'

CLEANUP_LOGS_PAUSED_FILE = '/var/lib/cleanup_logs_paused'

CLIENT_LOGIN_URL = '/accounts/ClientLogin'
CLIENT_LOGIN_NEW_URL = '/ClientLogin'

CRASH_DIR = '/var/spool/crash'
CRASH_REPORTER_RESIDUE_DIR = '/tmp/crash_reporter'

CREDENTIALS = {
    '$mockowner': ['mockowner.test.account@gmail.com', 'perfsmurf'],
    '$default': ['performance.test.account@gmail.com', 'perfsmurf'],
    '$apps': ['performance.test.account@googleapps.com', 'perfsmurf'],
    '$backdoor': ['chronos@gmail.com', 'chronos'],
}

SHADOW_ROOT = '/home/.shadow'

CRYPTOHOME_DEV_REGEX_ANY = r'.*'
CRYPTOHOME_DEV_REGEX_REGULAR_USER_SHADOW = r'^/home/\.shadow/.*/vault$'
CRYPTOHOME_DEV_REGEX_REGULAR_USER_EPHEMERAL = r'^ephemeralfs/.*$'
CRYPTOHOME_DEV_REGEX_REGULAR_USER = r'(%s|%s)' % (
    CRYPTOHOME_DEV_REGEX_REGULAR_USER_SHADOW,
    CRYPTOHOME_DEV_REGEX_REGULAR_USER_EPHEMERAL)
CRYPTOHOME_DEV_REGEX_GUEST = r'^guestfs$'

CRYPTOHOME_FS_REGEX_ANY = r'.*'
CRYPTOHOME_FS_REGEX_TMPFS = r'^tmpfs$'

CRYPTOHOME_MOUNT_PT = USER_DATA_DIR + '/user'

CRYPTOHOMED_LOG = '/var/log/cryptohomed.log'

# Directories to copy out of cryptohome, relative to CRYPTOHOME_MOUNT_PT.
CRYPTOHOME_DIRS_TO_RECOVER = ['crash', 'log']

DISABLE_BROWSER_RESTART_MAGIC_FILE = '/var/run/disable_chrome_restart'
DEFAULT_OWNERSHIP_TIMEOUT = 300  # Ownership is an inherently random process.

FLIMFLAM_TEST_PATH = '/usr/lib/flimflam/test/'

KEYGEN = 'keygen'

LOGGED_IN_MAGIC_FILE = '/var/run/state/logged-in'

LOGIN_PROFILE = USER_DATA_DIR + '/Default'
LOGIN_SERVICE = 'gaia'
LOGIN_ERROR = 'Error=BadAuthentication'
LOGIN_PROMPT_VISIBLE_MAGIC_FILE = '/tmp/uptime-login-prompt-visible'
LOGIN_TRUST_ROOTS = '/etc/login_trust_root.pem'

MOCK_OWNER_CERT = 'mock_owner_cert.pem'
MOCK_OWNER_KEY = 'mock_owner_private.key'
MOCK_OWNER_POLICY = 'mock_owner.policy'

NETWORK_MANAGER = 'flimflam'

ISSUE_AUTH_TOKEN_URL = '/accounts/IssueAuthToken'
ISSUE_AUTH_TOKEN_NEW_URL = '/IssueAuthToken'

OWNER_KEY_FILE = WHITELIST_DIR + '/owner.key'

PORTAL_CHECK_URL = '/generate_204'
PROCESS_LOGIN_URL = '/accounts/ProcessServiceLogin'
PROCESS_LOGIN_NEW_URL = '/ProcessServiceLogin'

SERVICE_LOGIN_URL = '/accounts/ServiceLogin'
SERVICE_LOGIN_NEW_URL = '/ServiceLogin'
SESSION_MANAGER = 'session_manager'
SESSION_MANAGER_LOG = '/var/log/session_manager'
SIGNED_POLICY_FILE = WHITELIST_DIR + '/policy'
SPECIAL_CASE_DOMAIN = 'gmail.com'

TOKEN_AUTH_URL = '/accounts/TokenAuth'
TOKEN_AUTH_NEW_URL = '/TokenAuth'

UI_LOG = '/var/log/ui/ui.LATEST'
UPDATE_ENGINE_LOG = '/var/log/update_engine.log'

WINDOW_MANAGER = 'chromeos-wm'

PKCS11_INIT_MAGIC_FILE = '/home/chronos/user/.tpm/.isinitialized'

RESOLV_CONF_FILE = '/etc/resolv.conf'

PENDING_SHUTDOWN_PATH = '/var/lib/crash_reporter/pending_clean_shutdown'
UNCLEAN_SHUTDOWN_DETECTED_PATH = '/var/run/unclean-shutdown-detected'

FAKE_ROOT_CA_DIR = '/etc/fake_root_ca'
FAKE_NSSDB_DIR = FAKE_ROOT_CA_DIR + '/nssdb'
