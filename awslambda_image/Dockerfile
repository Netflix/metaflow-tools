FROM public.ecr.aws/lambda/python:3.7

RUN yum install -y wget

RUN pip install awscli

COPY entrypoint.py ./
CMD ["entrypoint.handler"]
