# Metaflow Bot

## Table Of Contents

1. [Quick Setup And Running the Bot](./Setup.md)
2. [Bot Code Architecture](./Architecture.md)
3. [Slack Permissions and Scopes](./Scopes.md)
4. [Creating Custom/New Actions](Creating-Your-Action.md)


## Development Setup
### Pre-commit

We leverage the [pre-commit](https://pre-commit.com/) framework.

Install git hooks with `pre-commit install`.

Run the checks `pre-commit run --all-files`.

## What has Changed From the initial Version

Older version used the [slackclient](https://slack.dev/python-slackclient/) API which is an older version of the Slack API. The V2-bot uses the [python slack_sdk](https://slack.dev/python-slack-sdk/).
