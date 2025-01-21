#!/usr/bin/env python3

# -----------------------------------------------------------------------------
# Copyright (C) 2018 Alan Christie.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
# -----------------------------------------------------------------------------

"""A simple utility to 'guess' the next GitLab CI tag value.

This utility gets the nearest tag and, if found to be sensible,
this utility prints what it estimates to be the next version.

If the environment variable `CI_COMMIT_TAG` is defined (which is normal
for tagged builds) this utility simply returns (prints) the defined value -
i.e. on tagged builds this utility prints the tag.

If a tag cannot be found the utility will return the value
defined in the pyconf.yml file or, if it cannot be found, '0.0.0'.
"""

import os
import re
import subprocess

import yaml

# The Yaml configuration file
CONFIG_FILE = 'pyconf.yml'
# The anticipated `pyconf` variable, used to _seed_ the
# returned version number when no tag is found. If the
# pyconf file or its variable cannot be found `guesstag`
# uses the default format (M.M.P)
PYCONF_DEBUT_VARIABLE = 'BASE_TAG_VERSION'
# The command to get the most recent (annotated) tag
# reachable from a commit.
GIT_CMD = 'git describe --abbrev=0'
# Fall-back version (used if all else fails)
FALLBACK_VERSION = [0, 0, 0]
# The debut version.
# By default this is an invalid number (0.0.0).
# It is set to the pyconf config value (if found).
debut_version = FALLBACK_VERSION


# -----------------------------------------------------------------------------
# _try_to_decompose_version
# -----------------------------------------------------------------------------
def _try_to_decompose_version(version_str):
    """Tries to decompose a version string. The version format
    uses 2 or 3 digits plus a possible suffix. The suffix, i.e. the
    ``a1`` in ``1.2.3a1`` can begin ``-``, ``a``, ``b`` or ``c``.

    Version numbers cannot legitimately begin with '0'.

    :param version_str: The version string
    :type version_str: ``string``
    :return: None or a list of 2 or 3 digits
    :rtype: ``list``
    """

    assert isinstance(version_str, str)

    # Version is 2 or 3 numbers separated by a period.
    # returns None or a list of size 2 or 3.
    #
    # See 'CODING-STANDARDS-VERSION-NUMBERS.md` for a formal declaration
    # of our version numbering scheme.
    bits = version_str.split('.')

    # Must have 2 or 3 fields...
    if len(bits) not in [2, 3]:
        # Invalid version number, return None
        return None

    # Parts cannot be empty or start or end with space
    # or start with '0' if length is greater than 1.

    for bit in bits:
        if len(bit) == 0:
            return None
        lean_bit = bit.strip()
        if len(lean_bit) != len(bit):
            return None

    # Major must be a number.
    # There are Major & Minor for both the 'm.m.p' and 'y.m' formats.
    try:
        major = int(bits[0])
    except ValueError:
        return None

    if len(bits) == 2:

        # Format is '\d+\.\d+`. Where the first part is the year
        # typically 2018 or 18) and the 2nd is just a number.
        # Take any suffix away from the sub-year number
        # and insist that whatever sits in front of the suffix is a number...
        sub_year = bits[1]
        suffix = re.search('[-abc]', sub_year)
        if suffix:
            sub_year = sub_year[:suffix.start()]
        try:
            sub_year = int(sub_year)
        except ValueError:
            return None
        return [major, sub_year]

    else:

        # 3-digit version.
        # This (2nd position) is therefore the 'minor' part.
        try:
            minor = int(bits[1])
        except ValueError:
            return None

    # If we get here it's a 3-digit version number...

    # Take any suffix away from the patch number
    # and insist that whatever sits in front of the suffix is a number...
    patch = bits[2]
    suffix = re.search('[-abc]', patch)
    if suffix:
        patch = patch[:suffix.start()]
    try:
        patch = int(patch)
    except ValueError:
        return None

    return [major, minor, patch]


# -----------------------------------------------------------------------------
# _try_to_set_debut_version
# -----------------------------------------------------------------------------
def _try_to_set_debut_version(config_file):
    """Attempts to get debut (pre-tag) version and format from the
    supplied YAML configuration file. If found the global variables
    tag_format and debut_version ar changed to reflect the content of the
    ``PYCONF_DEBUT_VARIABLE`` value. If the file is not found or the variable
    does not exist the global variables are not modified.

    :param config_file: The (YAML) configuration file.
    :type config_file: ``string``
    :return: The new debut version (also a global variable)
    :rtype: ``list``
    """

    global debut_version

    # Reset debut version
    # (needed for tests where prior tests can corrupt the initial value)
    debut_version = FALLBACK_VERSION

    config = {}
    if os.path.isfile(config_file):
        with open(config_file, 'r') as fabric_stream:
            try:
                config = yaml.load(fabric_stream)
            except yaml.YAMLError:
                # Problems with the file.
                # Just continue (config will be empty)
                pass

    # Did we find YAML data?
    if config:
        config_version = debut_version
        got_config_version = False
        try:
            config_version = str(config['variables'][PYCONF_DEBUT_VARIABLE])
            got_config_version = True
        except KeyError:
            # No variable or value.
            # Don't care - got_config_version will remain False
            pass
        # If the YAML config variable was found,
        # is its value a valid version number?
        if got_config_version:
            version_bits = _try_to_decompose_version(config_version)
            if version_bits:
                debut_version = version_bits

    return debut_version


# -----------------------------------------------------------------------------
# _guess_tag
# -----------------------------------------------------------------------------
def _guess_tag():

    # Return the CI tag it it's defined.
    ci_commit_tag = os.environ.get('CI_COMMIT_TAG')
    if ci_commit_tag and ci_commit_tag.strip():
        return ci_commit_tag.strip()

    # Is there a 'debut' version in the config file?
    # If so we'll use this when no tag can be found...
    _try_to_set_debut_version(CONFIG_FILE)

    # ...`run` the GIT_CMD and inspect its `stdout`
    cp = subprocess.run(GIT_CMD.split(),
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE)
    last_tag = cp.stdout.decode("utf-8").strip()

    # Try to decompose the Git tag (it might be invalid or empty).
    # If invalid or empty we'll get None back and therefore
    # just return end up returning the `debut_version` (see below).
    version = _try_to_decompose_version(last_tag)

    # If we have a version from Git then increment the value,
    # otherwise return the debut version.
    if version:

        # Found a tag.
        # Return the tag + 1.
        if len(version) == 3:
            ret_val = '{}.{}.{}'.format(version[0], version[1], version[2] + 1)
        else:
            ret_val = '{}.{}'.format(version[0], version[1] + 1)

    else:

        # Debut version - return 'as is'.
        # This is either the FALLBACK_VALUE
        # or whatever was found in the YAML file
        if len(debut_version) == 3:
            ret_val = '{}.{}.{}'.format(debut_version[0],
                                        debut_version[1],
                                        debut_version[2])
        else:
            ret_val = '{}.{}'.format(debut_version[0], debut_version[1])

    return ret_val


# -----------------------------------------------------------------------------
# main
# -----------------------------------------------------------------------------
def main():
    """The console script entry-point. Called when guesstag is executed
    or from __main__.py, which is used by the installed console script.

    Here we simply print the result so the user can do somethign like
    TAG = `guesstag` from the shell.
    """
    print(_guess_tag())


# -----------------------------------------------------------------------------
# MAIN
# -----------------------------------------------------------------------------
if __name__ == '__main__':
    main()
