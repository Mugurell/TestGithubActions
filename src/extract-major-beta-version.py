#!/usr/bin/env python3

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/


import os, re, sys

from github import Github, InputGitAuthor, enable_console_debug_logging


#
# All these are lifted from relbot/utils.py
#


def major_version_from_release_branch_name(branch_name):
    print(f"Extracting major version from branch: {branch_name}")
    if matches := re.match(r"^releases_v(\d+)\.0($|.0$)", branch_name):
        return int(matches[1])
    raise Exception(f"Unexpected release branch name: {branch_name}")


def get_release_branches(repo):
    print(f"Repo {repo} has {repo.get_branches().totalCount} branches")
    for branch in repo.get_branches():
        print(f"     Branch name: {branch.name}")
    return [branch.name for branch in repo.get_branches()
            if re.match(r"^releases_v\d+\.0\.0$", branch.name)]


def get_latest_release_major_version(repo):
    major_versions = [major_version_from_release_branch_name(branch_name)
                      for branch_name in get_release_branches(repo)]
    print(f"Total major versions discovered:: {len(major_versions)}")
    for i in range(0, len(major_versions)):
        print(f" Major versions identified: {major_versions[i]}")
    if len(major_versions) > 0:
        return sorted(major_versions, reverse=True)[0]


def is_beta_version(version):
    return re.compile(r'\d+.0.0-beta.\d+', re.MULTILINE).match(version)


def is_beta_branch(repository, release_branch_name):
    """Fetch version.txt from the given branch and throw an exception if it is not a Beta release"""
    content_file = repository.get_contents("version.txt", ref=release_branch_name)
    version = content_file.decoded_content.decode('utf8')
    return is_beta_version(version)


#
# Main Action starts here. It expects GITHUB_REPOSITORY to be set.
#

if __name__ == "__main__":

    github = Github()
    if github.get_user() is None:
        print("[E] Could not get authenticated user. Exiting.")
        sys.exit(1)

    verbose = true

    repository = github.get_repo(os.getenv("GITHUB_REPOSITORY"))
    if not repository:
        print("[E] No GITHUB_REPOSITORY set. Exiting.")
        sys.exit(1)

    if verbose:
        print(f"[I] Looking at the \"{repository}\" repository")

    #
    # Actual Action logic starts here. The strategy is very simple:
    #
    # - Find the latest release branch - the branch with highest major release number
    # - Look at version.txt to make sure that branch is actually in Beta
    #

    latest_release_major_version = get_latest_release_major_version(repository)
    if not latest_release_major_version:
        print(f"[E] Could not determine the latest release branch of \"{repository}\"")
        sys.exit(1)

    branch_name = f"releases_v{latest_release_major_version}.0.0"

    if verbose:
        print(f"[I] Looking at branch \"{repository}:{branch_name}\"")

    if not is_beta_branch(repository, branch_name):
        print(f"Branch \"{repository}:{branch_name}\" is not in beta; returning an empty version")
        latest_release_major_version = ""

    if verbose:
        print(f"[I] Latest major beta version is: \"{latest_release_major_version}\"")

    print(f"::set-output name=beta_version::{latest_release_major_version}")