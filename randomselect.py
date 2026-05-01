import json
import random

INPUT_FILE = "passkey_urls.json"
OUTPUT_FILE = "random_selection_passkeys.json"
SAMPLE_SIZE = 55

def main():
    random.seed(42)
    # Load input JSON
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    domains = data.get("domains", [])

    if not isinstance(domains, list):
        raise ValueError("Invalid format: 'domains' must be a list")

    # Ensure we don't exceed available domains
    sample_size = min(SAMPLE_SIZE, len(domains))

    # Random unique selection
    selected = random.sample(domains, sample_size)

    # Prepare output structure
    output_data = {
        "count": sample_size,
        "domains": selected
    }

    # Write output JSON
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2)

    print(f"Saved {sample_size} domains to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()