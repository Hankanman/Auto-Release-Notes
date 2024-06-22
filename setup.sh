#!/bin/bash

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check for Python
if command_exists python3; then
    echo "Python is installed."
else
    echo "Python is not installed. Please install Python from https://www.python.org/downloads/"
    exit 1
fi

# Check for pip
if command_exists pip3; then
    echo "pip is installed."
else
    echo "pip is not installed. Please install pip from https://pip.pypa.io/en/stable/installation/"
    exit 1
fi

# Check for npm
if command_exists npm; then
    echo "npm is installed."
else
    echo "npm is not installed. Please install npm from https://www.npmjs.com/get-npm"
    exit 1
fi

# Install Python dependencies
pip3 install -r requirements.txt

# Check if .env file exists, if not create it with default values
if [ ! -f .env ]; then
    echo "Creating .env file with default values."
    cat <<EOL > .env
# This file contains the configuration settings for the Auto-Release-Notes project. It is a template file and should be renamed to ".env" before use.
# The values in this file should be updated with the appropriate values for your environment.
# The name of the Azure DevOps organization.
ORG_NAME=
# The name of the Azure DevOps project.
PROJECT_NAME=
# The name of the solution or repository.
SOLUTION_NAME=
# The version of the release.
RELEASE_VERSION=
# The query used to filter work items for the release.
RELEASE_QUERY=
# The Personal Access Token (PAT) for accessing Azure DevOps APIs.
PAT=
# The API key for accessing the GPT API.
GPT_API_KEY=
# A summary of the software changes or updates.
SOFTWARE_SUMMARY=
# The folder where the release notes will be generated.
OUTPUT_FOLDER=Releases
# The GPT model to use for generating release notes.
MODEL=gpt-4o
# The base URL for the GPT API.
MODEL_BASE_URL=https://api.openai.com/v1
# The base URL for the Azure DevOps API.
DEVOPS_BASE_URL=https://dev.azure.com
# The version of the Azure DevOps API to use.
DEVOPS_API_VERSION=6.0
EOL
fi

echo "Setup complete. You can now run the main script using 'python3 main.py'."
