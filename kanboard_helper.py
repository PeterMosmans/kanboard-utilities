#!/usr/bin/env python

"""
kanboard helper - show kanboard items

Copyright (C) 2016 Peter Mosmans [Go Forward]
This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.
"""

from __future__ import print_function

import argparse
from datetime import date
import logging
import re
import sys
import textwrap

import requests
from kanboard import Kanboard


VERSION = 0.1


def list_descriptions(tasks, options):
    """
    List description of all tasks (in column_id)
    """
    for task in tasks:
        if not options['column'] or (task['column_id'] == options['column']):
            task_id = task['id']
            title = task['title']
            modification = date.fromtimestamp(float(task['date_modification']))
            logging.warning('%s - last modified %s - %s', title, modification, task_id)
            logging.warning(task['description'])


def get_tasks(options):
    """
    Return a list of tasks from the specified kanboard
    """
    tasks = None
    print(options)
    kanboard = Kanboard(options['host'] + "/jsonrpc.php", username=options['username'],
                        password=options['password'], http_username=options['http_username'],
                        http_password=options['http_password'], proxies=options['proxy'],
                        verify=(not options['no_ssl_verify']), auth_header=options['auth_header'])
    try:
        tasks = kanboard.get_all_tasks(project_id=options['tasks'])
    except requests.exceptions.RequestException as exception:
        logging.error('Could not retrieve tasks: %s', exception)
        sys.exit(-1)
    except requests.packages.urllib3.exceptions.LocationParseError as exception:
        logging.error('Could not parse address: %s', exception)
    return tasks


def parse_arguments(banner):
    """
    Parse command line arguments.
    """
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=textwrap.dedent(banner + '''\
 - show kanboard items


Copyright (C) 2016  Peter Mosmans [Go Forward]
This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.'''))
    parser.add_argument('--auth-header', action='store',
                        help='Kanboard HTTP Authentication header')
    parser.add_argument('-c', '--config', action='store',
                        help='Load configuration file')
    parser.add_argument('--column', action='store', type=str, metavar='COLUMN_ID',
                        help='Show only items from specified column')
    parser.add_argument('--debug', action='store_true',
                        help='Show debug information')
    parser.add_argument('--host', action='store',
                        help='Hostname, including protocol')
    parser.add_argument('--http-password', action='store',
                        help='HTTP Auth password')
    parser.add_argument('--http-username', action='store',
                        help='HTTP Auth username')
    parser.add_argument('-p', '--password', action='store',
                        help='Kanboard password')
    parser.add_argument('--proxy', action='store',
                        help='Proxy server')
    parser.add_argument('--tasks', action='store', type=int, metavar='KANBOARD_ID',
                        help='Retrieve items from kanboard')
    parser.add_argument('-u', '--username', action='store',
                        help='Kanboard username')
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='Be more verbose')
    parser.add_argument('--no-ssl-verify', action='store_true',
                        help='Do NOT verify SSL certificate')
    return vars(parser.parse_args())


def preflight_checks(options):
    """
    Performs checks whether @options contain valid options.
    """
    if not options['host']:
        logging.error('No host specified')
        sys.exit(-1)
    if options['proxy']:
        options['proxy'] = {'http': options['proxy'], 'https': options['proxy']}
    else:
        options['proxy'] = {}


def read_config(options):
    """
    Read parameters from @options['config'],  but doesn't overwrite non-empty
    @options parameters.

    Returns: an array of options.
    """
    filename = options['config']
    if not filename:
        return options
    try:
        with open(filename, 'r') as config_file:
            contents = config_file.read()
            for key in ['auth_header', 'host', 'http_password', 'http_username',
                        'no_ssl_verify', 'password', 'proxy', 'username']:
                if not options[key]:
                    if contents and re.findall(r'(?:^|\n){0}:\s?(.*)'.format(key), contents):
                        options[key] = re.findall(r'(?:^|\n){0}:\s?(.*)'.format(key),
                                                  contents)[0]
                    if options[key] and options[key].lower() == 'false':
                        options[key] = False
        logging.debug(options)
    except IOError as exception:
        logging.error('Could not open configuration file %s: %s', filename, exception)
    except IndexError as exception:
        logging.error('Missing variables in %s', filename)
    return options


def setup_logging(options):
    """
    Set up loghandlers according to options.
    """
    # DEBUG = verbose status messages
    # INFO = status messages
    # WARNING = output
    # ERROR = error messages
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    console = logging.StreamHandler(stream=sys.stdout)
    console.setFormatter(logging.Formatter('%(message)s'))
    if options['debug']:
        console.setLevel(logging.DEBUG)
    else:
        if options['verbose']:
            console.setLevel(logging.INFO)
        else:
            logger.setLevel(logging.WARNING)
    logger.addHandler(console)


def main():
    """
    Main program loop.
    """
    banner = 'kanboard_helper version {0}'.format(VERSION)
    options = (parse_arguments(banner))
    setup_logging(options)
    options = read_config(options)
    preflight_checks(options)
    logging.info(banner + ' starting')
    if options['tasks']:
        tasks = get_tasks(options)
        list_descriptions(tasks, options)
    sys.exit(0)


if __name__ == "__main__":
    main()
