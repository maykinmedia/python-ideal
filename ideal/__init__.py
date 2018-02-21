# -*- coding: utf-8 -*-
"""Implementation of the iDEAL v3.3.1 specification in Python."""
# :copyright: (c) 2013-2018, Maykin Media B.V.
#             All rights reserved.
# :license:   MIT, see LICENSE for more details.

from __future__ import absolute_import, unicode_literals, unicode_literals

import re

from collections import namedtuple

__version__ = '0.3.0'
__author__ = 'Joeri Bekker'
__contact__ = 'joeri@maykinmedia.nl'
__homepage__ = 'https://github.com/maykinmedia/python-ideal'
__docformat__ = 'restructuredtext'

# -eof meta-

version_info_t = namedtuple('version_info_t', (
    'major', 'minor', 'patch', 'releaselevel', 'serial',
))

# bumpversion can only search for {current_version}
# so we have to parse the version here.
_temp = re.match(
    r'(\d+)\.(\d+).(\d+)(.+)?', __version__).groups()
VERSION = version_info = version_info_t(
    int(_temp[0]), int(_temp[1]), int(_temp[2]), _temp[3] or '', '')
del(_temp)
del(re)
