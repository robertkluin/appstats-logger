#
# Copyright 2013 Robert Kluin
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
"""This is a simple RPC recorder based on the App Stats recorder.  It is
designed to be registered with an App Stats recorder proxy, then called via
the RPC pre and post hooks.  It collects data on the duration of RPCs.
"""
import logging
import threading
import time


class Recorder(object):
    """In-memory state for the current request.

    An instance is created soon after the request is received, and
    set as the Recorder for the current request in the
    RequestLocalRecorderProxy in the global variable 'recorder_proxy'.  It
    collects information about the request and about individual RPCs
    made during the request, until just before the response is sent out,
    when the recorded information is logged by calling the emit() method.
    """

    def __init__(self, env):
        """Constructor.

        Args:
        env: A dict giving the CGI or WSGI environment.
        """
        self.start_timestamp = time.time()
        self.end_timestamp = self.start_timestamp

        self.pending = {}
        self.traces = []

        self._lock = threading.Lock()

        self.overhead = (time.time() - self.start_timestamp)

    def record_rpc_request(self, service, call, request, response, rpc):
        """Record the request of an RPC call.

        Args:
            service: The service name, e.g. 'memcache'.
            call: The call name, e.g. 'Get'.
            request: The request object.
            response: The response object (ignored).
            rpc: The RPC object; may be None.
        """
        pre_now = time.time()
        now = time.time()

        trace = {
            'offset': int(1000 * (now - self.start_timestamp)),
            'service': service,
            'call': call,
        }

        with self._lock:
            if rpc is not None:
                self.pending[rpc] = len(self.traces)

            self.traces.append(trace)
            self.overhead += (now - pre_now)

    def record_rpc_response(self, service, call, request, response, rpc):
        """Record the response of an RPC call.

        Args:
            service: The service name, e.g. 'memcache'.
            call: The call name, e.g. 'Get'.
            request: The request object.
            response: The response object (ignored).
            rpc: The RPC object; may be None.

        This first tries to match the request with an unmatched request trace.
        If no matching request trace is found, this is logged as a new trace.
        """
        now = time.time()

        delta = int(1000 * (now - self.start_timestamp))

        if rpc is not None:
            with self._lock:
                index = self.pending.get(rpc)
                if index is not None:
                    del self.pending[rpc]

                    if 0 <= index < len(self.traces):
                        trace = self.traces[index]
                        trace.update({
                            'duration': delta - trace['offset']
                        })
                        self.overhead += (time.time() - now)
                        return
        else:
            with self._lock:
                for trace in reversed(self.traces):
                    if (trace['service'] == service and
                            trace['call'] == call and
                            not trace['duration']):
                        logging.info('Matched RPC response without rpc object')
                        trace.update({
                            'duration': delta - trace['offset']
                        })
                        self.overhead += (time.time() - now)
                        return

        logging.warn('RPC response without matching request')

        trace = {
            'offset': delta,
            'service': service,
            'call': call,
            'duration': 0,
        }
        with self._lock:
            self.traces.append(trace)
            self.overhead += (time.time() - now)

    def get_profile_data(self):
        """Return a dict with the profile results."""
        return {
            'overhead': int(self.overhead * 1000),
            'exec_time': int((time.time() - self.start_timestamp) * 1000),
            'calls': self.traces
        }

