#!/usr/bin/env python
# -*- coding: utf-8 -*-
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

"""
Usage: superslacker [-t token] [-c channel] [-n hostname] [-w webhook] [-a attachment]

Options:
  -h, --help            show this help message and exit
  -t TOKEN, --token=TOKEN
                        Slack Token
  -c CHANNEL, --channel=CHANNEL
                        Slack Channel
  -w WEBHOOK, --webhook=WEBHOOK
                        Slack WebHook URL
  -a ATTACHMENT, --attachment=ATTACHMENT
                        Slack Attachment text
  -n HOSTNAME, --hostname=HOSTNAME
                        System Hostname
"""

import copy
import os
import sys

from slacker import Slacker, IncomingWebhook
from superlance.process_state_monitor import ProcessStateMonitor
from supervisor import childutils


class SuperSlacker(ProcessStateMonitor):
    process_state_events = ['PROCESS_STATE_FATAL']

    @classmethod
    def _get_opt_parser(cls):
        from optparse import OptionParser

        parser = OptionParser()
        parser.add_option("-t", "--token", help="Slack Token")
        parser.add_option("-c", "--channel", help="Slack Channel")
        parser.add_option("-w", "--webhook", help="Slack WebHook URL")
        parser.add_option("-a", "--attachment", help="Slack Attachment text")
        parser.add_option("-n", "--hostname", help="System Hostname")

        return parser

    @classmethod
    def parse_cmd_line_options(cls):
        parser = cls._get_opt_parser()
        (options, args) = parser.parse_args()
        return options

    @classmethod
    def validate_cmd_line_options(cls, options):
        parser = cls._get_opt_parser()
        if not options.token and not options.webhook:
            parser.print_help()
            sys.exit(1)
        if options.token and options.webhook:
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
        self.channel = kwargs['channel']
        self.token = kwargs.get('token', None)
        self.now = kwargs.get('now', None)
        self.hostname = kwargs.get('hostname', None)
        self.webhook = kwargs.get('webhook', None)
        self.attachment = kwargs.get('attachment', None)

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
            'webhook': self.webhook,
            'channel': self.channel,
            'attachment': self.attachment,
            'messages': self.batchmsgs
        }

    def send_message(self, message):
        for msg in message['messages']:
            payload = {
                'channel': message['channel'],
                'text': msg,
                'username': 'superslacker',
                'icon_emoji': ':sos:',
                'link_names': 1,
                'attachments': [{"text": message['attachment'], "color": "danger"}]
            }
            if message['webhook']:
                webhook = IncomingWebhook(url=message['webhook'])
                webhook.post(data=payload)
            if message['token']:
                slack = Slacker(token=message['token'])
                slack.chat.post_message(**payload)


def main():
    superslacker = SuperSlacker.create_from_cmd_line()
    superslacker.run()


def fatalslack():
    superslacker = SuperSlacker.create_from_cmd_line()
    superslacker.write_stderr('fatalslack is deprecated. Please use superslack instead\n')
    superslacker.run()


if __name__ == '__main__':
    main()
