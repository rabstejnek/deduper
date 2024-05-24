import json
from pathlib import Path

HERE = Path(__file__).parent.parent


def main():
    """
    Clean the manifest does the following:
    1. Change locale setting to utf8
    2. Replace windows paths \\ with /
    3. Remove files in .git and venv
    An issue has been reported to fix the third item:
    https://github.com/rstudio/rsconnect-python/issues/285
    """
    fn = HERE / "manifest.json"
    data = json.loads(fn.read_text())

    data["locale"] = "en_US.utf8"
    new_files = {}
    keep_matches = {"pyproject.toml", "requirements.txt", "src/deduper"}
    skip_matches = {"__pycache__", "ord-sem"}
    for key, value in data["files"].items():
        if not any(key.startswith(prefix) for prefix in keep_matches):
            continue
        if any(phrase in key for phrase in skip_matches):
            continue
        new_files[key.replace("\\", "/")] = value
    data["files"] = new_files
    data["metadata"]["primary_html"] = "Deduper"
    data["python"]["version"] = "3.11.0"
    fn.write_text(json.dumps(data, indent=2))


if __name__ == "__main__":
    main()
