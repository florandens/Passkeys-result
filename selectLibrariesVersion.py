import json
import re
import requests
from urllib.parse import urlparse

import tldextract


def read_json_file(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def write_json_file(data, file_path):
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def fetch_js(url):
    try:
        resp = requests.get(url, timeout=8)
        if resp.status_code == 200 and "javascript" in resp.headers.get("content-type", ""):
            return resp.text
    except Exception as e:
        print(f"Failed to fetch {url}: {e}")
    return None


def analyze_libraries(data, regex_pattern, remove_domain=None):

    keyForLibrariesHits = "librariesHit"
    result = {}

    visited_urls = set()
    cache = {}
    for website, librariesHits in data.items():
        # skip unwanted domains
        if remove_domain and tldextract.extract(website).domain == remove_domain:
            continue

        for entry in librariesHits:
            if not isinstance(entry, dict):
                continue

            found = False

            for value in list(entry.values()): #make list to avoid runtime error due to dict size change
                if not isinstance(value, str):
                    continue

                for pattern in regex_pattern:
                    match = re.search(pattern, value, re.IGNORECASE)
                    if match:
                        entry[keyForLibrariesHits] = match.group(0)
                        found = True
                        break

                if found:
                    break

            if not found:
                for value in entry.values():

                    if value in visited_urls:
                        js_code = cache.get(value)
                    else:
                        visited_urls.add(value)
                        js_code = fetch_js(value)
                        cache[value] = js_code

                    if not js_code: #in CSS and mv4 files we can not found versions
                        continue

                    for pattern in regex_pattern:
                        match = re.search(pattern, js_code, re.IGNORECASE)
                        if match:
                            entry[keyForLibrariesHits] = match.group(0)
                            found = True
                            break

                    if found:
                        break

        result[website] = librariesHits

    return result


def filter_sites_with_hits(data):
    filtered = {}
    for website, libs in data.items():
        if not isinstance(libs, list):
            continue
        for entry in libs:
            if isinstance(entry, dict) and "librariesHit" in entry:
                filtered[website] = entry   # store ONLY the first match
                break
    return filtered

def main():
    regex_pattern = [
        r"ver=\d+\.[^\s/]+",        # ver=1.2.3
        r"browser@[^\s/]+",    # browser@6.2.2
        r"\b(?!127\.0\.0\b)\d+\.\d+\.\d+\b"       # version numbers, remove local ips
    ]

    data = read_json_file("api_calls_with_keywords.json")

    analyzed_data = analyze_libraries(
        data,
        regex_pattern,
        remove_domain="yubico"
    )

    filtered = filter_sites_with_hits(analyzed_data)
    print(len(filtered))

    write_json_file(filtered, "analyzed_libraries.json")


if __name__ == "__main__":
    main()