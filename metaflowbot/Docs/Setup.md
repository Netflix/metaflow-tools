# Metaflow Bot Setup

The setup follows two parts.
1. The first part is setting up the bot on Slack to get access tokens.
2. The second part is running the Bot server manually or via a docker image.
## Slack Setup

1. [Create an App on Slack UI](https://api.slack.com/apps) using provided [manifest](../manifest.yml).

    ![](images/slacksetup.png)

2. Install the App
    ![](images/app_install.png)

3. Generate App token
    ![](images/app-token.png)

4. Generate Bot token
    ![](images/bot-token.png)

## Manual Running the Bot

1. Export the tokens as environment variables :
    ```sh
    export SLACK_APP_TOKEN=xapp-1-AAAAAAAAAAA-2222222222222-AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
    export SLACK_BOT_TOKEN=xoxb-2222222222222-2222222222222-AAAAAAAAAAAAAAAAAAAAAAAA
    ```

2. Run the BOT :

    ```sh
    python -m metaflowbot --slack-token $(echo $SLACK_BOT_TOKEN) server --admin me@server.com --new-admin-thread
    ```

## Running Via Docker Image

1. Building Docker image

    ```sh
    docker build -t metaflowbot .
    ```
2. Running the Bot Container instance on local. You can shed some metaflow variables and load a volume to the `~./metaflowconfig` to set Metaflow Config variables
    ```sh
    docker run -i -t --rm \
        -e SLACK_BOT_TOKEN=$(echo $SLACK_BOT_TOKEN) \
        -e ADMIN_USER_ADDRESS=admin@server.com \
        -e SLACK_APP_TOKEN=$(echo $SLACK_APP_TOKEN) \
        -e AWS_SECRET_ACCESS_KEY=$(echo $AWS_SECRET_ACCESS_KEY) \
        -e AWS_ACCESS_KEY_ID=$(echo $AWS_ACCESS_KEY_ID) \
        -e USERNAME=$(echo $USERNAME) \
        -e METAFLOW_SERVICE_AUTH_KEY=$(echo $METAFLOW_SERVICE_AUTH_KEY) \
        -e METAFLOW_SERVICE_URL=$(echo $METAFLOW_SERVICE_URL) \
        -e ADMIN_USER_ADDRESS=$(echo $METAFLOW_SERVICE_URL) \
        -e METAFLOW_DATASTORE_SYSROOT_S3=$(echo $METAFLOW_DATASTORE_SYSROOT_S3) \
        -e METAFLOW_DATATOOLS_SYSROOT_S3=$(echo $METAFLOW_DATATOOLS_SYSROOT_S3) \
        -e METAFLOW_DEFAULT_METADATA=service \
        -e METAFLOW_DEFAULT_DATASTORE=s3 \
        metaflowbot
    ```
