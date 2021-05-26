env = "prod"

aws_region = "us-west-2"

# Setting min vpcus and desired vcpus to 0 to prevent accidental cost accumulation.
# These settings will result in longer job startup times as AWS boots up the necessary compute resources.
cpu_max_compute_vcpus     = 128
cpu_min_compute_vcpus     = 0
cpu_desired_compute_vcpus = 0

large_cpu_max_compute_vcpus     = 128
large_cpu_min_compute_vcpus     = 0
large_cpu_desired_compute_vcpus = 0

gpu_max_compute_vcpus     = 128
gpu_min_compute_vcpus     = 0
gpu_desired_compute_vcpus = 0

enable_step_functions = true

access_list_cidr_blocks = []
