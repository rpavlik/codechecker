# -------------------------------------------------------------------------
#                     The CodeChecker Infrastructure
#   This file is distributed under the University of Illinois Open Source
#   License. See LICENSE.TXT for details.
# -------------------------------------------------------------------------
"""
Util module.
"""
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

import io
import json
import os

import portalocker

from codechecker_common.logger import get_logger

LOG = get_logger('system')


def arg_match(options, args):
    """Checks and selects the option string specified in 'options'
    that are present in parameter 'args'."""
    matched_args = []
    for option in options:
        if any([arg if option.startswith(arg) else None
                for arg in args]):
            matched_args.append(option)
            continue

    return matched_args


def get_line(file_name, line_no, errors='ignore'):
    """
    Return the given line from the file. If line_no is larger than the number
    of lines in the file then empty string returns.
    If the file can't be opened for read, the function also returns empty
    string.

    Try to encode every file as utf-8 to read the line content do not depend
    on the platform settings. By default locale.getpreferredencoding() is used
    which depends on the platform.

    Changing the encoding error handling can influence the hash content!
    """
    try:
        with io.open(file_name, mode='r',
                     encoding='utf-8',
                     errors=errors) as source_file:
            for line in source_file:
                line_no -= 1
                if line_no == 0:
                    return line
            return u''
    except IOError:
        LOG.error("Failed to open file %s", file_name)
        return u''


def load_json_or_empty(path, default=None, kind=None, lock=False):
    """
    Load the contents of the given file as a JSON and return it's value,
    or default if the file can't be loaded.
    """

    ret = default
    try:
        with io.open(path, 'r') as handle:
            if lock:
                portalocker.lock(handle, portalocker.LOCK_SH)

            ret = json.loads(handle.read())

            if lock:
                portalocker.unlock(handle)
    except IOError as ex:
        LOG.warning("Failed to open %s file: %s",
                    kind if kind else 'json',
                    path)
        LOG.warning(ex)
    except OSError as ex:
        LOG.warning("Failed to open %s file: %s",
                    kind if kind else 'json',
                    path)
        LOG.warning(ex)
    except ValueError as ex:
        LOG.warning("'%s' is not a valid %s file.",
                    kind if kind else 'json',
                    path)
        LOG.warning(ex)
    except TypeError as ex:
        LOG.warning('Failed to process json file: %s', path)
        LOG.warning(ex)

    return ret


def get_last_mod_time(file_path):
    """
    Return the last modification time of a file.
    """
    try:
        return os.stat(file_path).st_mtime
    except OSError as oerr:
        LOG.debug(oerr)
        LOG.debug("File is missing")
        return None


def trim_path_prefixes(path, prefixes):
    """
    Removes the longest matching leading path from the file path.
    """

    # If no prefixes are specified.
    if not prefixes:
        return path

    # Find the longest matching prefix in the path.
    longest_matching_prefix = None
    for prefix in prefixes:
        if not prefix.endswith('/'):
            prefix += '/'

        if path.startswith(prefix) and (not longest_matching_prefix or
                                        longest_matching_prefix < prefix):
            longest_matching_prefix = prefix

    # If no prefix found or the longest prefix is the root do not trim the
    # path.
    if not longest_matching_prefix or longest_matching_prefix == '/':
        return path

    return path[len(longest_matching_prefix):]
