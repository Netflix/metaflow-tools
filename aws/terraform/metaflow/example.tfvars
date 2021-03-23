env = "prod"

aws_region = "us-west-2"

# Since we're testing, as this is the dev stack setting the min and desired to 0 so that we experience a cold-boot
# should be appropriate
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
