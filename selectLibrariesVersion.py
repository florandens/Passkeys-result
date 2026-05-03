import json
import re
import requests
from urllib.parse import urlparse

import tldextract
SIMPLEWEBAUTHN_REGEX = r"browser@(\d+\.\d+\.\d+)"
JSONWEBAUTHN_REGEX = r"webauthn-json"
WPWEBAUTHN_REGEX = r"wp-webauthn"
VERSION_REGEX = r"ver=(\d+\.[^\s/]+)"
SECUREPASSKEYS_REGEX = r"secure-passkeys"
def read_json_file(file_path, encoding="utf-8"):
    with open(file_path, "r", encoding=encoding) as f:
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

def AddtimeStamp(data):
    webauthmVersion = read_json_file("versionList/simplewebauthnVersionList.json", encoding="utf-16") #list create by npm view @simplewebauthn/browser time --json > simplewebauthnVersionList.json
    wpwebauthnVersion = read_json_file("versionList/wp-webauthnVersionList.json") #list is created by github tags https://github.com/yrccondor/wp-webauthn/releases
    securePasskeysVersion = read_json_file("versionList/securePasskeysVersionList.json") #list create by https://wordpress.org/plugins/secure-passkeys/#developers
    webautnJsonVersion = read_json_file("versionList/webauthnJsonVersionList.json") #list create by npm view @simplewebauthn/webauthn-json time --json > webauthn-jsonVersionList.json
    for website, value in data.items():
        match_sim = re.search(SIMPLEWEBAUTHN_REGEX, value["librariesHit"], re.IGNORECASE)
        match_wp = re.search(WPWEBAUTHN_REGEX, value["url"], re.IGNORECASE)
        match_securePasskeys = re.search(SECUREPASSKEYS_REGEX, value["url"], re.IGNORECASE)
        match_json = re.search(JSONWEBAUTHN_REGEX, value["url"], re.IGNORECASE)

        if match_sim:
            version = match_sim.group(1)
            timestamp = webauthmVersion.get(version)
            if timestamp:
                value["timestamp"] = timestamp

        elif match_wp:
            match_wp = re.search(VERSION_REGEX, value["librariesHit"], re.IGNORECASE)
            if match_wp:
                timestamp = wpwebauthnVersion.get(match_wp.group(1))
                if timestamp:
                    value["timestamp"] = timestamp

        elif match_securePasskeys:
                match_securePasskeys = re.search(VERSION_REGEX, value["librariesHit"], re.IGNORECASE)
                timestamp = securePasskeysVersion.get(match_securePasskeys.group(1))
                if timestamp:
                    value["timestamp"] = timestamp

        elif match_json:
                match_json = re.search(VERSION_REGEX, value["librariesHit"], re.IGNORECASE)
                if not match_json:
                    timestamp = webautnJsonVersion.get(value["librariesHit"])
                else:
                    timestamp = webautnJsonVersion.get(match_json.group(1))

                if timestamp:
                    value["timestamp"] = timestamp
    return data

def main():
    regex_pattern = [
        r"ver=\d+\.[^\s/]+",        # ver=1.2.3
        SIMPLEWEBAUTHN_REGEX,    # browser@6.2.2
        r"\b(?!127\.0\.0\b)\d+\.\d+\.\d+\b"       # version numbers, remove local ips
    ]

    data = read_json_file("api_calls_with_keywords.json")

    analyzed_data = analyze_libraries(
         data,
        regex_pattern,
        remove_domain="yubico"
     )
    filtered = filter_sites_with_hits(analyzed_data)
    filtered_timestamps = AddtimeStamp(filtered)
    write_json_file(filtered_timestamps, "analyzed_libraries_with_timestamps.json")
    

if __name__ == "__main__":
    main()