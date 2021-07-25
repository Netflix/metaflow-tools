# Metaflow bot docker file : Temp workaround like to to use heroku github action
FROM python:3.7.2
ADD metaflowbot /metaflowbot
RUN pip3 install /metaflowbot/.
RUN pip3 install /metaflowbot/extensions/jokes-command/.
CMD python3 -m metaflowbot --slack-bot-token $(echo $SLACK_BOT_TOKEN) server --admin $(echo $ADMIN_USER_ADDRESS) --new-admin-thread
