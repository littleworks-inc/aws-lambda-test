# NetraScale-API
The NetraScale-API documents the Lambda functions and their deployment methods following a 
standardized approach including patterns, idioms, heuristics, and SDLC elements. This documentation
is intended for the internal development team to build, maintain, and support our serverless API.

# Database Credential Security
Database variables should be placed as "environment variables" for the function until Secrets Manager is used.
The variable definitions are as follows:

- ``DB_HOST``
- ``DB_NAME``
- ``DB_USER``
- ``DB_PASSWORD``
- ``DB_PORT``

Hardcoding of sensitive information like database passwords in your code must be avoided at all times. Use environment variables or AWS Secrets Manager for secure storage. The following is an example of how the information can be retrieved (minus error checking).

```python
import os

db_host = os.environ['DB_HOST']
db_name = os.environ['DB_NAME']
db_user = os.environ['DB_USER']
db_password = os.environ['DB_PASSWORD']
db_port = os.environ.get('DB_PORT', 5432)
```

## Deployment Methodology

1. Package the function to be deployed and perform the following commands

```bash 
$ cd risk_act_api/lambdas/function1

# Install dependencies locally into a "build" directory (from requirements.txt)
pip install -r requirements.txt --target ./build

# Copy source code to the "build" directory
cp app.py config.json build/
cp -R ../common build/common

# Package everything into a zip file
cd build
zip -r ../function1.zip .
```

2. Deploy using Terraform to the production environment
```bash
$ terraform init
$ terraform apply
```

Alternatively, the deployment script can be used:

```batch
deploy_lambda.bat
```

which will produce output similiar to the following:
```
Starting deployment for function1...
Zipping Lambda function code...
Creating build directory...
Installing dependencies...
Copying Lambda code and dependencies to build directory...
Creating zip file...
Running Terraform to deploy Lambda function...
Terraform initialization successful!
Terraform plan completed.
Deployment successful for function1!
```

If an error occurs at any step, you'll get a red error message, such as:
```
Failed to zip Lambda function!
```

## Setup and Configuration

### Associated Libraries

### Directory Structure

1. **lambdas/** Directory - Each Lambda function resides in its own subdirectory (function1, function2, etc.).
    - ``app.py``: The main Lambda handler file.
    - ``requirements.txt``: Specific dependencies for the function.
    - ``config.json``: Optional configuration file for environment-specific variables.
    - ``__init__.py``: Marks the directory as a Python package (can be empty or contain imports).

2. **common/** Directory - Contains reusable components shared by multiple functions, such as:
    - ``constants.py``: Application-wide constants

3. **tests/** Directory - Mirrors the structure of the lambdas/ directory.
    - Test files are named as test_``<function_name>.py``

4. **infrastructure/** Directory - Contains templates for infrastructure as code
    - ``terraform/``: For Terraform-based IaC.
    - Documentation for deployment.

5. **scripts/** Directory - Automation scripts for packaging, deploying, and managing the Lambda functions.

6. **Root Files**
    - ``requirements.txt``: For shared dependencies if functions use similar libraries.
    - ``.gitignore``: To exclude unnecessary files (e.g., __pycache__, .env, etc.).
    - ``.env.example``: A template for managing environment variables.
    - ``README.md``: High-level project overview and instructions.

## Resources