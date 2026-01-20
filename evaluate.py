import json

OUTPUT_FILE = "output.json"
GROUND_TRUTH_FILE = "ground_truth.json"

FIELDS = [
    "product_line",
    "origin_port_code",
    "origin_port_name",
    "destination_port_code",
    "destination_port_name",
    "incoterm",
    "cargo_weight_kg",
    "cargo_cbm",
    "is_dangerous"
]

def load_output():
    with open(OUTPUT_FILE, "r") as f:
        return json.load(f)

def load_ground_truth():
    with open(GROUND_TRUTH_FILE, "r") as f:
        return json.load(f)

def normalize_string(s):
    if s is None:
        return None
    return str(s).strip().lower()

def normalize_float(f):
    if f is None:
        return None
    return round(float(f), 2)

def compare_values(field, a, b):
    if field in ["product_line", "origin_port_code", "origin_port_name", "destination_port_code", "destination_port_name", "incoterm"]:
        return normalize_string(a) == normalize_string(b)

    if field in ["cargo_weight_kg", "cargo_cbm"]:
        return normalize_float(a) == normalize_float(b)

    if field == "is_dangerous":
        return a == b

    return False

def main():
    output = load_output()
    ground_truth = load_ground_truth()

    gt_dict = {item["id"]: item for item in ground_truth}

    total_fields = 0
    total_correct = 0

    for item in output:
        email_id = item["id"]
        actual = gt_dict.get(email_id)

        if not actual:
            print(f"✗ {email_id} not found in ground truth")
            continue

        for field in FIELDS:
            total_fields += 1
            if compare_values(field, item.get(field), actual.get(field)):
                total_correct += 1
            else:
                print(f"✗ {field}: {item.get(field)} != {actual.get(field)}")

    overall_accuracy = total_correct / total_fields * 100
    print(f"\nOverall Accuracy: {overall_accuracy:.2f}%")
    print(f"Correct fields: {total_correct} / {total_fields}")

if __name__ == "__main__":
    main()
