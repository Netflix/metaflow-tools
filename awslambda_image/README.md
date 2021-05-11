# Metaflow Docker image for AWS Lambda

This is the docker image that is used to run Metaflow steps on AWS Lambda.

To customize the image:
* edit the Dockerfile, but make sure to keep the entrypoint intact
* push the image to your ECR repository (Lambda only supports ECR)
* Either change `METAFLOW_LAMBDA_IMAGE_URI` to point to your new image, or specify a custom image URI per step in `@awslambda` decorator, e.g.
```python
@awslambda(image="1234.dkr.ecr.us-west-2.amazonaws.com/my-image:latest")
def my_step(self):
    ...
```

Another thing to note is that if you update the image under the same tag, Lambda will _not_ re-fetch it automatically. To force it, you can either click "Deploy new image" in the AWS Console, or use `refresh_image` option in the @awslambda decorator like this:
```python
@awslambda(image="..", refresh_image=True)
def my_step(self):
    ...
```

Setting this flag to True, however, adds significant latency for task start time, so it is not recommended to set it to True permanently.
