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
"""This is a simple test handle that makes several RPCs to ensure the recorder
and middleware work as expected.
"""

import webapp2

from google.appengine.api import memcache

from appstats_logger.middleware import stats_logger_wsgi_middleware


class HelloHandler(webapp2.RequestHandler):
    """Make some RPCs so we can check the profiling data."""
    def get(self):
        self.test_memcache()
        self.test_memcache()

        memcache.set_multi({'key': 'value', 'other': 'value'})
        memcache.get_multi(['key', 'other', 'thing'])

        self.response.out.write('Hello world')

    def test_memcache(self):
        memcache.set('key', 'value')
        memcache.get('key')


app = webapp2.WSGIApplication([
    ('/', HelloHandler),
])

app = stats_logger_wsgi_middleware(app)


