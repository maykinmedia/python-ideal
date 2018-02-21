import os
import re
from io import open

IDEAL_NAMESPACES = {
    'ideal': 'http://www.idealdesk.com/ideal/messages/mer-acq/3.3.1',
    'xmldsig': 'http://www.w3.org/2000/09/xmldsig#',
}


def render_to_string(template_file, ctx):
    f = open(os.path.abspath(os.path.join(os.path.dirname(__file__), template_file)), 'r')
    data = f.read()
    f.close()

    data = data.format(**ctx)

    return data


def convert_camelcase(name):
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()
