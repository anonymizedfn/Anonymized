import subprocess
import os
import re
import csv
import git
from datetime import datetime

REPO_PATH = "../src/"
FILE_PATH = "third_party/WebKit/Source/platform/RuntimeEnabledFeatures.in"
OUTPUT_CSV = "../runtime_in_status_changes.csv"


def get_git_log_with_diff():
    """
    Use GitPython to get the full diff history of a file with commit metadata,
    similar to `git log --follow --full-history -p --format=...`.
    """
    repo = git.Repo(REPO_PATH)
    return repo.git.log(
        "--follow",
        "--full-history",
        "-p",
        "--format=--COMMIT--%n%H%n%cI",
        "--",
        FILE_PATH
    )

def extract_changes_from_log(log_text):
    changes = []
    current_commit = None
    current_date = None

    lines = log_text.splitlines()
    for i, line in enumerate(lines):
        if line.startswith("--COMMIT--"):
            current_commit = lines[i + 1].strip()
            current_date = lines[i + 2].strip()
            continue

        # Look for lines with status=... (ignoring comments and blanks)
        match = re.match(r'^([+\-])\s*([A-Za-z0-9_]+)\s+.*?\bstatus\s*=\s*([a-zA-Z_]+)', line)
        if match:
            sign = match.group(1)
            toggle_name = match.group(2)
            status_value = match.group(3)

            changes.append({
                "commit": current_commit,
                "date": current_date,
                "toggle": toggle_name,
                "change_type": "add" if sign == "+" else "remove",
                "status": status_value
            })

    return changes

def save_to_csv(changes, output_path):
    with open(output_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["commit", "date", "toggle", "change_type", "status"])
        writer.writeheader()
        for row in changes:
            writer.writerow(row)

def main():
    log_text = get_git_log_with_diff()
    changes = extract_changes_from_log(log_text)
    save_to_csv(changes, OUTPUT_CSV)
    print(f"Saved {len(changes)} status changes to {OUTPUT_CSV}")

if __name__ == "__main__":
    main()
