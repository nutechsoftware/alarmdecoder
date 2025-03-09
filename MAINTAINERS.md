# Maintainers

This document is intended for maintainers of the `nutechsoftware/alarmdecoder` repository.

It summarizes information about the automated processes involved with the repository.

## GitHub Actions Automation

This section describes how GitHub Actions is used to automate test and release processes for the `nutechsoftware/alarmdecoder` repository. GitHub Actions is free for public repositories. More information about GitHub Actions can be found on their official documentation site here: https://docs.github.com/en/actions.

### Reusable Actions

The GitHub Actions workflows described below make use of [composite actions](https://docs.github.com/en/actions/sharing-automations/creating-actions/creating-a-composite-action) to help consolidate common workflow steps.

These actions are found in the [.github/actions](./.github/actions) directory. Each action has a `description` field at the top of the file that describes its purpose.

### Workflows

The GitHub Actions workflows can be found in the [.github/workflows](./.github/workflows) directory. Each workflow has a comment at the top of the file that describes its purpose.

The sections below further delineate between automated and manual workflows that are in use. More information on triggering workflows (both automatically and manually) can be found here: https://docs.github.com/en/actions/writing-workflows/choosing-when-your-workflow-runs/triggering-a-workflow.

#### Automated Workflows

Some workflows are configured to run automatically based on certain GitHub events. Examples of these workflows are listed below:

- `pr.yaml` - runs in response to pull requests being opened
- `merge.yaml` - runs anytime a change is pushed to the `master` branch (i.e. when a PR is merged)

#### Manual Workflows

Some workflows are configured to run based on a manual invocation from a maintainer. Examples of these workflows are listed below:

- `release.yaml` - runs a workflow to build, test, and release the `alarmdecoder` Python packages to PyPI

More information on manually triggering GitHub Actions workflows can be found here: https://docs.github.com/en/actions/managing-workflow-runs-and-deployments/managing-workflow-runs/manually-running-a-workflow.
