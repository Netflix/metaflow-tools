# Metaflow Bot

[slackclient](https://slack.dev/python-slackclient/) API is the old API

[slack_sdk](https://slack.dev/python-slack-sdk/) is the new SDK for python for Slack.

Slack also has a python API called [BOLT](https://github.com/slackapi/bolt-python). BOLT seems to be the simplistic way of creating and using Bots with Python.

## What Does Actions Does the Current Bot Support ? 

### MVP : With Read Only Access

- Help
  - Dummy rule to define help anchors
  - First message of the thread, requesting help
- New Thread
  - First message of the thread
- Internal Events to Save all data:
  - Run process lost
- Run Status Checks
  - Show runs but no rungroup
  - Show run status
  - Show run but run has finished already
- Read Parameters of Flow
  - Show parameters but no code set
  - Show parameters
  - Export Flow Meta as JSON [+]
- Run Inspection 
  - Define a run to be inspected
  - Inspect run without an argument and no run set, show help
  - Inspect run without an argument but a run is set, basic inspect
  - Inspect but no run set
  - Inspect the chosen run
  - How to inspect run
  - How to inspect (fallback)
- Data Inspection
  - Inspect data but no run set, show help
  - Inspect data with an argument
  - Inspect data without an argument, show help
- Log Inspection
  - Inspect logs but no run set, show help
  - Inspect logs with an argument
  - Inspect logs without an argument, show help
- Generic Help
  - Generic help fallbacks


### Not Part of MVP

- Run Execution Rules [X]
  - Run but no flow specified
  - Run already started
  - Start a run
- Cancellations [X]
  - Cancel runs
  - Cancel but nothing running
- Quiet run status updates [X]
  - Disable automatic run status updates but no rungroup
  - Disable automatic run status updates
- Use code (?) : Code Exec Preferences for Runs [X]
  - How to use code
  - Remind about parameters after setting code
- Parameter based Instantiation [X]
  - Set parameter but no code set
  - Set parameter
  - Set parameter CSV
  - Set parameter syntax issue
  - How to set parameters

## Action Plan 

> The current implementation of MetaflowBot relies on soon-to-be-deprecated slack APIs that we can migrate away from. 

- Modify [metaflowbot/slack_client.py](metaflowbot/slack_client.py) with a new modified version of either `slack_sdk` or `BOLT`. 
    - Change the abstractions according to the event management done via [metaflowbot/server.py](metaflowbot/server.py). The `loop_forever` method has all the underlying abstractions that manage the events coming to the bot from the slack RMT protocol and manage the individual subscript invocation for bot actions. 

> Create Read only Access driven MVP 

- Remove the rules which are not part of the MVP. 

> Create a fully configurable bot that can be setup in minimal step according to the configuration of choice. 

- Verify current installation and setup in the [metaflowbot/cli.py](metaflowbot/cli.py) and identify changes that will help support configuration in a standalone way and also via pointing to a configuration file.

> Verify that the bot’s performance doesn’t degrade as the number of flows/tasks increase or more users use the bot. Verify that the bot is able to recover from crashes seamlessly.
- Create a suit of tests that can analyze the performance of the bot on different types and traffic of messages. Understand UX behaviour and simulate crashes to see how things function when bot dies :X 

> Create documentation for How-to-use the bot , How-to-deploy, how-to-upgrade and how-to-extend the bot guide.

- Write docs as a part of the development process. 

## References:

1. https://www.digitalocean.com/community/tutorials/how-to-build-a-slackbot-in-python-on-ubuntu-20-04
   - Good Auth setup instructions.
2. https://slack.engineering/rewriting-the-slack-python-sdk/
   - Blog on the `slackclient` deprecation and migration of `slack_sdk`.
