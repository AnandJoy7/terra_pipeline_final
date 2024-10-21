pipeline {
    agent any

    environment {
        // Load AWS and Git credentials from Jenkins Credentials Store
        AWS_ACCESS_KEY_ID = credentials('aws-access-key')
        AWS_SECRET_ACCESS_KEY = credentials('aws-secret-key')
        GIT_PAT = credentials('git-pat')  // Personal Access Token (PAT) for GitHub
    }

    stages {
        stage('Clone Repository from Main') {
            steps {
                git branch: 'main', 
                    url: 'https://github.com/AnandJoy7/terra_pipeline_final.git', 
                    credentialsId: 'github-credentials'
            }
        }

        stage('Setup Python Environment') {
            steps {
                sh '''
                python3 -m venv venv
                source venv/bin/activate
                pip install boto3
                '''
            }
        }

        stage('Run Python Script') {
            steps {
                withCredentials([
                    string(credentialsId: 'aws-access-key', variable: 'AWS_ACCESS_KEY_ID'),
                    string(credentialsId: 'aws-secret-key', variable: 'AWS_SECRET_ACCESS_KEY')
                ]) {
                    sh '''
                    source venv/bin/activate
                    python terra_auto.py <<EOF
                    us-east-1
                    10.0.0.0/16
                    10.0.1.0/24
                    10.0.2.0/24
                    vpc-xxxxxxxx
                    EOF
                    '''
                }
            }
        }

        stage('Initialize and Apply Terraform') {
            steps {
                dir('terraform-vpc-root') {
                    sh '''
                    terraform init
                    terraform apply -auto-approve
                    '''
                }
            }
        }

        stage('Run Terraform Import Script') {
            steps {
                dir('terraform-vpc-root') {
                    sh './import_resources.sh'
                }
            }
        }

        stage('Commit and Push Changes to Dev Branch') {
            steps {
                dir('terraform-vpc-root') {
                    sh '''
                    git config --global user.name "Jenkins CI"
                    git config --global user.email "jenkins@example.com"
                    git checkout -b dev
                    git add terraform.tfvars import_resources.sh *.tf
                    git commit -m "Add Terraform state and imported resources"
                    git push https://${GIT_PAT}@github.com/AnandJoy7/terra_pipeline_final.git dev
                    '''
                }
            }
        }
    }

    post {
        success {
            echo "Terraform setup and resource import completed successfully."
        }
        failure {
            echo "Pipeline failed. Check the logs for details."
        }
    }
}
