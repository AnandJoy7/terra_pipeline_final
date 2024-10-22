pipeline {
    agent any 

    environment {
        AWS_ACCESS_KEY_ID     = credentials('aws-access-key')  // AWS Access Key from Jenkins
        AWS_SECRET_ACCESS_KEY = credentials('aws-secret-key')  // AWS Secret Key from Jenkins
        GITHUB_CREDENTIALS    = credentials('github-credentials')  // GitHub credentials from Jenkins
        AWS_DEFAULT_REGION    = 'us-east-1'  // Change to your desired AWS region
    }

    stages {
        stage('Clean Workspace') {
            steps {
                // Clean the workspace to avoid conflicts
                deleteDir()
            }
        }

        stage('Checkout Code') {
            steps {
                script {
                    // Clone the repository into the 'terraform' directory
                    dir('terraform') {
                        git(
                            url: 'https://github.com/AnandJoy7/terra_pipeline_final.git',
                            branch: 'main',  // Ensure correct branch is specified
                            credentialsId: 'github-credentials'
                        )
                    }
                }
            }
        }

        stage('Run Terraform Script') {
            steps {
                // Execute the Terraform automation script from the 'terraform' directory
                dir('terraform') {
                    sh 'python3 terra_auto.py'
                }
            }
        }
    }

    post {
        always {
            // Archive Terraform plan output for reference
            dir('terraform') {
                archiveArtifacts artifacts: 'terraform_plan_output.txt', allowEmptyArchive: true
            }
        }
        success {
            echo 'Terraform automation completed successfully.'
        }
        failure {
            echo 'Terraform automation failed. Please check the logs.'
        }
    }
}
