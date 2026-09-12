"""Inject simple obstacle bodies into a MuJoCo XML string.

This module is intentionally independent of LIBERO/robosuite imports so it can
be unit-tested quickly. A future obstacle eval runner can call
``inject_obstacles_into_xml(env.sim.model.get_xml(), scenario)`` before
``reset_from_xml_string``.
"""

from __future__ import annotations

import argparse
import json
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any


DEFAULT_RGBA = {
    "easy": "0.9 0.45 0.15 1",
    "medium": "0.85 0.15 0.12 1",
    "hard": "0.55 0.1 0.7 1",
}


def _size_to_mujoco(shape: str, size_m: list[float]) -> str:
    if shape == "box":
        if len(size_m) != 3:
            raise ValueError(f"box obstacle size must be [x, y, z], got {size_m}")
        return " ".join(f"{value / 2:.4f}" for value in size_m)
    if shape == "cylinder":
        if len(size_m) != 2:
            raise ValueError(f"cylinder obstacle size must be [radius, height], got {size_m}")
        return f"{size_m[0]:.4f} {size_m[1] / 2:.4f}"
    raise ValueError(f"Unsupported concrete obstacle shape: {shape}")


def _default_position(index: int, difficulty: str) -> str:
    positions = {
        "easy": [(0.00, -0.18, 0.43), (0.12, 0.18, 0.43)],
        "medium": [(0.00, -0.14, 0.44), (0.14, 0.14, 0.44)],
        "hard": [(0.05, 0.00, 0.45), (-0.10, -0.16, 0.45), (0.16, 0.16, 0.45)],
    }
    selected = positions.get(difficulty, positions["medium"])
    x, y, z = selected[index % len(selected)]
    return f"{x:.4f} {y:.4f} {z:.4f}"


def obstacle_bodies_for_scenario(scenario: dict[str, Any]) -> list[ET.Element]:
    bodies: list[ET.Element] = []
    difficulty = str(scenario.get("difficulty", "medium"))
    for index, obstacle in enumerate(scenario.get("obstacles", [])):
        shape = obstacle.get("shape")
        if shape == "virtual_safety_zone":
            continue
        name = f"avoidance_{scenario['scenario_id']}_{index}"
        body = ET.Element("body", {"name": name, "pos": _default_position(index, difficulty)})
        ET.SubElement(
            body,
            "geom",
            {
                "name": f"{name}_geom",
                "type": str(shape),
                "size": _size_to_mujoco(str(shape), list(obstacle.get("size_m", []))),
                "rgba": DEFAULT_RGBA.get(difficulty, DEFAULT_RGBA["medium"]),
                "contype": "1",
                "conaffinity": "1",
                "group": "1",
            },
        )
        bodies.append(body)
    return bodies


def inject_obstacles_into_xml(xml_text: str, scenario: dict[str, Any]) -> str:
    root = ET.fromstring(xml_text)
    worldbody = root.find("worldbody")
    if worldbody is None:
        raise ValueError("MuJoCo XML does not contain a <worldbody> element.")
    for body in obstacle_bodies_for_scenario(scenario):
        worldbody.append(body)
    return ET.tostring(root, encoding="unicode")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--curriculum", required=True)
    parser.add_argument("--scenario-id", default="")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    curriculum = json.loads(Path(args.curriculum).read_text(encoding="utf-8"))
    scenarios = curriculum.get("scenarios", [])
    if not scenarios:
        raise ValueError("Curriculum contains no scenarios.")
    if args.scenario_id:
        scenario = next((item for item in scenarios if item.get("scenario_id") == args.scenario_id), None)
        if scenario is None:
            raise ValueError(f"Unknown scenario id: {args.scenario_id}")
    else:
        scenario = scenarios[0]

    base_xml = """<mujoco model="obstacle_injector_smoke"><worldbody><body name="table" pos="0 0 0.36"><geom name="table_collision" type="box" size="0.5 0.5 0.025"/></body></worldbody></mujoco>"""
    injected = inject_obstacles_into_xml(base_xml, scenario)
    output = Path(args.output).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(injected, encoding="utf-8")
    print(f"Wrote obstacle XML smoke sample: {output}")
    print(f"Scenario: {scenario['scenario_id']}")


if __name__ == "__main__":
    main()
