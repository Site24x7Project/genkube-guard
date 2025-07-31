import subprocess
import uuid
import os
import tempfile
import logging

logger = logging.getLogger("genkube")

def run_kube_linter(yaml_bytes: bytes):
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".yaml") as tmp:
            tmp.write(yaml_bytes)
            temp_file = tmp.name

        kube_linter_path = "tools/kube-linter.exe" if os.name == "nt" else "kube-linter"

        result = subprocess.run(
            [kube_linter_path, "lint", temp_file],
            capture_output=True,
            text=True,
            check=False
        )

        output = result.stdout.strip()
        error_output = result.stderr.strip()

        lines = [line.strip() for line in output.splitlines() if line.strip()]

        issues = []
        for line in lines:
            if "kubelinter" in line.lower():
                continue
            if ":" not in line:
                continue
            issues.append(line)

        if not issues:
            if error_output:
                logger.warning("kube-linter stderr: %s", error_output)
            return [" No lint issues found."]

        return issues

    except Exception as e:
        logger.exception("Error running kube-linter")
        return [f"Error running kube-linter: {str(e)}"]

    finally:
        if os.path.exists(temp_file):
            os.remove(temp_file)
