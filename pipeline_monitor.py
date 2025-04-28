import os
import boto3
import argparse
from datetime import datetime
from typing import Dict, List
from tabulate import tabulate
from dotenv import load_dotenv

load_dotenv()


class PipelineMonitor:
    def __init__(self, name_filters: List[str]):
        load_dotenv()

        # Get AWS credentials from environment variables
        self.aws_access_key_id = os.getenv("AWS_ACCESS_KEY_ID")
        self.aws_secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY")
        self.aws_session_token = os.getenv("AWS_SESSION_TOKEN")
        self.aws_region = os.getenv("AWS_REGION", "eu-west-1")
        self.name_filters = [f.lower() for f in name_filters]

        if not all(
            [self.aws_access_key_id, self.aws_secret_access_key, self.aws_session_token]
        ):
            raise ValueError("AWS credentials not found in environment variables")

        # Initialize AWS clients
        self.codepipeline = boto3.client(
            "codepipeline",
            aws_access_key_id=self.aws_access_key_id,
            aws_secret_access_key=self.aws_secret_access_key,
            aws_session_token=self.aws_session_token,
            region_name=self.aws_region,
        )

    def get_latest_execution(self, pipeline_name: str) -> Dict:
        """Get the latest execution for a specific pipeline"""
        try:
            response = self.codepipeline.list_pipeline_executions(
                pipelineName=pipeline_name,
                maxResults=1,  # Get only the latest execution
            )
            executions = response.get("pipelineExecutionSummaries", [])
            return executions[0] if executions else None
        except Exception as e:
            print(
                f"Error getting latest execution for pipeline {pipeline_name}: {str(e)}"
            )
            return None

    def get_commit_message(self, pipeline_name: str, execution_id: str) -> str:
        """Get commit message from pipeline execution"""
        try:
            response = self.codepipeline.get_pipeline_execution(
                pipelineName=pipeline_name, pipelineExecutionId=execution_id
            )

            execution = response.get("pipelineExecution", {})
            if not execution:
                return "Unknown"

            # Look for the source action in the execution
            for stage in execution.get("artifactRevisions", []):
                if not "helm" in stage.get("name", "").lower():
                    revision_summary = stage.get("revisionSummary", "")
                    # Extract commit message from revision summary
                    # Format is usually like "commit message (branch: branch-name)"
                    if 'CommitMessage":"' in revision_summary:
                        commit_message = revision_summary.split('CommitMessage":')[1][
                            1:-2
                        ]
                    else:
                        commit_message = revision_summary
                    return commit_message

            return "Unknown"
        except Exception as e:
            print(
                f"Error getting commit message for pipeline {pipeline_name}: {str(e)}"
            )
            return "Unknown"

    def get_pipeline_branch(self, pipeline_name: str) -> str:
        """Get the branch name from pipeline configuration"""
        try:
            # Get the pipeline configuration
            response = self.codepipeline.get_pipeline(name=pipeline_name)
            pipeline = response.get("pipeline", {})

            # Find the source stage
            for stage in pipeline.get("stages", []):
                if stage.get("name", "").lower() == "source":
                    # Find the source action
                    for action in stage.get("actions", []):
                        # Get the configuration
                        configuration = action.get("configuration", {})
                        # The branch is in the BranchName configuration
                        branch = configuration.get("BranchName")
                        if branch:
                            return branch

            return "Unknown"
        except Exception as e:
            print(f"Error getting branch for pipeline {pipeline_name}: {str(e)}")
            return "Unknown"

    def format_duration(self, start_time: datetime, end_time: datetime = None) -> str:
        """Format the duration between two timestamps"""
        if not end_time:
            end_time = datetime.now()
        duration = end_time - start_time
        total_seconds = int(duration.total_seconds())

        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60

        if hours > 0:
            return f"{hours}h {minutes}m"
        elif minutes > 0:
            return f"{minutes}m {seconds}s"
        else:
            return f"{seconds}s"

    def format_date(self, date: datetime) -> str:
        """Format date in dd/mm/yy hh:mm format"""
        return date.strftime("%d/%m/%Y %H:%M")

    def list_all_pipelines(self) -> List[str]:
        """List all pipelines in the account that match any of the name filters"""
        try:
            response = self.codepipeline.list_pipelines()
            all_pipelines = [
                pipeline["name"] for pipeline in response.get("pipelines", [])
            ]
            # Filter pipelines based on the name filters
            return [
                pipeline
                for pipeline in all_pipelines
                if any(f in pipeline.lower() for f in self.name_filters)
            ]
        except Exception as e:
            print(f"Error listing pipelines: {str(e)}")
            return []

    def monitor_pipelines(self):
        """Main function to monitor pipelines"""
        print("\n=== AWS CodePipeline Deployment Monitor ===")
        print(f"Last updated: {self.format_date(datetime.now())}")
        print(f"Filtering pipelines containing: {', '.join(self.name_filters)}\n")

        # Get filtered pipelines
        pipelines = self.list_all_pipelines()

        if not pipelines:
            print(
                f"No pipelines found containing any of: {', '.join(self.name_filters)}"
            )
            return

        # Prepare data for tabulation
        table_data = []
        headers = [
            "Pipeline",
            "Branch",
            "Status",
            "Last Run",
            "Duration",
            "Commit Message",
        ]

        for pipeline in pipelines:
            execution = self.get_latest_execution(pipeline)
            if not execution:
                continue

            status = execution.get("status", "UNKNOWN")
            execution_id = execution.get("pipelineExecutionId", "")
            start_time = execution.get("startTime", datetime.now())
            last_update_time = execution.get("lastUpdateTime", datetime.now())

            # Format the last run time
            last_run = self.format_date(start_time)

            # Calculate duration
            if isinstance(start_time, datetime) and isinstance(
                last_update_time, datetime
            ):
                duration = self.format_duration(start_time, last_update_time)
            else:
                duration = "Unknown"

            branch = self.get_pipeline_branch(pipeline)
            commit_message = self.get_commit_message(pipeline, execution_id)

            # Truncate long commit messages
            if len(commit_message) > 50:
                commit_message = commit_message[:50] + "..."

            table_data.append(
                [pipeline, branch, status, last_run, duration, commit_message]
            )

        # Sort by pipeline name
        table_data.sort(key=lambda x: x[0])

        # Print the table
        print(tabulate(table_data, headers=headers, tablefmt="grid"))
        print()


if __name__ == "__main__":
    try:
        # Set up argument parser
        parser = argparse.ArgumentParser(
            description="Monitor AWS CodePipeline deployments"
        )
        parser.add_argument(
            "--filters",
            nargs="+",
            default=["kulu"],
            help="List of filters to match pipeline names (default: kulu)",
        )
        args = parser.parse_args()

        monitor = PipelineMonitor(name_filters=args.filters)
        monitor.monitor_pipelines()
    except Exception as e:
        print(f"Error: {str(e)}")
        print("\nPlease ensure you have set the following environment variables:")
        print("AWS_ACCESS_KEY_ID")
        print("AWS_SECRET_ACCESS_KEY")
        print("AWS_SESSION_TOKEN")
