import requests
import gzip
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
import pytz
import os

def fetch_and_filter_epg(output_path, target_channels, timezone_str="Pacific/Auckland"):
    url = "https://watch.livecricketsl.xyz/epg/epg.xml.gz"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }
    response = requests.get(url, headers=headers)
    print(f"[DEBUG] Fetch status code: {response.status_code}")
    if response.status_code != 200:
        print(f"[DEBUG] Response text: {response.text[:300]}")
        raise Exception("Failed to fetch EPG file. The site may be geo-blocked or rejecting connections.")

    with open("epg.xml.gz", "wb") as f:
        f.write(response.content)

    with gzip.open("epg.xml.gz", "rb") as f:
        tree = ET.parse(f)
    root = tree.getroot()

    normalized_channels = {name.lower() for name in target_channels}
    filtered_tv = ET.Element("tv")
    channel_ids = set()

    for channel in root.findall("channel"):
        name = channel.find("display-name").text
        if name and name.strip().lower() in normalized_channels:
            filtered_tv.append(channel)
            channel_ids.add(channel.attrib['id'])

    akl_tz = pytz.timezone(timezone_str)
    now_akl = datetime.now(akl_tz)
    end_akl = now_akl + timedelta(hours=24)
    now_utc = now_akl.astimezone(pytz.utc)
    end_utc = end_akl.astimezone(pytz.utc)

    for programme in root.findall("programme"):
        channel_id = programme.attrib["channel"]
        if channel_id not in channel_ids:
            continue

        start_time = datetime.strptime(programme.attrib["start"].split(" ")[0], "%Y%m%d%H%M%S").replace(tzinfo=timezone.utc)
        stop_time = datetime.strptime(programme.attrib["stop"].split(" ")[0], "%Y%m%d%H%M%S").replace(tzinfo=timezone.utc)

        if now_utc <= stop_time and start_time <= end_utc:
            filtered_tv.append(programme)

    ET.ElementTree(filtered_tv).write(output_path, encoding="utf-8", xml_declaration=True)
    print(f"✅ Filtered EPG saved to {output_path}")

if __name__ == "__main__":
    channels = [
        "Rupavahini", "ITN", "Sirasa", "Siyatha", "Derana", "Hiru", "Supreme TV", "TNL",
        "Channel One", "TV1", "Shakti", "Shakthi", "Shakthi TV", "Cityhitz", "Ridee TV", "Hi TV",
        "Swarnavahini", "TV Derana", "Siyatha TV", "Citi Hitz"
    ]
    output_file = "diaLK.xml"
    fetch_and_filter_epg(output_file, channels)
