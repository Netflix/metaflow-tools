## Pre-requisites

### Terraform

[Download](https://www.terraform.io/downloads.html) and install terraform 0.14.x.

### AWS

AWS should be [configured](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-quickstart.html) with a profile. The `AWS_PROFILE` environment should be set to the profile that has been configured.

The [awscli](https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-install.html) can be used as follows to 
confirm that it has been configured properly by running:

```
aws sts get-caller-identity
```

which should output your account information.

## Setup

### Infrastructure stack

The infra sub-project provides some pre-requisite infrastructure for the Metaflow service. For more details see the [README](aws/terraform/infra/README.md)

Copy `example.tfvars` to `prod.tfvars` (or whatever environment name you prefer) and update that `env` name and the `region` as needed. These variables are used to construct unique names for infrastructure resources.

Initialize the terraform:

`cd infra && terraform init`

Apply it:

```
terraform apply --var-file prod.tfvars
```

### Metaflow stack

The metaflow sub-project provisions the metadata API, AWS Step Functions, and an AWS Batch queue. For more details see the 
[README](aws/terraform/metaflow/README.md)

Copy `example.tfvars` to `prod.tfvars` (or whatever environment name you prefer) and update that `env` name and the `region` as needed. These variables are used to construct unique names for infrastructure resources.

Metadata API authentication: the endpoint is exposed to the public internet via Amazon API Gateway, but only accessible to the IPs that match `access_list_cidr_blocks` (default is none).

Additionally:
* There are variables which govern the three compute environments associated with the AWS Batch queue that can be adjusted based on needs. 
* The `enable_step_functions` flag can be set to false to not provision the AWS Step Functions infrastructure.
* The `access_list_cidr_blocks` should be set to the network cidr blocks that will be accessing the metadata API. If you only need access from your local machine, determine your public IP address (`curl https://ifconfig.me/`) and add that value to the list.

Initialize the terraform:

`cd infra && terraform init`

Apply it:

```
terraform apply --var-file prod.tfvars
```

Once the Terraform executes, configure Metaflow using `metaflow configure import ./metaflow_config_<env>_<region>.json`

### Custom Default Batch Image

A custom default batch image can be used by setting the variable `enable_custom_batch_container_registry` to `true`. This will provision an Amazon ECR registry, and the generated Metaflow AWS Batch configuration will have `METAFLOW_BATCH_CONTAINER_IMAGE` and `METAFLOW_BATCH_CONTAINER_REGISTRY` set to the Amazon ECR repository. The Metaflow AWS Batch image must then be pushed into the repository before the first flow can be executed.

To do this, first copy the output of `metaflow_batch_container_image`.

Then login to the Amazon ECR repository:
```
aws ecr get-login-password | docker login --username AWS --password-stdin <ecr-repository-name>
```

Pull the appropriate image from Docker Hub. In this case, we are using `continuumio/miniconda3:latest`:

```
docker pull continuumio/miniconda3
```

Tag the image:

```
docker tag continuumio/miniconda3:latest <ecr-repository-name>
```

Push the image:

```
docker push <ecr-repository-name>
```

### Amazon Sagemaker Notebook stack

The sagemaker-notebook subproject provisions an optional Jupyter notebook with access to the Metaflow API.

Copy `example.tfvars` to `prod.tfvars` (or whatever environment name you prefer) and update that `env` name and the `region` as needed. These variables are used to construct unique names for infrastructure resources.

Initialize the terraform:

`cd infra && terraform init`

Apply it:

```
terraform apply --var-file prod.tfvars
```

The Amazon Sagemaker notebook url is output as `SAGEMAKER_NOTEBOOK_URL`. Open it to access the notebook.
