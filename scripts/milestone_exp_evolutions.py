import subprocess
import re
import pandas as pd
from datetime import datetime
import os
import git 

REPO_PATH = "../src/"
FILE_PATH = "chrome/browser/flag-metadata.json"



def run_git_log_with_diff():
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

def extract_expiry_changes(git_log_output):
    changes = []
    lines = git_log_output.splitlines()
    current_commit = None
    current_date = None

    for i, line in enumerate(lines):
        if line.startswith("--COMMIT--"):
            current_commit = lines[i + 1].strip()
            current_date = lines[i + 2].strip()
            continue

        # Look for added or removed expiry_milestone
        expiry_match = re.match(r'^[\+\-]\s*"expiry_milestone"\s*:\s*(\d+)', line)
        if expiry_match:
            change_type = "add" if line.startswith("+") else "remove"
            expiry_value = int(expiry_match.group(1))

            # Look back for the nearest name
            name = None
            for j in range(i - 1, max(i - 15, 0), -1):
                name_match = re.match(r'^[\+\-\s]*["]?name["]?\s*:\s*"([^"\n]+)"', lines[j])
                if name_match:
                    name = name_match.group(1)
                    break

            if name:
                changes.append({
                    "commit": current_commit,
                    "date": current_date,
                    "toggle": name,
                    "change_type": change_type,
                    "expiry_milestone": expiry_value
                })

    return pd.DataFrame(changes)

def main():
    log_output = run_git_log_with_diff()
    df_expiry = extract_expiry_changes(log_output)
    df_expiry.to_csv("../expiry_milestone_changes.csv", index=False)
    print("Saved expiry milestone change history to expiry_milestone_changes.csv")
    print(df_expiry.head())

if __name__ == "__main__":
    main()
