output "SAGEMAKER_NOTEBOOK_URL" {
  value       = "https://${aws_sagemaker_notebook_instance.this.name}.notebook.${var.aws_region}.sagemaker.aws/tree"
  description = "URL used to access the SageMaker notebook instance"
}
