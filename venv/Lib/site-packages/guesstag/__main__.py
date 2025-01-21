#!/usr/bin/env python3

"""An entry-point that allows the module to be executed.
This also simplifies the distribution as this is the
entry-point for the console script (see setup.py).
"""

import sys
from .guesstag import main as guesstag_main


def main():
    """The entry-point of the component."""
    return guesstag_main()


if __name__ == '__main__':
    sys.exit(main())
