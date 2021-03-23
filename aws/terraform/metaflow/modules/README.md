# Modules

Our Metaflow Terraform code has been separated into separate modules based on the service architecture.

## Datastore

Sets up blob and tabular data storage. Records all flows, the steps they took, their conda environments, artifacts and results.

Should exist for the lifetime of the stack.

## Metadata Service

Sets up an API entrypoint to interact with all other services, both for running flows and interacting with the Datastore to explore historic runs.

## Computation

Sets up remote computation resources so flows can be run on EC2 instances.