"""
Representations of Panels and their templates.

.. moduleauthor:: Scott Petersen <scott@nutech.com>
"""

ADEMCO = 0
DSC = 1

MODES = {
    'A': ADEMCO,
    'D': DSC,
}

VISTA20 = 0

TEMPLATES = {
    VISTA20: {
        'name': 'Vista 20',
        # number of expanders, starting_address, number of channels
        'expanders': (5, 7, 7)
    }
}
