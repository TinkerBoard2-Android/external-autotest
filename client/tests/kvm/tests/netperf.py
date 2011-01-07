import logging, commands, os
from autotest_lib.client.common_lib import error
from autotest_lib.client.bin import utils
import kvm_test_utils

def run_netperf(test, params, env):
    """
    Network stress test with netperf.

    1) Boot up a VM.
    2) Launch netserver on guest.
    3) Execute netperf client on host with different protocols.
    4) Output the test result.

    @param test: KVM test object.
    @param params: Dictionary with the test parameters.
    @param env: Dictionary with test environment.
    """
    vm = kvm_test_utils.get_living_vm(env, params.get("main_vm"))
    login_timeout = int(params.get("login_timeout", 360))
    session = kvm_test_utils.wait_for_login(vm, timeout=login_timeout)

    netperf_dir = os.path.join(os.environ['AUTODIR'], "tests/netperf2")
    setup_cmd = params.get("setup_cmd")
    guest_ip = vm.get_address()
    result_file = os.path.join(test.resultsdir, "output_%s" % test.iteration)

    firewall_flush = "iptables -F"
    session.get_command_output(firewall_flush)

    for i in params.get("netperf_files").split():
        if not vm.copy_files_to(os.path.join(netperf_dir, i), "/tmp"):
            raise error.TestError("Could not copy file %s to guest" % i)

    if session.get_command_status(firewall_flush):
        logging.warning("Could not flush firewall rules on guest")

    if session.get_command_status(setup_cmd % "/tmp", timeout=200):
        raise error.TestFail("Fail to setup netperf on guest")

    if session.get_command_status(params.get("netserver_cmd") % "/tmp"):
        raise error.TestFail("Fail to start netperf server on guest")

    try:
        logging.info("Setup and run netperf client on host")
        utils.run(setup_cmd % netperf_dir)
        list_fail = []
        result = open(result_file, "w")
        result.write("Netperf test results\n")

        for i in params.get("protocols").split():
            cmd = params.get("netperf_cmd") % (netperf_dir, i, guest_ip)
            logging.info("Netperf: protocol %s", i)
            try:
                netperf_output = utils.system_output(cmd,
                                                     retain_output=True)
                result.write("%s\n" % netperf_output)
            except:
                logging.error("Test of protocol %s failed", i)
                list_fail.append(i)

        result.close()

        if list_fail:
            raise error.TestFail("Some netperf tests failed: %s" %
                                 ", ".join(list_fail))

    finally:
        session.get_command_output("killall netserver")
        session.close()
