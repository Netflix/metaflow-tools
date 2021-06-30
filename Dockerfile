FROM python:3.7
ADD metaflowbot /metaflowbot
RUN pip3 install -r /metaflowbot/requirements.txt
RUN cd /metaflowbot
CMD python3 -m metaflowbot --slack-token $(echo $SLACK_BOT_TOKEN) server --admin $(echo $ADMIN_USER_ADDRESS)

