import subprocess
import os
import re
import csv
import git
from datetime import datetime

# Update this to point to your Chromium repo and file path
REPO_PATH = "../src/"
FILE_PATH = "third_party/blink/renderer/platform/runtime_enabled_features.json5"
OUTPUT_CSV = "../toggle_status_changes.csv"

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
        "-U20",
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

        if re.match(r"^[\+\-]\s*status\s*:", line):
            change_type = "add" if line.startswith("+") else "remove"
            status_value = line.split(":", 1)[1].strip().strip(",").strip('"')

            # Look for the nearest name field before this line
            name = None
            for j in range(i - 1, max(i - 10, 0), -1):
                #name_match = re.search(r'^\s*(?:"name"|name)\s*:\s*"([^"\n]+)"', lines[j])
                name_match = re.search(r'^[\+\-\s]*["]?name["]?\s*:\s*"([^"\n]+)"', lines[j])

                if name_match:
                    name = name_match.group(1)
                    break

            if name:
                changes.append({
                    "commit": current_commit,
                    "date": current_date,
                    "toggle": name,
                    "change_type": change_type,
                    "status": status_value
                })

    return changes

def save_to_csv(changes, output_path):
    with open(output_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["commit", "date", "toggle", "change_type", "status"])
        writer.writeheader()
        for row in changes:
            print(row)
            writer.writerow(row)

def main():
    log_text = get_git_log_with_diff()
    changes = extract_changes_from_log(log_text)
    save_to_csv(changes, OUTPUT_CSV)
    print(f"Saved {len(changes)} status changes to {OUTPUT_CSV}")

if __name__ == "__main__":
    main()
