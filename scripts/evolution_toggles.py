import os
import json
import git
import re
import pandas as pd
from datetime import datetime

def get_file_versions(repo_dir, file_path):
    """
    Get all historical versions of a file, including renames, using git log --follow --name-status.
    """
    repo = git.Repo(repo_dir)
    log_data = repo.git.log("--follow", "--name-status", "--", file_path)
    file_versions = [file_path]  # Start with the latest version
    
    for line in log_data.split("\n"):
        parts = line.split("\t")
        if len(parts) == 3 and parts[0].startswith("R"):  # Rename detected
            file_versions.append(parts[1])  # Store previous file name
    
    return file_versions

def get_file_diff_history(repo_dir, file_version):
    """
    Get the full history of all versions of a file, including patches, ensuring --follow works.
    """
    repo = git.Repo(repo_dir)
    log_entries = []
    
    #for file_version in file_versions:
    log_data = repo.git.log("-p", "--follow", "--full-history", "--", file_version)
    log_entries.append(log_data)
    
    return "\n".join(log_entries)  # Combine all histories

def parse_toggle_changes(repo_dir, file_path):
    """
    Parses feature toggles and switch-related options from a file's git history.
    Detects added/removed JSON toggles and C++ switches, even when spread across multiple lines.
    """
    data = []
    
    log_data = get_file_diff_history(repo_dir, file_path)
    commit_id, commit_date, commit_msg = None, None, ""
    collecting_message = False
    change_id = None
    reviewed_on = None
    
    for line in log_data.split("\n"):
        
        commit_match = re.match(r"^commit ([0-9a-f]{40})", line)
        date_match = re.match(r"^Date:\s*(.*)", line)
        change_id_match = re.search(r'Change-Id:\s*([A-Za-z0-9]+)', line)
        reviewed_on_match = re.search(r'Reviewed-on:\s*(https?://[^\s]+)', line)
        diff_match = re.match(r"^diff --git", line)
        
        if commit_match:
            commit_id = commit_match.group(1)
            commit_msg = ""
            collecting_message = True  # Start collecting commit message
        elif date_match:
            commit_date = datetime.strptime(date_match.group(1).strip(), "%a %b %d %H:%M:%S %Y %z").isoformat()
        elif diff_match:
            collecting_message = False  # Stop collecting commit message when diff starts
        elif collecting_message and line.strip():
            commit_msg += line.strip() + " "  # Collect commit message
        
        #add_match = re.search(r'^\+\s*(?:"name"|name)\s*:\s*"([^"\n]+)"', line)
        #remove_match = re.search(r'^\-\s*(?:"name"|name)\s*:\s*"([^"\n]+)"', line)

        
        switch_add_match = re.search(r'\+\s*const (?:char|wchar) (k[A-Za-z0-9_]+)\[\] = ', line)
        switch_remove_match = re.search(r'-\s*const (?:char|wchar) (k[A-Za-z0-9_]+)\[\] = ', line)
        
        # RuntimeEnabledFeatures.in toggle line
        add_match = re.match(r'^\+\s*([A-Za-z_][A-Za-z0-9_]*)', line)
        remove_match = re.match(r'^\-\s*([A-Za-z_][A-Za-z0-9_]*)', line)


        if change_id_match:
            change_id = change_id_match.group(1)
            
        if reviewed_on_match:
            reviewed_on = reviewed_on_match.group(1)
        
        if add_match and commit_id and commit_date:
            feature = add_match.group(1)
            data.append({
                "file_name": file_path,
                "feature": feature,
                "variable": None,
                "commit_id": commit_id,
                "commit_date": commit_date,
                "change_type": "added",
                "commit_message": commit_msg.strip(),
                "change_id": change_id,
                "reviewed_on": reviewed_on
            })
        
        if remove_match and commit_id and commit_date:
            feature = remove_match.group(1)
            data.append({
                "file_name": file_path,
                "feature": feature,
                "variable": None,
                "commit_id": commit_id,
                "commit_date": commit_date,
                "change_type": "removed",
                "commit_message": commit_msg.strip(),
                "change_id": change_id,
                "reviewed_on": reviewed_on
            })
        
        if switch_add_match and commit_id and commit_date:
            feature = switch_add_match.group(1)
            data.append({
                "file_name": file_path,
                "feature": feature,
                "variable": None,
                "commit_id": commit_id,
                "commit_date": commit_date,
                "change_type": "added",
                "commit_message": commit_msg.strip(),
                "change_id": change_id,
                "reviewed_on": reviewed_on
            })
        
        if switch_remove_match and commit_id and commit_date:
            feature = switch_remove_match.group(1)
            data.append({
                "file_name": file_path,
                "feature": feature,
                "variable": None,
                "commit_id": commit_id,
                "commit_date": commit_date,
                "change_type": "removed",
                "commit_message": commit_msg.strip(),
                "change_id": change_id,
                "reviewed_on": reviewed_on
            })
        
    df = pd.DataFrame(data)
    return df

def find_cc_files(repo_dir):
    """
    Find all .cc files containing 'switch' in their name.
    """
    repo = git.Repo(repo_dir)
    cc_files = repo.git.ls_files("*switches*.cc").split("\n")
    print(cc_files)
    return [file for file in cc_files if file.strip()]

if __name__ == "__main__":
    repo_dir = "../src/"
    files_to_check = [
        #"third_party/blink/renderer/platform/runtime_enabled_features.json5",
        "third_party/WebKit/Source/platform/RuntimeEnabledFeatures.in"# ,
        #"chrome/browser/flag-metadata.json",
    ]
    
    # Find all switch-related .cc files
    #files_to_check.extend(find_cc_files(repo_dir))
    
    all_changes = []
    for file in files_to_check:
        df_changes = parse_toggle_changes(repo_dir, file)
        df_changes.to_csv("toggle_history_C.csv", mode='a', index=False, header=not os.path.exists("toggle_history_C.csv"))
    
    print("Toggle history saved in toggle_history.csv")
