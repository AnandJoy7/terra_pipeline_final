import boto3
import json
import os
import subprocess
from pathlib import Path

# Constants for directory paths
ROOT_MODULE_DIR = "terraform-vpc-root"
CHILD_MODULE_DIR = f"{ROOT_MODULE_DIR}/modules/vpc"
TFVARS_FILE = f"{ROOT_MODULE_DIR}/terraform.tfvars"
IMPORT_SCRIPT_FILE = f"{ROOT_MODULE_DIR}/import_resources.sh"

def get_boto3_client(service, region):
    """Initialize a Boto3 client for the given service and region."""
    return boto3.client(service, region_name=region)

def create_directory_structure():
    """Create root and child module directories."""
    os.makedirs(CHILD_MODULE_DIR, exist_ok=True)
    print(f"Directory structure created at {CHILD_MODULE_DIR}")

def write_to_file(filename, content):
    """Write content to the specified file."""
    with open(filename, 'w') as f:
        f.write(content)
    print(f"File written: {filename}")

def generate_terraform_root_module():
    """Generate the root Terraform module."""
    content = """
    terraform {
      required_providers {
        aws = {
          source  = "hashicorp/aws"
          version = "~> 4.0"
        }
      }
    }

    provider "aws" {
      region = var.aws_region
    }

    module "vpc" {
      source = "./modules/vpc"
      cidr_block = var.vpc_cidr_block
    }

    variable "aws_region" {}
    variable "vpc_cidr_block" {}
    """
    write_to_file(f"{ROOT_MODULE_DIR}/main.tf", content)

def generate_terraform_child_module():
    """Generate the child Terraform VPC module."""
    content = """
    resource "aws_vpc" "this" {
      cidr_block = var.cidr_block
    }

    resource "aws_internet_gateway" "this" {
      vpc_id = aws_vpc.this.id
    }

    resource "aws_subnet" "this" {
      for_each = var.subnet_cidrs
      cidr_block = each.value
      vpc_id     = aws_vpc.this.id
    }

    resource "aws_security_group" "this" {
      name   = "example_sg"
      vpc_id = aws_vpc.this.id
    }

    variable "cidr_block" {}
    variable "subnet_cidrs" {
      type = map(string)
    }
    """
    write_to_file(f"{CHILD_MODULE_DIR}/main.tf", content)

def fetch_vpc_resources(ec2_client, vpc_id):
    """Fetch all resources for a VPC."""
    print(f"Fetching resources for VPC: {vpc_id}")
    subnets = ec2_client.describe_subnets(Filters=[{'Name': 'vpc-id', 'Values': [vpc_id]}])['Subnets']
    igws = ec2_client.describe_internet_gateways(Filters=[{'Name': 'attachment.vpc-id', 'Values': [vpc_id]}])['InternetGateways']
    route_tables = ec2_client.describe_route_tables(Filters=[{'Name': 'vpc-id', 'Values': [vpc_id]}])['RouteTables']
    security_groups = ec2_client.describe_security_groups(Filters=[{'Name': 'vpc-id', 'Values': [vpc_id]}])['SecurityGroups']

    return {
        'subnets': subnets,
        'internet_gateways': igws,
        'route_tables': route_tables,
        'security_groups': security_groups
    }

def generate_terraform_tfvars(region, vpc_cidr, subnet_cidrs):
    """Generate a terraform.tfvars file."""
    content = f"""
    aws_region = "{region}"
    vpc_cidr_block = "{vpc_cidr}"
    subnet_cidrs = {json.dumps(subnet_cidrs, indent=4)}
    """
    write_to_file(TFVARS_FILE, content)

def generate_import_script(resources, vpc_id):
    """Generate a script to import existing resources into Terraform."""
    lines = [f"terraform import module.vpc.aws_vpc.this {vpc_id}"]
    
    for subnet in resources['subnets']:
        lines.append(f"terraform import module.vpc.aws_subnet.this[\"{subnet['SubnetId']}\"] {subnet['SubnetId']}")

    for igw in resources['internet_gateways']:
        lines.append(f"terraform import module.vpc.aws_internet_gateway.this {igw['InternetGatewayId']}")

    for rt in resources['route_tables']:
        lines.append(f"terraform import module.vpc.aws_route_table.this {rt['RouteTableId']}")

    for sg in resources['security_groups']:
        lines.append(f"terraform import module.vpc.aws_security_group.this {sg['GroupId']}")

    script_content = "\n".join(lines)
    write_to_file(IMPORT_SCRIPT_FILE, script_content)
    # Make the script executable
    Path(IMPORT_SCRIPT_FILE).chmod(0o755)
    print(f"Import script generated at {IMPORT_SCRIPT_FILE}")

def main():
    """Main function to automate the process."""
    region = input("Enter the AWS region (e.g., us-east-1): ")
    ec2_client = get_boto3_client('ec2', region)

    # Create the directory structure and Terraform modules
    create_directory_structure()
    generate_terraform_root_module()
    generate_terraform_child_module()

    # Input CIDR block details
    vpc_cidr = input("Enter the CIDR block for the new VPC (e.g., 10.0.0.0/16): ")
    subnet_cidrs = {
        "subnet1": input("Enter the CIDR block for subnet1 (e.g., 10.0.1.0/24): "),
        "subnet2": input("Enter the CIDR block for subnet2 (e.g., 10.0.2.0/24): ")
    }

    # Create terraform.tfvars
    generate_terraform_tfvars(region, vpc_cidr, subnet_cidrs)

    # Import existing VPC resources
    existing_vpc_id = input("Enter the existing VPC ID to import: ")
    resources = fetch_vpc_resources(ec2_client, existing_vpc_id)
    generate_import_script(resources, existing_vpc_id)

    print("\nTerraform setup completed successfully.")
    print("Run the following commands to initialize and apply Terraform:")
    print(f"  cd {ROOT_MODULE_DIR}")
    print("  terraform init")
    print("  terraform apply")
    print("To import resources, run:")
    print(f"  ./{IMPORT_SCRIPT_FILE}")

if __name__ == "__main__":
    main()
