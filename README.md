# AWS Pipeline Monitor

A Python script to monitor AWS CodePipeline deployments and display pipeline information in a tabulated format.

## Features

- List all pipelines matching specified filters
- Display current branch, status, and last execution time
- Show commit messages and execution duration
- Filter pipelines by name
- Command-line argument support for filters

## Prerequisites

- Python 3.6 or higher
- AWS credentials with appropriate permissions
- Required Python packages (see Installation)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/aws_pipeline_monitor.git
cd aws_pipeline_monitor
```

2. Create and activate a virtual environment:
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

3. Install the required packages:
```bash
pip install -r requirements.txt
```

4. Set up your AWS credentials:
```bash
# Copy the example environment file
cp .env.example .env
```

5. Edit the `.env` file with your AWS credentials
The `.env` file should contain:
```bash
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_SESSION_TOKEN=your_session_token
AWS_REGION=your_region  # Optional, defaults to eu-west-1
```

Alternatively, you can set the environment variables directly:
```bash
export AWS_ACCESS_KEY_ID=your_access_key
export AWS_SECRET_ACCESS_KEY=your_secret_key
export AWS_SESSION_TOKEN=your_session_token
export AWS_REGION=your_region  # Optional, defaults to eu-west-1
```

## Usage

Basic usage with default filter ("kulu"):
```bash
python pipeline_monitor.py
```

Specify a single filter:
```bash
python pipeline_monitor.py --filters core
```

Specify multiple filters:
```bash
python pipeline_monitor.py --filters core service
```

## Output Example

```text
=== AWS CodePipeline Deployment Monitor ===
Last updated: 01/01/2024 12:00
Filtering pipelines containing: core

+------------------+--------+-----------+------------------+----------+-------------------------------+
| Pipeline         | Branch | Status    | Last Run         | Duration | Commit Message                |
+==================+========+===========+==================+==========+===============================+
| core-service-1   | main   | Succeeded | 01/01/2024 11:30 | 5m 30s   | Update dependencies           |
+------------------+--------+-----------+------------------+----------+-------------------------------+
| core-service-2   | dev    | Failed    | 01/01/2024 10:45 | 2m 15s   | Fix authentication issue      |
+------------------+--------+-----------+------------------+----------+-------------------------------+
```

## Required AWS Permissions

The script requires your IAM role to have the following AWS permissions:
- `codepipeline:ListPipelines`
- `codepipeline:GetPipeline`
- `codepipeline:ListPipelineExecutions`
- `codepipeline:GetPipelineExecution`

## Contributing

Contributions are welcome! If you have a feature request or found a bug, please open an issue.

To contribute code:
1. Fork the repository
2. Create a new branch for your feature (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
