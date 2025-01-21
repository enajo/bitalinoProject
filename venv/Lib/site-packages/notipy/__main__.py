#!/usr/bin/env python
from __future__ import absolute_import, division, print_function
from __future__ import unicode_literals

import sys

from notipy.cli import Notipy


def main(args=None):
    if args is None:
        args = sys.argv[1:]

    if len(args) >= 1:
        if len(args) == 1:
            message = args[0]
        else:
            message = ' '.join(args)

        Notipy().send(message)

    return 0


if __name__ == "__main__":
    sys.exit(main())
