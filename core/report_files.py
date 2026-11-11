"""Pure report-file resolution helpers, independent of Chainlit."""
from datetime import datetime
from pathlib import Path


def resolve_report_files(startup_path, structured=None):
    if structured is not None:
        run_id = structured["run_id"]
        root = Path(structured["output_dir"])
    else:
        run_id = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        root = Path(startup_path)
    return {"run_id": run_id, "html_path": str(root / "Business_Plan.html") if structured is not None else str(root / f"business_plan_{run_id}.html"), "json_path": str(root / "Business_Plan.json") if structured is not None else str(root / f"business_plan_{run_id}.json"), "html_name": f"Business_Plan_{run_id}.html", "json_name": f"Business_Plan_{run_id}.json"}
