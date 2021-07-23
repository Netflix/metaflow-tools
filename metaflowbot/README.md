# Metaflow Bot

## Documentation
Thorough Documentation is present in the [Documentation folder](./Docs)
## Bot Commands

- `@flowey help` | `@flowey hi` : Help

- `@flowey tell me a joke`

- `@flowey inspect` | `@flowey how to inspect` : How to inspect

- `@flowey inspect HelloFlow` : Inspect `Run`s of a particular `Flow`

- `@flowey inspect savin's HelloFlow`: Inspect `Run`s of a particular `Flow`

- `@flowey inspect savin's HelloFlow tagged some_tag` : Inspect `Run`s of a particular `Flow`

- `@flowey inspect HelloFlow/12` : Inspect an individual `Run` instance

- `@flowey inspect the latest run of HelloFlow` : Inspect an individual `Run` instance

- `@flowey inspect dberg's latest run of HelloFlow` : Inspect an individual `Run` instance


## Metaflow Bot UX (How Will the bot Behave)

There are two places to interact with Metaflowbot : on a `channel` or via `direct message`. But for either places, the following is the general behavior of the bot:

> *When a user messages the bot, the bot will open a new message thread and will engage with the user on the same thread. The user can open multiple threads with the bot. Each thread is an independent discussion*

The following are interaction/UX restrictions based on where the user is conversing with the Metaflow bot.
### Talking to the bot on a `channel`

As the current [manifest.yml](./manifest.yml) only supports `app_mention` and `message.im` events. This means that when users want to talk to the bot on a channel, then they need to specifically need to mention `@flowey` or `@custombotname` to talk to the bot. We don't listen to messages on channels only `app_mentions`.

### Talking to the bot in `direct messages`

Users can message the bot without `@` mentions via direct messages. The bot will support the same command list.

## References:

- [Slack Permission Scopes](https://api.slack.com/scopes)
- [Slack Events](https://api.slack.com/events)
- [Slack Socket Mode](https://slack.dev/python-slack-sdk/socket-mode/index.html#socketmodeclient)
- [How to make threads in slack via python API](https://slack.dev/python-slack-sdk/web/index.html)
