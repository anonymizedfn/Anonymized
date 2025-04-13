import re

# Set the path to the git_log.txt file
git_log_file = "git_log.txt"

# Read the contents of the file
with open(git_log_file, "r", encoding="utf-8") as file:
    lines = file.readlines()

commits = []
current_commit = None
added_lines = 0
removed_lines = 0
changed_files = 0

for line in lines:
    line = line.strip()
    if re.match(r"^[0-9a-f]{40}$", line):  # Full commit hash
        if current_commit:  # Save previous commit stats
            commits.append((current_commit, changed_files, added_lines, removed_lines))
        current_commit = line
        added_lines = 0
        removed_lines = 0
        changed_files = 0
    elif line:  # File change stats
        parts = line.split("\t")
        if len(parts) == 3:
            try:
                added_lines += int(parts[0]) if parts[0] != '-' else 0
                removed_lines += int(parts[1]) if parts[1] != '-' else 0
                changed_files += 1
            except ValueError:
                pass  # Ignore invalid entries

# Add last commit
if current_commit:
    commits.append((current_commit, changed_files, added_lines, removed_lines))

# Print results
for commit in commits:
    print(f"{commit[0]},{commit[1]},{commit[2]},{commit[3]}")
