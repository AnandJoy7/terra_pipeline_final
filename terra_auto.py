    import subprocess
    # import hcl2
    import os
    # import json
    import boto3

    def fetch_vpc_details(vpc_id, region):
        """Fetch VPC details from AWS using the given VPC ID."""
        ec2_client = boto3.client('ec2', region_name=region)
        response = ec2_client.describe_vpcs(VpcIds=[vpc_id])
        
        if response['Vpcs']:
            vpc = response['Vpcs'][0]
            cidr_block = vpc['CidrBlock']
            tags = {tag['Key']: tag['Value'] for tag in vpc.get('Tags', [])}
            return cidr_block, tags
        else:
            raise Exception(f"VPC with ID {vpc_id} not found.")

    def create_directory_structure(base_path):
        """Create the required directory structure."""
        # Create Parent_Module directory
        parent_module = os.path.join(base_path, "Parent_Module")
        os.makedirs(parent_module, exist_ok=True)
        
        # Create Child_Module directory
        child_module = os.path.join(base_path, "Child_Module")
        os.makedirs(child_module, exist_ok=True)
        
        return parent_module, child_module

    def create_terraform_files(parent_module, child_module):
        """Create all necessary Terraform files."""
        # Parent Module files
        parent_main_tf = """resource "aws_vpc" "my_existing_vpc" {
        for_each = var.imported_vpc_configs
        
        cidr_block           = each.value.cidr_block
        enable_dns_support   = each.value.enable_dns_support
        enable_dns_hostnames = each.value.enable_dns_hostnames
        tags                 = each.value.tags
    }"""
        
        parent_variables_tf = """variable "imported_vpc_configs" {
        description = "Imported VPC configurations"
        type = map(object({
            cidr_block           = string
            enable_dns_support   = bool
            enable_dns_hostnames = bool
            tags                 = map(string)
        }))
        default = {}
    }

    variable "aws_region" {
        description = "AWS region"
        type        = string
    }"""
        
        # Create parent module files
        with open(os.path.join(parent_module, "main.tf"), "w") as f:
            f.write(parent_main_tf)
        with open(os.path.join(parent_module, "variables.tf"), "w") as f:
            f.write(parent_variables_tf)
        
        # Child Module files
        child_main_tf = """module "imported_vpc" {
        source = "../Parent_Module"

        imported_vpc_configs = var.imported_vpc_configs
        aws_region          = var.aws_region
    }"""
        
        child_variables_tf = """variable "imported_vpc_configs" {
        description = "Imported VPC configurations"
        type = map(object({
            cidr_block           = string
            enable_dns_support   = bool
            enable_dns_hostnames = bool
            tags                 = map(string)
        }))
        default = {}
    }

    variable "aws_region" {
        description = "AWS region"
        type        = string
    }

    variable "existing_vpc_ids" {
        description = "List of existing VPC IDs to import"
        type        = list(string)
        default     = []
    }"""
        
        backend_tf = """terraform {
        backend "local" {}
    }"""
        
        # Create child module files
        with open(os.path.join(child_module, "main.tf"), "w") as f:
            f.write(child_main_tf)
        with open(os.path.join(child_module, "variables.tf"), "w") as f:
            f.write(child_variables_tf)
        with open(os.path.join(child_module, "backend.tf"), "w") as f:
            f.write(backend_tf)

    def create_or_update_tfvars(child_module, vpc_id, cidr_block, tags, region):
        """Create or update terraform.tfvars file preserving existing configurations."""
        # Format tags with proper newlines and commas
        formatted_tags = ',\n'.join([f'      {k} = "{v}"' for k, v in tags.items()])
        
        tfvars_content = f"""aws_region = "{region}"


    existing_vpc_ids = ["{vpc_id}"]

    imported_vpc_configs = {{
    "{vpc_id}" = {{
        cidr_block           = "{cidr_block}"
        enable_dns_support   = true
        enable_dns_hostnames = true
        tags = {{
    {formatted_tags}
        }}
    }}
    }}"""
        
        tfvars_path = os.path.join(child_module, "terraform.tfvars")
        with open(tfvars_path, "w") as f:
            f.write(tfvars_content)

    def main():
        """Main function to run the script."""
        # Get the current script's directory
        base_path = os.path.dirname(os.path.abspath(__file__))
        
        # Create directory structure
        parent_module, child_module = create_directory_structure(base_path)
        
        # Create Terraform files
        create_terraform_files(parent_module, child_module)
        
        # Configuration
        region = "us-east-1"  # Change this to your desired region
        vpc_id = "vpc-0d522ed84b46c719d"  # Your existing VPC ID
        
        try:
            # Fetch VPC details
            print(f"Fetching details for VPC {vpc_id}...")
            cidr_block, tags = fetch_vpc_details(vpc_id, region)
            
            # Create or update tfvars
            create_or_update_tfvars(child_module, vpc_id, cidr_block, tags, region)
            
            # Change to Child_Module directory
            os.chdir(child_module)
            
            # Initialize Terraform
            print("Initializing Terraform...")
            subprocess.run(['terraform', 'init'], check=True)
            
            # Import VPC
            print(f"Importing VPC {vpc_id}...")
            import_cmd = [
                'terraform', 'import',
                f'module.imported_vpc.aws_vpc.my_existing_vpc["{vpc_id}"]',
                vpc_id
            ]
            result = subprocess.run(import_cmd, capture_output=True, text=True)
            if result.returncode != 0:
                print("Import Output:", result.stdout)
                print("Import Error:", result.stderr)
            else:
                print("Import successful!")
            
            # Plan and apply
            print("Planning changes...")
            subprocess.run(['terraform', 'plan'], check=True)
            
            print("Applying changes...")
            subprocess.run(['terraform', 'apply', '-auto-approve'], check=True)
            
            print("VPC import completed successfully!")
            
        except Exception as e:
            print(f"Error: {str(e)}")
            exit(1)

    if __name__ == "__main__":
        main()