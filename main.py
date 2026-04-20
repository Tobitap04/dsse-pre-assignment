import re

from pydriller import Repository
from pydriller.domain.commit import ModificationType
from git.exc import GitCommandError


def find_unique_issue_commits(repo_url, issue_ids):
    issue_patterns = [re.compile(rf"\b{re.escape(issue_id)}\b", re.IGNORECASE) for issue_id in issue_ids]
    matching_commit_hashes = set()

    for commit in Repository(repo_url).traverse_commits():
        message = commit.msg or ""
        if any(pattern.search(message) for pattern in issue_patterns):
            matching_commit_hashes.add(commit.hash)

    return matching_commit_hashes


def average_unique_changed_files_per_commit(repo_url, commit_hashes):
    total_commits = len(commit_hashes)
    if total_commits == 0:
        return 0.0

    unique_modified_paths = set()

    for commit in Repository(repo_url).traverse_commits():
        if commit.hash not in commit_hashes:
            continue

        try:
            for modified_file in commit.modified_files:
                if modified_file.change_type in {
                    ModificationType.ADD,
                    ModificationType.MODIFY,
                    ModificationType.DELETE,
                }:
                    path = modified_file.new_path or modified_file.old_path
                    if path:
                        unique_modified_paths.add(path)
        except GitCommandError:
            # Treat unreadable diffs as zero file contribution for this commit.
            continue

    return len(unique_modified_paths) / total_commits


def average_dmm_score_per_commit(repo_url, commit_hashes):
    total_commits = len(commit_hashes)
    if total_commits == 0:
        return 0.0

    dmm_total = 0.0

    for commit in Repository(repo_url).traverse_commits():
        if commit.hash not in commit_hashes:
            continue

        dmm_unit_size = commit.dmm_unit_size or 0.0
        dmm_unit_complexity = commit.dmm_unit_complexity or 0.0
        dmm_unit_interfacing = commit.dmm_unit_interfacing or 0.0
        commit_dmm_score = (dmm_unit_size + dmm_unit_complexity + dmm_unit_interfacing) / 3.0
        dmm_total += commit_dmm_score

    return dmm_total / total_commits


def main():
    issue_ids = ["LUCENE-12", "LUCENE-17", "LUCENE-701", "LUCENE-1200", "LUCENE-1799"]
    repo_url = "https://github.com/apache/lucene"

    unique_commits = find_unique_issue_commits(repo_url, issue_ids)
    avg_unique_files_per_commit = average_unique_changed_files_per_commit(repo_url, unique_commits)
    avg_dmm_score = average_dmm_score_per_commit(repo_url, unique_commits)

    print("Total commits analyzed: ", len(unique_commits))
    print("Average number of files changed: ", avg_unique_files_per_commit)
    print("Average DMM metrics: ", avg_dmm_score)
    

if __name__ == "__main__":
    main()