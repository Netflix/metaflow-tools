
# Event Lifecycle of Bot
![](images/slack-bot-event-lifecycle.jpg)

The `MFBServer` listens to events from slack via `MFBSlackClientV2`and converts then to internal event representation. These events are matched with rules to and based on the matched rules an action is invoked.

In the above event lifecycle, the `metaflowbot` uses Slack as a stateful store for storing context about threads. When the Bot detects a `state_change` event, its stores its contents in the `MFBState` [Object](../metaflowbot/state.py).
## Event Lifecycle Psuedo Code
```python

while server runs forever: # metaflowbot.server.MFBServer
	- foreach event from  slack: # metaflowbot.slack_client.MFBSlackClientV2
		- convert events to MFBot Compatible events: # metaflowbot.server._make_events
            - if event matches rules # metaflowbot.rules.MFBRules
                - apply action matches by rule # metaflowbot.server.actions
                # Every action is invoked as a seperate python process.
```

## Events

### `lost_process`
> Event created when processed dead processes are detected **(?)**
### `new_thread`
> When a completely new thread is created
### `user_message`
> When a user messages on a thread
