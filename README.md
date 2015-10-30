# Superslacker 

Superslacker is a plugin utility that sends events from
processes that run under [supervisor](http://supervisord.org)
to [Slack](https://slack.com).


## Installation

```
pip install superslacker
```

## Configuration

```
[eventlistener:fatalslacker]
command=fatalslack --token="slacktoken-slacktoken-slacktoken" --channel="#notifications" --hostname="HOST"
events=PROCESS_STATE,TICK_60
```

