"""
Parsing drone configuration
===========================

.. warning:: This module is a work in progress!

"""

import re

def parse(config):
  """Parse configuration strings as returned by the drone.

  >>> import json
  >>> cfg = '\\n'.join([
  ...   'GENERAL:foo = bar',
  ...   'VIDEO:enable = 1',
  ...   'GENERAL:buzz = quux',
  ...   'VIDEO:be_clever = TRUE',
  ...   'AUDIO:listen = -4',
  ... ])
  >>> parse(cfg) == { \
        'AUDIO': {'listen': '-4'}, \
        'VIDEO': {'enable': '1', 'be_clever': 'TRUE'}, \
        'GENERAL': {'foo': 'bar', 'buzz': 'quux'} \
      }
  True

  """
  lines = config.splitlines()
  line_parser = re.compile('^(\w+):(\w+)\s*=\s*(.*)$')
  rv = { }

  for line in lines:
    match = line_parser.match(line)
    if match is None:
      continue
    (section, key, value) = match.groups()
    if section not in rv:
      rv[section] = { }
    rv[section][key] = value
  
  return rv
