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
"""This is a simple middleware to handle setting up the App Stats recorder,
and then getting and dumping the profile data from it at the end of the
request.
"""
import base64
import zlib
import json
import logging
import os
import time

from google.appengine.api import memcache
from google.appengine.ext.appstats.recording import recorder_proxy

from appstats_logger.recorder import Recorder

_local_cache = dict()

class StatsDjangoMiddleware(object):
    """Django Middleware to install the instrumentation.

    To start recording your app's RPC statistics, add

        'appstats_logger.middleware.StatsDjangoMiddleware',

    to the MIDDLEWARE_CLASSES entry in your Django settings.py file.
    It's best to insert it in front of any other middleware classes,
    since some other middleware may make RPC calls and those won't be
    recorded if that middleware is invoked before this middleware.

    See http://docs.djangoproject.com/en/dev/topics/http/middleware/.
    """

    def process_request(self, request):
        """Called by Django before deciding which view to execute."""
        _start_recording()

    def process_response(self, request, response):
        """Called by Django just before returning a response."""
        _stop_recording()
        return response


def stats_logger_wsgi_middleware(app):

    def appstats_wsgi_wrapper(environ, start_response):
        """Outer wrapper function around the WSGI protocol.

        The top-level appstats_wsgi_middleware() function returns this
        function to the caller instead of the app class or function passed
        in.  When the caller calls this function (which may happen
        multiple times, to handle multiple requests) this function
        instantiates the app class (or calls the app function), sandwiched
        between calls to start_recording() and end_recording() which
        manipulate the recording state.

        The signature is determined by the WSGI protocol.
        """
        _start_recording(environ)

        try:
            result = app(environ, start_response)
        except Exception:
            _stop_recording()
            raise

        if result is not None:
            for value in result:
                yield value

        _stop_recording()

    return appstats_wsgi_wrapper


def _start_recording(env=None):
    """Reset the recorder registry (proxy), and setup a new recorder."""
    recorder_proxy.clear_for_current_request()
    if env is None:
        env = os.environ

    recorder_proxy.set_for_current_request(Recorder(env))


def _stop_recording():
    """Get the current recorder and log the profiling data."""
    rec = recorder_proxy.get_for_current_request()
    if rec is not None:
        # update _local_cache if this is the first time or it's been 10 min
        if _local_cache.get('last_check', 0) + 600 < int(time.time()):
            use_plaintext = memcache.get('appstats-logger_use-plaintext')
            _local_cache['last_check'] = int(time.time())
            if use_plaintext:
                _local_cache['use_plaintext'] = True
            else:
                _local_cache['use_plaintext'] = False

        profile_data = rec.get_profile_data()

        if _local_cache['use_plaintext']:
            profile_calls = _split_profile(profile_data['calls'], 100)
        else:
            profile_calls = _split_profile(profile_data['calls'], 800)

        profile_data['calls'] = profile_calls.pop(0)['calls']

        logging.info("PROFILE: %s",
                     profile_data
                     if _local_cache['use_plaintext'] else
                     base64.b64encode(zlib.compress(json.dumps(profile_data))))

        for more_calls in profile_calls:
            logging.info("PROFILE: %s",
                         profile_data
                         if _local_cache['use_plaintext'] else
                         base64.b64encode(
                             zlib.compress(json.dumps(more_calls))))

    recorder_proxy.clear_for_current_request()


def _split_profile(profile, size):
    return [{'calls':profile[x:x+size]} for x in xrange(0, len(profile), size)]