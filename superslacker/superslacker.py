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
Usage: superslacker [-t token] [-c channel] [-n hostname] [-w webhook] [-e events] [-p proxy] [--eventname TICK_x] [--interval interval] [--blacklist apps ] [--whitelist apps]

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
  --eventname=eventname
                        How often to check process states (TICK_5 or TICK_60). Default TICK_5
  --interval=interval
                        How often to flush message queue (in seconds). Default 60
  -e EVENTS, --events=EVENTS
                        Supervisor process state event(s)
  --blacklist=apps
                        List of applications to ignore                      
  --whitelist=apps
                        List of applications always monitoring (all events)
  -p PROXY, --proxy=PROXY
                        Proxy Server
"""

import copy
import os
import sys
import json

from slack import WebClient, WebhookClient
from superlance.process_state_monitor import ProcessStateMonitor
from supervisor import childutils


class SuperSlacker(ProcessStateMonitor):
    SUPERVISOR_EVENTS = (
        'STARTING', 'RUNNING', 'BACKOFF', 'STOPPING',
        'FATAL', 'EXITED', 'STOPPED', 'UNKNOWN',
    )

    EVENTS_SLACK_COLORS = {
        "PROCESS_STATE_STOPPED": ':apple:',
        "PROCESS_STATE_STARTING": ':warning:',
        "PROCESS_STATE_RUNNING": ':green_apple:',
        "PROCESS_STATE_BACKOFF": ':apple:',
        "PROCESS_STATE_STOPPING": ':apple:',
        "PROCESS_STATE_EXITED": ':apple:',
        "PROCESS_STATE_FATAL": ':apple:',
        "PROCESS_STATE_UNKNOWN": ':apple:',
    }

    EVENTS_SHORT_NAMES = {
        "PROCESS_STATE_STOPPED": 'STOPPED',
        "PROCESS_STATE_STARTING": 'STARTING',
        "PROCESS_STATE_RUNNING": 'RUNNING',
        "PROCESS_STATE_BACKOFF": 'BACKOFF',
        "PROCESS_STATE_STOPPING": 'STOPPING',
        "PROCESS_STATE_EXITED": 'EXITED',
        "PROCESS_STATE_FATAL": 'FATAL',
        "PROCESS_STATE_UNKNOWN": 'UNKNOWN',
    }

    @classmethod
    def _get_opt_parser(cls):
        from optparse import OptionParser

        parser = OptionParser()
        parser.add_option("-t", "--token", help="Slack Token")
        parser.add_option("-c", "--channel", help="Slack Channel")
        parser.add_option("-w", "--webhook", help="Slack WebHook URL")
        parser.add_option("-i", "--icon", default=':sos:',
                          help="Slack emoji to be used as icon")
        parser.add_option("-u", "--username",
                          default='superslacker', help="Slack username")
        parser.add_option("-n", "--hostname", help="System Hostname")
        parser.add_option("-p", "--proxy", help="Proxy server")
        parser.add_option(
            "--eventname", default="TICK_60", help="TICK_5 or TICK_60. Default TICK_60. How often to add messages into queue")
        parser.add_option(
            "--interval", default=60, help="How often to flush message queue. Default 60sec")
        parser.add_option(
            "-e", "--events", help="Supervisor event(s). Can be any, some or all of {} as comma separated values".format(cls.SUPERVISOR_EVENTS))
        parser.add_option(
            "--blacklist", help="Comma-separated list of application for which not to send notifiactions")
        parser.add_option(
            "--whitelist", help="Comma-separated list of application always to monitor")

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
        self.proxy = kwargs.get('proxy', None)
        self.icon = kwargs.get('icon')
        self.username = kwargs.get('username')
        self.eventname = kwargs.get('eventname', "TICK_5")
        self.interval = float(kwargs.get('interval', 60))/60
        self.process_state_events = ['PROCESS_STATE_{}'.format(status)
                                     for status in self.SUPERVISOR_EVENTS]

        if kwargs.get('events'):
            self.process_filter_events = [
                'PROCESS_STATE_{}'.format(e.strip().upper())
                for e in kwargs.get('events', None).split(",")
                if e in self.SUPERVISOR_EVENTS
            ]
        else:
            self.process_filter_events = self.process_state_events

        if kwargs.get('blacklist'):
            self.process_blacklist = [
                '{}'.format(e.strip())
                for e in kwargs.get('blacklist', None).split(",")
            ]
        else:
            self.process_blacklist = []

        if kwargs.get('whitelist'):
            self.process_whitelist = [
                '{}'.format(e.strip())
                for e in kwargs.get('whitelist', None).split(",")
            ]
        else:
            self.process_whitelist = []

    def get_process_state_change_msg(self, headers, payload):
        pheaders, pdata = childutils.eventdata(payload + '\n')
        return "{hostname};{groupname}:{processname};{from_state};{event}".format(
            hostname=self.hostname, event=headers['eventname'], **pheaders
        )

    def send_slack_notification(self, processname, hostname, eventname, from_state):
        payload = {
            'channel': self.channel,
            'username': self.username,
            'icon_emoji': self.icon,
            'blocks': [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "{4} *{0}* @{1}: *{2}* from {3}".format(processname,
                                                                        hostname,
                                                                        self.EVENTS_SHORT_NAMES[eventname],
                                                                        from_state,
                                                                        self.EVENTS_SLACK_COLORS[eventname])
                    }
                }
            ]
        }
        if self.webhook:
            webhook = WebhookClient(url=self.webhook, proxy=self.proxy)
            webhook.send_dict(body=payload)
        elif self.token:
            slack = WebClient(token=self.token, proxy=self.proxy)
            slack.chat_postMessage(**payload)

    def send_batch_notification(self):
        for msg in self.batchmsgs:
            hostname, processname, from_state, eventname = msg.rsplit(';')
            processname = processname.split(":")[0]
            if processname in self.process_whitelist or "all".lower() in [x.lower() for x in self.process_whitelist]:
                self.send_slack_notification(
                    processname, hostname, eventname, from_state)
            elif processname in self.process_blacklist or "all".lower() in [x.lower() for x in self.process_blacklist]:
                return
            else:
                if eventname in self.process_filter_events:
                    self.send_slack_notification(
                        processname, hostname, eventname, from_state)


def main():
    superslacker = SuperSlacker.create_from_cmd_line()
    superslacker.run()


if __name__ == '__main__':
    main()
