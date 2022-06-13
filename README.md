# Superslacker

Superslacker is a supervisor "event listener" that sends events from processes that run under [supervisor](http://supervisord.org) to [Slack](https://slack.com). When `superslacker` receives an event, it sends a message notification to a configured `Slack` channel.

`superslacker` uses [Slacker](https://github.com/os/slacker) full-featured Python interface for the Slack API.

## Installation

```
pip install superslacker
```

## Command-Line Syntax

```bash
$ superslacker [-t token] [-c channel] [-n hostname] [-w webhook] [-a attachment] [-e events] [-p proxy] [--eventname eventname] [--interval interval] [--blacklist apps] [--whitelist apps]
```

### Options

```-t TOKEN, --token=TOKEN```

Post a message to Slack using Slack Web API. In order to be able to send messages to Slack, you need to generate your `token` by registering your application. More info can be found [here](https://api.slack.com/web)

```-c CHANNEL, --channel=CHANNEL```

`#channel` to fill with your crash messages.

```-n HOSTNAME, --hostname=HOSTNAME```

Name or identificator of the machine where the events are been generated. This goes in the event message.

```-w WEBHOOK, --webhook=WEBHOOK```

Post a message to Slack using Slack Incoming WebHook. In order to be able to send messages to Slack, you need to configure an `Incoming WebHook` for your Slack account. More info can be found [here](https://api.slack.com/incoming-webhooks)

```-e EVENTS, --event=EVENTS```

The Supervisor Process State event(s) to listen for. It can be any, one of, or all of
STARTING, RUNNING, BACKOFF, STOPPING, EXITED, STOPPED, UNKNOWN.

```-p PROXY, --proxy=PROXY```

If you server with supervisord is behind proxy

```-i ICON_EMOJI, --icon=ICON_EMOJI```

To customize the Slackmoji to be used as icon. Defaults to `:sos:`.

```-u USERNAME, --username=USERNAME```

To customize the Slack username. Defaults to `superslacker`.

```-eventname=EVENTNAME```

How often to check changes. TICK_5 or TICK_60. Default TICK_60.

```--interval=INTERVAL```

How often to flush message queue. Default 60 sec.

```--blacklist=apps```

List of applications to ignore (support keyword "ALL")

```--whitelist=apps```

List of applications always to monitor with all events (support keyword "ALL". Take priority over blacklist)




## Notes

:ghost: gonna be used as an icon for the message and `superslacker` as a username. 


## Configuration
An `[eventlistener:x]` section must be placed in `supervisord.conf` in order for `superslacker` to do its work. See the “Events” chapter in the Supervisor manual for more information about event listeners.

The following example assume that `superslacker` is on your system `PATH`.


```
[eventlistener:superslacker]
command=superslacker --token="slacktoken-slacktoken-slacktoken" --channel="#notifications" --hostname="HOST" --events="UNKNOWN,STOPPING"
events=PROCESS_STATE,TICK_60
```

