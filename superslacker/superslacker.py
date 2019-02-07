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
Usage: superslacker [-t token] [-c channel] [-n hostname] [-w webhook] [-e events]

Options:
  -h, --help            show this help message and exit
  -t TOKEN, --token=TOKEN
                        Slack Token
  -c CHANNEL, --channel=CHANNEL
                        Slack Channel
  -w WEBHOOK, --webhook=WEBHOOK
                        Slack WebHook URL
  -i ICON_EMOJI, --icon=ICON_EMOJI
                        Slack emoji to be used as icon
  -u USERNAME, --username=USERNAME
                        Slack username
  -n HOSTNAME, --hostname=HOSTNAME
                        System Hostname
  -e EVENTS, --events=EVENTS
                        Supervisor process state event(s)
"""

import copy
import os
import sys

from slacker import Slacker, IncomingWebhook
from superlance.process_state_monitor import ProcessStateMonitor
from supervisor import childutils


class SuperSlacker(ProcessStateMonitor):
    SUPERVISOR_EVENTS = (
        'STARTING', 'RUNNING', 'BACKOFF', 'STOPPING',
        'FATAL', 'EXITED', 'STOPPED', 'UNKNOWN',
    )

    EVENTS_SLACK_COLORS = {
        "PROCESS_STATE_STOPPED": 'danger',
        "PROCESS_STATE_STARTING": 'warning',
        "PROCESS_STATE_RUNNING": 'good',
        "PROCESS_STATE_BACKOFF": 'danger',
        "PROCESS_STATE_STOPPING": 'danger',
        "PROCESS_STATE_EXITED": 'danger',
        "PROCESS_STATE_FATAL": 'danger',
        "PROCESS_STATE_UNKNOWN": 'danger',
    }

    @classmethod
    def _get_opt_parser(cls):
        from optparse import OptionParser

        parser = OptionParser()
        parser.add_option("-t", "--token", help="Slack Token")
        parser.add_option("-c", "--channel", help="Slack Channel")
        parser.add_option("-w", "--webhook", help="Slack WebHook URL")
        parser.add_option("-i", "--icon", default=':sos:', help="Slack emoji to be used as icon")
        parser.add_option("-u", "--username", default='superslacker', help="Slack username")
        parser.add_option("-n", "--hostname", help="System Hostname")
        parser.add_option("-e", "--events", help="Supervisor event(s). Can be any, some or all of {} as comma separated values".format(cls.SUPERVISOR_EVENTS))

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
        self.icon = kwargs.get('icon')
        self.username = kwargs.get('username')
        events = kwargs.get('events', None)
        self.process_state_events = [
            'PROCESS_STATE_{}'.format(e.strip().upper())
            for e in kwargs.get('events', None).split(",")
            if e in self.SUPERVISOR_EVENTS
        ]

    def get_process_state_change_msg(self, headers, payload):
        pheaders, pdata = childutils.eventdata(payload + '\n')
        return "{hostname};{groupname}:{processname};{from_state};{event}".format(
            hostname=self.hostname, event=headers['eventname'], **pheaders
        )

    def send_batch_notification(self):
        for msg in self.batchmsgs:
            hostname, processname, from_state, eventname = msg.rsplit(';')
            payload = {
                'channel': self.channel,
                'username': self.username,
                'icon_emoji': self.icon,
                'attachments': [
                    {
                        'fallback': msg,
                        "color": self.EVENTS_SLACK_COLORS[eventname],
                        "pretext": "Supervisor event",
                        'fields': [
                            {
                                "title": "Hostname",
                                "value": hostname,
                                "short": True,
                            },
                            {
                                "title": "Process",
                                "value": processname,
                                "short": True,
                            },
                            {
                                "title": "From state",
                                "value": from_state,
                                "short": True,
                            },
                            {
                                "title": "Event",
                                "value": eventname,
                                "short": True,
                            },
                        ]
                    }
                ]
            }
            if self.webhook:
                webhook = IncomingWebhook(url=self.webhook)
                webhook.post(data=payload)
            elif self.token:
                slack = Slacker(token=self.token)
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
