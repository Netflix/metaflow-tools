# Metaflow Bot Setup 

The setup Has the following steps:

1. [Create an App on Slack UI](https://api.slack.com/apps) using provided [manifest](../manifest.yml).

    ![](images/slacksetup.png)

2. Install the App
    ![](images/app_install.png)

3. Generate App token 
    ![](images/app-token.png)

4. Generate Bot token 
    ![](images/bot-token.png)

5. Export the tokens as environment variables :
    ```sh
    export SLACK_APP_TOKEN=xapp-1-AAAAAAAAAAA-2222222222222-AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
    export SLACK_BOT_TOKEN=xoxb-2222222222222-2222222222222-AAAAAAAAAAAAAAAAAAAAAAAA
    ```

6. Run the BOT :

    ```sh
    python -m metaflowbot --slack-token $(echo $SLACK_BOT_TOKEN) server --admin me@server.com --new-admin-thread
    ```

## TODOS

1. Clean up Bot-Token and slack token passing to the bot server.
2. Remove code relating to starting runs.
3. Run more tests on the bot to test actual read functionality.
4. Test flow executions with the bot.
5. Setup profile based configuration change. 