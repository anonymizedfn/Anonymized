import requests
import json
import pandas as pd
from datetime import datetime

def get_chromium_releases(start_milestone=1, end_milestone=120):
    releases = []
    channel = "Stable"
    
    for milestone in range(start_milestone, end_milestone + 1):
        url = f"https://chromiumdash.appspot.com/fetch_releases?milestone={milestone}&channel={channel}"
        response = requests.get(url)
        
        if response.status_code != 200:
            print(f"Failed to fetch data for milestone {milestone}, channel {channel}")
            continue
        
        try:
            data = json.loads(response.text)
        except json.JSONDecodeError:
            print(f"Failed to parse JSON response for milestone {milestone}, channel {channel}")
            continue
        
        if not isinstance(data, list):
            print(f"Unexpected data format for milestone {milestone}, channel {channel}")
            continue
        
        for release in data:
            milestone = release.get("milestone")
            version = release.get("version")
            timestamp = release.get("time")
            platform = release.get("platform")
            
            if milestone and version and timestamp and platform:
                release_date = datetime.utcfromtimestamp(timestamp / 1000).strftime('%Y-%m-%d %H:%M:%S')
                releases.append({
                    "Milestone": milestone,
                    "Version": version,
                    "Release Date": release_date,
                    "Platform": platform
                })
    
    return releases

def main():
    releases = get_chromium_releases(start_milestone=1, end_milestone=140)
    if releases:
        df = pd.DataFrame(releases)
        df.to_csv("chromium_releases.csv", index=False)
        print("Data saved to chromium_releases.csv")
    else:
        print("No data available")

if __name__ == "__main__":
    main()
