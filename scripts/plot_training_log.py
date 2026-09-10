from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path


FIELD_RE = re.compile(r"(?<![A-Za-z_])(?P<name>loss|grdn|lr|mem_gb):(?P<value>[-+0-9.eE]+)")
LOG_ANCHOR_RE = re.compile(r"ot_train\.py:769\s+")
PROGRESS_RE = re.compile(r"(?P<step>\d+)/(?P<total>\d+)")
NEXT_RECORD_RE = re.compile(r"(?=Training:|INFO \d{4}-\d{2}-\d{2}|\Z)")


def parse_step(value: str) -> int:
    if value.endswith("K"):
        return int(float(value[:-1]) * 1000)
    return int(value)


def unwrap_record(value: str) -> str:
    """Repair PowerShell/tqdm wrapping that splits fields across lines."""
    value = value.replace("\r", "")
    value = re.sub(r"\s*\n\s*", "", value)
    return value


def parse_records(text: str) -> list[dict]:
    rows = []
    for match in LOG_ANCHOR_RE.finditer(text):
        progress_matches = list(PROGRESS_RE.finditer(text[max(0, match.start() - 2000) : match.start()]))
        if not progress_matches:
            continue
        step = int(progress_matches[-1].group("step"))
        next_match = NEXT_RECORD_RE.search(text, match.end())
        record_end = next_match.start() if next_match else len(text)
        body = unwrap_record(text[match.end() : record_end])
        fields = {field.group("name"): field.group("value") for field in FIELD_RE.finditer(body)}
        if not {"loss", "grdn", "lr", "mem_gb"}.issubset(fields):
            continue
        rows.append(
            {
                "step": step,
                "loss": float(fields["loss"]),
                "grad_norm": float(fields["grdn"]),
                "lr": float(fields["lr"]),
                "mem_gb": float(fields["mem_gb"]),
            }
        )
    return rows


def read_log(path: Path) -> str:
    raw = path.read_bytes()
    if raw.startswith((b"\xff\xfe", b"\xfe\xff")):
        return raw.decode("utf-16", errors="ignore")
    if raw[:256:2].count(0) > 20 or raw[1:256:2].count(0) > 20:
        return raw.decode("utf-16", errors="ignore")
    return raw.decode("utf-8", errors="ignore")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--log", default="artifacts/train_pi05_task10_utf8.log")
    parser.add_argument("--out-csv", default="artifacts/train_pi05_task10_loss.csv")
    parser.add_argument("--out-png", default="artifacts/train_pi05_task10_loss.png")
    args = parser.parse_args()

    log_path = Path(args.log)
    rows = parse_records(read_log(log_path))

    out_csv = Path(args.out_csv)
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    with out_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["step", "loss", "grad_norm", "lr", "mem_gb"])
        writer.writeheader()
        writer.writerows(rows)

    try:
        import matplotlib.pyplot as plt

        steps = [row["step"] for row in rows]
        losses = [row["loss"] for row in rows]
        plt.figure(figsize=(9, 5))
        plt.plot(steps, losses, marker="o", linewidth=1.6)
        plt.xlabel("step")
        plt.ylabel("training loss")
        plt.title("Pi 0.5 LIBERO task10 training loss")
        plt.grid(True, alpha=0.25)
        plt.tight_layout()
        plt.savefig(args.out_png, dpi=160)
        print(f"Wrote plot: {args.out_png}")
    except Exception as exc:  # noqa: BLE001
        try:
            from PIL import Image, ImageDraw

            steps = [row["step"] for row in rows]
            losses = [row["loss"] for row in rows]
            width, height = 1440, 800
            margin_left, margin_right, margin_top, margin_bottom = 90, 40, 60, 90
            plot_width = width - margin_left - margin_right
            plot_height = height - margin_top - margin_bottom
            image = Image.new("RGB", (width, height), "white")
            draw = ImageDraw.Draw(image)
            draw.rectangle(
                (margin_left, margin_top, margin_left + plot_width, margin_top + plot_height),
                outline=(80, 80, 80),
            )
            if rows:
                x_min, x_max = min(steps), max(steps)
                y_min, y_max = min(losses), max(losses)
                y_pad = max((y_max - y_min) * 0.08, 0.01)
                y_min -= y_pad
                y_max += y_pad

                def point(step: int, loss: float) -> tuple[int, int]:
                    x = margin_left + int((step - x_min) / max(1, x_max - x_min) * plot_width)
                    y = margin_top + plot_height - int((loss - y_min) / max(1e-12, y_max - y_min) * plot_height)
                    return x, y

                points = [point(step, loss) for step, loss in zip(steps, losses, strict=True)]
                draw.line(points, fill=(35, 95, 180), width=3)
                for point_x, point_y in points:
                    draw.ellipse((point_x - 3, point_y - 3, point_x + 3, point_y + 3), fill=(35, 95, 180))
                for tick in range(6):
                    y = margin_top + int(tick / 5 * plot_height)
                    value = y_max - tick / 5 * (y_max - y_min)
                    draw.line((margin_left - 5, y, margin_left + plot_width, y), fill=(225, 225, 225))
                    draw.text((10, y - 8), f"{value:.3f}", fill=(50, 50, 50))
                for tick in range(7):
                    x = margin_left + int(tick / 6 * plot_width)
                    value = x_min + tick / 6 * (x_max - x_min)
                    draw.line((x, margin_top, x, margin_top + plot_height + 5), fill=(235, 235, 235))
                    draw.text((x - 28, margin_top + plot_height + 18), f"{int(value)}", fill=(50, 50, 50))
            draw.text((margin_left, 22), "Pi 0.5 LIBERO task10 training loss", fill=(20, 20, 20))
            draw.text((margin_left + plot_width // 2 - 20, height - 35), "step", fill=(20, 20, 20))
            draw.text((20, margin_top + plot_height // 2), "loss", fill=(20, 20, 20))
            image.save(args.out_png)
            print(f"Wrote plot with PIL fallback: {args.out_png}")
        except Exception as fallback_exc:  # noqa: BLE001
            print(f"Skipped plot: {exc}; PIL fallback failed: {fallback_exc}")

    print(f"Wrote csv: {out_csv}")
    if rows:
        print(f"points={len(rows)} first={rows[0]} last={rows[-1]}")
    else:
        print("points=0")


if __name__ == "__main__":
    main()
