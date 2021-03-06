"""
An interactive flow that prompt the user for required information to bootstrap the AWS account of an environment
with the required infrastructure
"""
import os
import sys
from textwrap import dedent
from typing import Optional, List, Tuple, Callable

import click
from botocore.credentials import EnvProvider

from samcli.commands.exceptions import CredentialsError
from samcli.commands.pipeline.external_links import CONFIG_AWS_CRED_DOC_URL
from samcli.lib.bootstrap.bootstrap import get_current_account_id
from samcli.lib.utils.colors import Colored

from samcli.lib.utils.defaults import get_default_aws_region
from samcli.lib.utils.profile import list_available_profiles


class GuidedContext:
    def __init__(
        self,
        profile: Optional[str] = None,
        environment_name: Optional[str] = None,
        pipeline_user_arn: Optional[str] = None,
        pipeline_execution_role_arn: Optional[str] = None,
        cloudformation_execution_role_arn: Optional[str] = None,
        artifacts_bucket_arn: Optional[str] = None,
        create_image_repository: bool = False,
        image_repository_arn: Optional[str] = None,
        region: Optional[str] = None,
    ) -> None:
        self.profile = profile
        self.environment_name = environment_name
        self.pipeline_user_arn = pipeline_user_arn
        self.pipeline_execution_role_arn = pipeline_execution_role_arn
        self.cloudformation_execution_role_arn = cloudformation_execution_role_arn
        self.artifacts_bucket_arn = artifacts_bucket_arn
        self.create_image_repository = create_image_repository
        self.image_repository_arn = image_repository_arn
        self.region = region
        self.color = Colored()

    def _prompt_account_id(self) -> None:
        profiles = list_available_profiles()
        click.echo("The following AWS credential sources are available to use:")
        click.echo(
            dedent(
                f"""\
                To know more about configuration AWS credentials, visit the link below:
                {CONFIG_AWS_CRED_DOC_URL}\
                """
            )
        )
        if os.getenv(EnvProvider.ACCESS_KEY) and os.getenv(EnvProvider.SECRET_KEY):
            click.echo(f"  e. Environment variables: {EnvProvider.ACCESS_KEY} and {EnvProvider.SECRET_KEY}")
        for i, profile in enumerate(profiles):
            click.echo(f"  {i + 1}. {profile} (named profile)")
        click.echo("  q. Quit and configure AWS credential myself")
        answer = click.prompt(
            "Select an account source to associate with this stage",
            show_choices=False,
            show_default=False,
            type=click.Choice([str(i + 1) for i in range(len(profiles))] + ["q", "e"]),
        )
        if answer == "q":
            sys.exit(0)
        elif answer == "e":
            # by default, env variable has higher precedence
            # https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-envvars.html#envvars-list
            self.profile = None
        else:
            self.profile = profiles[int(answer) - 1]

        try:
            account_id = get_current_account_id(self.profile)
            click.echo(self.color.green(f"Associated account {account_id} with stage {self.environment_name}."))
        except CredentialsError as ex:
            click.echo(self.color.red(ex.message))
            self._prompt_account_id()

    def _prompt_stage_name(self) -> None:
        click.echo(
            "Enter a name for this stage. This will be referenced later when you use the sam pipeline init command:"
        )
        self.environment_name = click.prompt(
            "Stage name",
            default=self.environment_name,
            type=click.STRING,
        )

    def _prompt_region_name(self) -> None:
        self.region = click.prompt(
            "Enter the region in which you want these resources to be created",
            type=click.STRING,
            default=get_default_aws_region(),
        )

    def _prompt_pipeline_user(self) -> None:
        self.pipeline_user_arn = click.prompt(
            "Enter the pipeline IAM user ARN if you have previously created one, or we will create one for you",
            default="",
            type=click.STRING,
        )

    def _prompt_pipeline_execution_role(self) -> None:
        self.pipeline_execution_role_arn = click.prompt(
            "Enter the pipeline execution role ARN if you have previously created one, "
            "or we will create one for you",
            default="",
            type=click.STRING,
        )

    def _prompt_cloudformation_execution_role(self) -> None:
        self.cloudformation_execution_role_arn = click.prompt(
            "Enter the CloudFormation execution role ARN if you have previously created one, "
            "or we will create one for you",
            default="",
            type=click.STRING,
        )

    def _prompt_artifacts_bucket(self) -> None:
        self.artifacts_bucket_arn = click.prompt(
            "Please enter the artifact bucket ARN for your Lambda function. "
            "If you do not have a bucket, we will create one for you",
            default="",
            type=click.STRING,
        )

    def _prompt_image_repository(self) -> None:
        if click.confirm("Does your application contain any IMAGE type Lambda functions?"):
            self.image_repository_arn = click.prompt(
                "Please enter the ECR image repository ARN(s) for your Image type function(s)."
                "If you do not yet have a repository, we will create one for you",
                default="",
                type=click.STRING,
            )
            self.create_image_repository = not bool(self.image_repository_arn)
        else:
            self.create_image_repository = False

    def _get_user_inputs(self) -> List[Tuple[str, Callable[[], None]]]:
        return [
            (f"Account: {get_current_account_id(self.profile)}", self._prompt_account_id),
            (f"Stage name: {self.environment_name}", self._prompt_stage_name),
            (f"Region: {self.region}", self._prompt_region_name),
            (
                f"Pipeline user ARN: {self.pipeline_user_arn}"
                if self.pipeline_user_arn
                else "Pipeline user: [to be created]",
                self._prompt_pipeline_user,
            ),
            (
                f"Pipeline execution role ARN: {self.pipeline_execution_role_arn}"
                if self.pipeline_execution_role_arn
                else "Pipeline execution role: [to be created]",
                self._prompt_pipeline_execution_role,
            ),
            (
                f"CloudFormation execution role ARN: {self.cloudformation_execution_role_arn}"
                if self.cloudformation_execution_role_arn
                else "CloudFormation execution role: [to be created]",
                self._prompt_cloudformation_execution_role,
            ),
            (
                f"Artifacts bucket ARN: {self.artifacts_bucket_arn}"
                if self.artifacts_bucket_arn
                else "Artifacts bucket: [to be created]",
                self._prompt_artifacts_bucket,
            ),
            (
                f"ECR image repository ARN: {self.image_repository_arn}"
                if self.image_repository_arn
                else f"ECR image repository: [{'to be created' if self.create_image_repository else 'skipped'}]",
                self._prompt_image_repository,
            ),
        ]

    def run(self) -> None:  # pylint: disable=too-many-branches
        """
        Runs an interactive questionnaire to prompt the user for the ARNs of the AWS resources(infrastructure) required
        for the pipeline to work. Users can provide all, none or some resources' ARNs and leave the remaining empty
        and it will be created by the bootstrap command
        """
        click.secho(self.color.bold("[1] Stage definition"))
        if self.environment_name:
            click.echo(f"Stage name: {self.environment_name}")
        else:
            self._prompt_stage_name()
        click.echo()

        click.secho(self.color.bold("[2] Account details"))
        self._prompt_account_id()
        click.echo()

        if not self.region:
            self._prompt_region_name()

        if self.pipeline_user_arn:
            click.echo(f"Pipeline IAM user ARN: {self.pipeline_user_arn}")
        else:
            self._prompt_pipeline_user()
        click.echo()

        click.secho(self.color.bold("[3] Reference application build resources"))

        if self.pipeline_execution_role_arn:
            click.echo(f"Pipeline execution role ARN: {self.pipeline_execution_role_arn}")
        else:
            self._prompt_pipeline_execution_role()
        click.echo()

        if self.cloudformation_execution_role_arn:
            click.echo(f"CloudFormation execution role ARN: {self.cloudformation_execution_role_arn}")
        else:
            self._prompt_cloudformation_execution_role()
        click.echo()

        if self.artifacts_bucket_arn:
            click.echo(f"Artifacts bucket ARN: {self.cloudformation_execution_role_arn}")
        else:
            self._prompt_artifacts_bucket()
        click.echo()

        if self.image_repository_arn:
            click.echo(f"ECR image repository ARN: {self.image_repository_arn}")
        else:
            self._prompt_image_repository()
        click.echo()

        # Ask customers to confirm the inputs
        click.secho(self.color.bold("[5] Summary"))
        while True:
            inputs = self._get_user_inputs()
            click.secho("Below is the summary of the answers:")
            for i, (text, _) in enumerate(inputs):
                click.secho(f"  {i + 1}. {text}")
            edit_input = click.prompt(
                text="Press enter to confirm the values above, or select an item to edit the value",
                default="0",
                show_choices=False,
                show_default=False,
                type=click.Choice(["0"] + [str(i + 1) for i in range(len(inputs))]),
            )
            if int(edit_input):
                inputs[int(edit_input) - 1][1]()
                click.echo()
            else:
                break
