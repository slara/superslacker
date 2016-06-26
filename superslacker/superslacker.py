#!/usr/bin/env python
##############################################################################
#
# Copyright (c) 2007 Agendaless Consulting and Contributors.
# All Rights Reserved.
#
# Copyright (c) 2015 MTSolutions S.A.
#
# This software is subject to the provisions of the BSD-like license at
# http://www.repoze.org/LICENSE.txt.  A copy of the license should accompany
# this distribution.  THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL
# EXPRESS OR IMPLIED WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO,
# THE IMPLIED WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND
# FITNESS FOR A PARTICULAR PURPOSE
#
##############################################################################

# A event listener meant to be subscribed to PROCESS_STATE_CHANGE
# events.  It will send slack messages when processes that are children of
# supervisord transition unexpectedly to the EXITED state.

# A supervisor config snippet that tells supervisor to use this script
# as a listener is below.
#
# [eventlistener:superslacker]
# command=python superslacker
# events=PROCESS_STATE,TICK_60

doc = """\
superslacker.py [--token=<Slack API Token>]
        [--channel=<slack channel>]

Options:

--token - User Slack Web API Token

--channel - the channel to send messages

A sample invocation:

superslacker.py --token="your-slack-api-token" --channel="#notifications"

"""
import os
import sys
import copy

from supervisor import childutils
from superlance.process_state_email_monitor import ProcessStateMonitor
from slacker import Slacker


class SuperSlacker(ProcessStateMonitor):

    process_state_events = ['PROCESS_STATE_FATAL']

    @classmethod
    def _get_opt_parser(cls):
        from optparse import OptionParser

        parser = OptionParser()
        parser.add_option("-t", "--token", dest="token", default="",
                          help="Slack Token")

        parser.add_option("-c", "--channel", dest="channel", default="",
                          help="Slack Channel")

        parser.add_option("-n", "--hostname", dest="hostname", default="",
                          help="System Hostname")
        return parser

    @classmethod
    def parse_cmd_line_options(cls):
        parser = cls._get_opt_parser()
        (options, args) = parser.parse_args()
        return options

    @classmethod
    def validate_cmd_line_options(cls, options):
        parser = cls._get_opt_parser()
        if not options.token:
            parser.print_help()
            sys.exit(1)
        if not options.channel:
            parser.print_help()
            sys.exit(1)
        if not options.hostname:
            import socket
            options.hostname = socket.gethostname()

        validated = copy.copy(options)
        return validated

    @classmethod
    def get_cmd_line_options(cls):
        return cls.validate_cmd_line_options(cls.parse_cmd_line_options())

    @classmethod
    def create_from_cmd_line(cls):
        options = cls.get_cmd_line_options()

        if 'SUPERVISOR_SERVER_URL' not in os.environ:
            sys.stderr.write('Must run as a supervisor event listener\n')
            sys.exit(1)

        return cls(**options.__dict__)

    def __init__(self, **kwargs):
        ProcessStateMonitor.__init__(self, **kwargs)
        self.token = kwargs['token']
        self.channel = kwargs['channel']
        self.now = kwargs.get('now', None)
        self.hostname = kwargs.get('hostname', None)

    def get_process_state_change_msg(self, headers, payload):
        pheaders, pdata = childutils.eventdata(payload + '\n')
        txt = ("[{0}] Process {groupname}:{processname} "
               "failed to start too many times".format(self.hostname, **pheaders))
        return txt

    def send_batch_notification(self):
        message = self.get_batch_message()
        if message:
            self.send_message(message)

    def get_batch_message(self):
        return {
            'token': self.token,
            'channel': self.channel,
            'messages': self.batchmsgs
        }

    def send_message(self, message):
        slack = Slacker(message['token'])
        for msg in message['messages']:
            slack.chat.post_message(message['channel'], msg)


def main():
    superslacker = SuperSlacker.create_from_cmd_line()
    superslacker.run()

def fatalslack():
    superslacker = SuperSlacker.create_from_cmd_line()
    superslacker.write_stderr('fatalslack is deprecated. Please use superslack instead\n')
    superslacker.run()


if __name__ == '__main__':
    main()
