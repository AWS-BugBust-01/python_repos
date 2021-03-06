from unittest import TestCase

from aws_lambda_builders.architecture import X86_64, ARM64

from aws_lambda_builders.workflows.go_dep.workflow import GoDepWorkflow
from aws_lambda_builders.workflows.go_dep.actions import DepEnsureAction, GoBuildAction


class TestGoDepWorkflow(TestCase):
    """
    The workflow requires an external tool, dep to run. It will need to be tested with integration
    tests. These are just tests to provide quick feedback if anything breaks
    """

    def test_workflow_sets_up_workflow(self):
        workflow = GoDepWorkflow(
            "source", "artifacts", "scratch", "manifest", options={"artifact_executable_name": "foo"}
        )

        self.assertEqual(len(workflow.actions), 2)
        self.assertIsInstance(workflow.actions[0], DepEnsureAction)
        self.assertIsInstance(workflow.actions[1], GoBuildAction)

    def test_must_validate_architecture(self):
        workflow = GoDepWorkflow(
            "source",
            "artifacts",
            "scratch",
            "manifest",
            options={"artifact_executable_name": "foo"},
        )
        workflow_with_arm = GoDepWorkflow(
            "source",
            "artifacts",
            "scratch",
            "manifest",
            options={"artifact_executable_name": "foo"},
            architecture=ARM64,
        )

        self.assertEqual(workflow.architecture, "x86_64")
        self.assertEqual(workflow_with_arm.architecture, "arm64")
