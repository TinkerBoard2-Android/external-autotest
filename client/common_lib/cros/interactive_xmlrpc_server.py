#!/usr/bin/env python

# Copyright (c) 2013 The Chromium OS Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import cgi
import json
import logging
import logging.handlers
import os
import sys

import common
from autotest_lib.client.bin import utils
from autotest_lib.client.common_lib.cros import chrome, xmlrpc_server
from autotest_lib.client.cros import constants


class InteractiveXmlRpcDelegate(xmlrpc_server.XmlRpcDelegate):
    """Exposes methods called remotely to create interactive tests.

    All instance methods of this object without a preceding '_' are exposed via
    an XML-RPC server. This is not a stateless handler object, which means that
    if you store state inside the delegate, that state will remain around for
    future calls.
    """

    def login(self):
        """Login to the system and open a tab.

        The tab opened is used by other methods on this server to interact
        with the user.

        @return True.

        """
        self._chrome = chrome.Chrome()
        self._chrome.browser.SetHTTPServerDirectories(
                os.path.dirname(sys.argv[0]))
        self._tab = self._chrome.browser.tabs[0]
        self._tab.Navigate(self._chrome.browser.http_server.UrlOf('shell.html'))

        return True


    def set_output(self, html):
        """Replace the contents of the tab.

        @param html: HTML document to replace tab contents with.

        @return True.

        """
        # JSON does a better job of escaping HTML for JavaScript than we could
        # with string.replace().
        html_escaped = json.dumps(html)
        # Use JavaScript to append the output and scroll to the bottom of the
        # open tab.
        self._tab.ExecuteJavaScript('document.body.innerHTML = %s; ' %
                                    html_escaped)
        self._tab.Activate()
        self._tab.WaitForDocumentReadyStateToBeInteractiveOrBetter()
        return True


    def append_output(self, html):
        """Append HTML to the contents of the tab.

        @param html: HTML to append to the existing tab contents.

        @return True.

        """
        # JSON does a better job of escaping HTML for JavaScript than we could
        # with string.replace().
        html_escaped = json.dumps(html)
        # Use JavaScript to append the output and scroll to the bottom of the
        # open tab.
        self._tab.ExecuteJavaScript(
                ('document.body.innerHTML += %s; ' % html_escaped) +
                'window.scrollTo(0, document.body.scrollHeight);')
        self._tab.Activate()
        self._tab.WaitForDocumentReadyStateToBeInteractiveOrBetter()
        return True


    def append_buttons(self, *args):
        """Append confirmation buttons to the tab.

        Each button is given an index, 0 for the first button, 1 for the second,
        and so on.

        @param title...: Title of button to append.

        @return True.

        """
        html = ''
        index = 0
        for title in args:
            onclick = 'submit_button(%d)' % index
            html += ('<input type="button" value="%s" onclick="%s">' % (
                     cgi.escape(title),
                     cgi.escape(onclick)))
            index += 1
        return self.append_output(html)


    def wait_for_button(self, timeout):
        """Wait for a button to be clicked.

        Call append_buttons() before this to add buttons to the document.

        @param timeout: Maximum time, in seconds, to wait for a click.

        @return index of button that was clicked.

        """
        # Wait for the button to be clicked.
        utils.poll_for_condition(
                condition=lambda:
                    self._tab.EvaluateJavaScript('window.__ready') == 1,
                desc='User clicked on button.',
                timeout=timeout)
        # Fetch the result.
        result = self._tab.EvaluateJavaScript('window.__result')
        # Reset for the next button.
        self._tab.ExecuteJavaScript(
                'window.__ready = 0; '
                'window.__result = null;')
        return result


    def close(self):
        """Close the browser.

        @return True.

        """
        if hasattr(self, '_chrome'):
            self._chrome.browser.Close()
        return True


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    handler = logging.handlers.SysLogHandler(address='/dev/log')
    logging.getLogger().addHandler(handler)
    logging.debug('interactive_xmlrpc_server main...')
    server = xmlrpc_server.XmlRpcServer(
            'localhost',
            constants.INTERACTIVE_XMLRPC_SERVER_PORT)
    server.register_delegate(InteractiveXmlRpcDelegate())
    server.run()
