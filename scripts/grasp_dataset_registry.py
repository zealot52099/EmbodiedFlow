"""Validate and summarize the grasp pipeline dataset registry."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any


REQUIRED_FIELDS = {
    "id",
    "name",
    "category",
    "source_url",
    "license",
    "has_action",
    "has_language",
    "has_3d_or_depth",
    "embodiment",
    "download",
    "recommended_role",
}


def load_registry(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_registry(registry: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    categories = set(registry.get("categories", []))
    seen_ids: set[str] = set()
    datasets = registry.get("datasets", [])

    if not isinstance(datasets, list) or not datasets:
        errors.append("registry.datasets must be a non-empty list")
        return errors

    for index, dataset in enumerate(datasets):
        missing = sorted(REQUIRED_FIELDS - set(dataset))
        if missing:
            errors.append(f"datasets[{index}] missing fields: {', '.join(missing)}")
        dataset_id = dataset.get("id")
        if dataset_id in seen_ids:
            errors.append(f"duplicate dataset id: {dataset_id}")
        seen_ids.add(dataset_id)
        if dataset.get("category") not in categories:
            errors.append(f"{dataset_id}: invalid category {dataset.get('category')!r}")
        for key in ("has_action", "has_language", "has_3d_or_depth"):
            if key in dataset and not isinstance(dataset[key], bool):
                errors.append(f"{dataset_id}: {key} must be boolean")
    return errors


def write_summary(registry: dict[str, Any], output: Path) -> None:
    datasets = registry["datasets"]
    counts = Counter(item["category"] for item in datasets)
    lines = [
        "# Grasp Dataset Registry",
        "",
        f"Schema version: `{registry.get('schema_version', 'unknown')}`",
        f"Updated at: `{registry.get('updated_at', 'unknown')}`",
        "",
        "## Category Counts",
        "",
    ]
    for category in registry.get("categories", []):
        lines.append(f"- `{category}`: {counts.get(category, 0)}")
    lines.extend(["", "## Datasets", ""])
    lines.append("| id | category | action | language | 3d/depth | role |")
    lines.append("| --- | --- | --- | --- | --- | --- |")
    for item in datasets:
        lines.append(
            "| {id} | {category} | {action} | {language} | {depth} | {role} |".format(
                id=item["id"],
                category=item["category"],
                action="yes" if item["has_action"] else "no",
                language="yes" if item["has_language"] else "no",
                depth="yes" if item["has_3d_or_depth"] else "no",
                role=item["recommended_role"].replace("|", "/"),
            )
        )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--registry", default="data/grasp_dataset_registry.json")
    parser.add_argument("--summary-output", default="artifacts/grasp_pipeline/dataset_registry_summary.md")
    args = parser.parse_args()

    registry_path = Path(args.registry).resolve()
    registry = load_registry(registry_path)
    errors = validate_registry(registry)
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        raise SystemExit(1)

    summary_output = Path(args.summary_output).resolve()
    write_summary(registry, summary_output)
    print(f"Validated {len(registry['datasets'])} datasets from {registry_path}")
    print(f"Wrote summary: {summary_output}")


if __name__ == "__main__":
    main()
