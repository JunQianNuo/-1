"""Paper-ready final figures built directly from validation result CSV files."""

from __future__ import annotations

import csv
import math
from pathlib import Path
import re
from typing import Iterable, Sequence

import numpy as np
from PIL import Image, ImageDraw, ImageFont


FIGURE_SIZE = (2400, 1350)
BLUE = (37, 99, 167)
ORANGE = (224, 122, 31)
GREEN = (37, 142, 83)
RED = (196, 61, 61)
GRAY = (90, 90, 90)
LIGHT_GRAY = (218, 218, 218)

FONT_CANDIDATES = (
    Path(r"C:\Windows\Fonts\msyh.ttc"),
    Path(r"C:\Windows\Fonts\msyhbd.ttc"),
    Path(r"C:\Windows\Fonts\simhei.ttf"),
)


def generate_final_figure(question: str, results_dir: Path) -> Path:
    """Create one formal validation figure from raw CSV rows.

    Parameters
    ----------
    question:
        One of ``q2``, ``q3``, or ``q4``.
    results_dir:
        Directory containing the question subdirectories with raw CSV outputs.
    """

    directory = Path(results_dir)
    sensitivity = _read_csv(directory / question / "sensitivity.csv")
    monte_carlo = _read_csv(directory / question / "monte_carlo.csv")
    builders = {"q2": _draw_q2, "q3": _draw_q3, "q4": _draw_q4}
    if question not in builders:
        raise ValueError(f"unknown question: {question}")
    return builders[question](sensitivity, monte_carlo, directory / "figures")


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        raise FileNotFoundError(f"missing result file: {path}")
    with path.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        raise ValueError(f"result file is empty: {path}")
    return rows


def _require_columns(rows: list[dict[str, str]], required: Iterable[str], label: str) -> None:
    actual = set(rows[0])
    missing = sorted(set(required) - actual)
    if missing:
        raise ValueError(f"{label} missing columns: {', '.join(missing)}")


def _number(row: dict[str, str], field: str) -> float:
    try:
        value = float(row[field])
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(f"invalid numeric field {field!r}") from exc
    if not math.isfinite(value):
        raise ValueError(f"non-finite numeric field {field!r}")
    return value


def _cjk_font(size: int, *, bold: bool = False) -> ImageFont.FreeTypeFont:
    candidates = FONT_CANDIDATES[1:2] + FONT_CANDIDATES[:1] if bold else FONT_CANDIDATES
    for candidate in candidates:
        if not candidate.is_file():
            continue
        try:
            return ImageFont.truetype(str(candidate), size=size)
        except OSError:
            continue
    raise RuntimeError("未找到可用中文字体")


def _new_canvas(title: str) -> tuple[Image.Image, ImageDraw.ImageDraw, dict[str, ImageFont.FreeTypeFont]]:
    image = Image.new("RGB", FIGURE_SIZE, "white")
    draw = ImageDraw.Draw(image)
    fonts = {
        "title": _cjk_font(48, bold=True),
        "subtitle": _cjk_font(31, bold=True),
        "body": _cjk_font(25),
        "small": _cjk_font(21),
    }
    draw.text((90, 52), title, fill="black", font=fonts["title"])
    return image, draw, fonts


def _centered_text(
    draw: ImageDraw.ImageDraw,
    xy: tuple[float, float],
    text: str,
    font: ImageFont.FreeTypeFont,
    fill: tuple[int, int, int] = (0, 0, 0),
) -> None:
    box = draw.textbbox((0, 0), text, font=font)
    draw.text((int(xy[0] - (box[2] - box[0]) / 2), int(xy[1] - (box[3] - box[1]) / 2)), text, font=font, fill=fill)


def _panel(
    draw: ImageDraw.ImageDraw,
    bounds: tuple[int, int, int, int],
    title: str,
    fonts: dict[str, ImageFont.FreeTypeFont],
) -> None:
    left, top, right, bottom = bounds
    draw.rounded_rectangle(bounds, radius=18, outline=GRAY, width=2)
    draw.text((left + 24, top + 20), title, font=fonts["subtitle"], fill="black")
    draw.line((left + 90, top + 95, left + 90, bottom - 80), fill="black", width=2)
    draw.line((left + 90, bottom - 80, right - 30, bottom - 80), fill="black", width=2)


def _plot_area(bounds: tuple[int, int, int, int]) -> tuple[int, int, int, int]:
    left, top, right, bottom = bounds
    return left + 90, top + 95, right - 30, bottom - 80


def _scale(value: float, low: float, high: float, y_top: int, y_bottom: int) -> int:
    return round(y_bottom - (value - low) / (high - low) * (y_bottom - y_top))


def _draw_y_axis(
    draw: ImageDraw.ImageDraw,
    plot: tuple[int, int, int, int],
    low: float,
    high: float,
    fonts: dict[str, ImageFont.FreeTypeFont],
    *,
    reference: float | None = None,
    reference_label: str | None = None,
) -> None:
    left, top, right, bottom = plot
    for value in np.linspace(low, high, 5):
        y = _scale(float(value), low, high, top, bottom)
        draw.line((left, y, right, y), fill=LIGHT_GRAY, width=1)
        label = f"{value:.3f}" if high <= 1.1 else f"{value:.0f}"
        _centered_text(draw, (left - 43, y), label, fonts["small"], GRAY)
    if reference is not None and low <= reference <= high:
        y = _scale(reference, low, high, top, bottom)
        draw.line((left, y, right, y), fill=RED, width=3)
        if reference_label:
            draw.text((right - 180, y - 31), reference_label, font=fonts["small"], fill=RED)


def _draw_x_labels(
    draw: ImageDraw.ImageDraw,
    plot: tuple[int, int, int, int],
    labels: Sequence[str],
    fonts: dict[str, ImageFont.FreeTypeFont],
) -> list[int]:
    left, _top, right, bottom = plot
    positions = [round(left + (right - left) * index / max(1, len(labels) - 1)) for index in range(len(labels))]
    for position, label in zip(positions, labels):
        _centered_text(draw, (position, bottom + 36), label, fonts["small"], GRAY)
    return positions


def _legend(
    draw: ImageDraw.ImageDraw,
    x: int,
    y: int,
    items: Sequence[tuple[str, tuple[int, int, int]]],
    fonts: dict[str, ImageFont.FreeTypeFont],
) -> None:
    cursor = x
    for label, color in items:
        draw.line((cursor, y + 13, cursor + 34, y + 13), fill=color, width=5)
        cursor += 42
        draw.text((cursor, y), label, font=fonts["small"], fill=GRAY)
        cursor += int(draw.textlength(label, font=fonts["small"])) + 30


def _interval(values: Sequence[float]) -> tuple[float, float, float]:
    array = np.asarray(values, dtype=float)
    if array.size == 0 or not np.all(np.isfinite(array)):
        raise ValueError("interval values must be finite and nonempty")
    return float(np.mean(array)), float(np.quantile(array, 0.025)), float(np.quantile(array, 0.975))


def _candidate_order(rows: list[dict[str, str]]) -> list[str]:
    return list(dict.fromkeys(row["candidate"] for row in rows))


def _draw_q2(
    sensitivity: list[dict[str, str]],
    monte_carlo: list[dict[str, str]],
    figures_dir: Path,
) -> Path:
    _require_columns(sensitivity, {"candidate", "scenario", "C1", "C2"}, "q2 sensitivity.csv")
    _require_columns(monte_carlo, {"candidate", "replicate", "C1", "C2"}, "q2 monte_carlo.csv")
    image, draw, fonts = _new_canvas("问题二：覆盖模型敏感性与蒙特卡洛检验")
    left_panel = (90, 150, 1210, 1130)
    right_panel = (1280, 150, 2310, 1130)
    _panel(draw, left_panel, "(a) 覆盖率对物理参数扰动的响应", fonts)
    _panel(draw, right_panel, "(b) 空间—时间抽样的 95% 区间", fonts)

    scenarios = list(dict.fromkeys(row["scenario"] for row in sensitivity))
    candidates = _candidate_order(sensitivity)
    plot = _plot_area(left_panel)
    _draw_y_axis(draw, plot, 0.0, 1.0, fonts)
    positions = _draw_x_labels(draw, plot, [_scenario_label(value) for value in scenarios], fonts)
    colors = (BLUE, ORANGE, GREEN, RED)
    legend_items: list[tuple[str, tuple[int, int, int]]] = []
    for candidate_index, candidate in enumerate(candidates):
        candidate_rows = {row["scenario"]: row for row in sensitivity if row["candidate"] == candidate}
        for metric_index, metric in enumerate(("C1", "C2")):
            points = []
            color = colors[candidate_index * 2 + metric_index]
            for position, scenario in zip(positions, scenarios):
                row = candidate_rows.get(scenario)
                if row is None:
                    raise ValueError(f"q2 sensitivity.csv missing {candidate}/{scenario}")
                points.append((position, _scale(_number(row, metric), 0.0, 1.0, plot[1], plot[3])))
            draw.line(points, fill=color, width=4)
            for x, y in points:
                draw.ellipse((x - 5, y - 5, x + 5, y + 5), fill=color)
            legend_items.append((f"{candidate} {metric}", color))
    _legend(draw, left_panel[0] + 115, left_panel[1] + 64, legend_items, fonts)

    interval_plot = _plot_area(right_panel)
    _draw_y_axis(draw, interval_plot, 0.0, 1.0, fonts)
    categories = [(candidate, metric) for candidate in candidates for metric in ("C1", "C2")]
    interval_positions = _draw_x_labels(
        draw,
        interval_plot,
        [f"{candidate}\n{metric}" for candidate, metric in categories],
        fonts,
    )
    for index, ((candidate, metric), x) in enumerate(zip(categories, interval_positions)):
        values = [_number(row, metric) for row in monte_carlo if row["candidate"] == candidate]
        mean, lower, upper = _interval(values)
        y_low = _scale(lower, 0.0, 1.0, interval_plot[1], interval_plot[3])
        y_high = _scale(upper, 0.0, 1.0, interval_plot[1], interval_plot[3])
        y_mean = _scale(mean, 0.0, 1.0, interval_plot[1], interval_plot[3])
        color = colors[index]
        draw.line((x, y_low, x, y_high), fill=color, width=5)
        draw.line((x - 12, y_low, x + 12, y_low), fill=color, width=4)
        draw.line((x - 12, y_high, x + 12, y_high), fill=color, width=4)
        draw.ellipse((x - 8, y_mean - 8, x + 8, y_mean + 8), fill=color)

    draw.text((110, 1190), "注：随机抽样反映离散覆盖率估计稳定性，不能替代连续区域严格覆盖证明。", font=fonts["body"], fill=GRAY)
    return _save(image, figures_dir / "fig_q2_validation.png")


def _draw_q3(
    sensitivity: list[dict[str, str]],
    monte_carlo: list[dict[str, str]],
    figures_dir: Path,
) -> Path:
    _require_columns(sensitivity, {"candidate", "scenario", "p30_all"}, "q3 sensitivity.csv")
    _require_columns(monte_carlo, {"candidate", "replicate", "p30_all_bootstrap"}, "q3 monte_carlo.csv")
    image, draw, fonts = _new_canvas("问题三：通信饱和模型敏感性与 Bootstrap 检验")
    left_panel = (90, 150, 1210, 1130)
    right_panel = (1280, 150, 2310, 1130)
    _panel(draw, left_panel, "(a) P30(all) 对通信物理参数的响应", fonts)
    _panel(draw, right_panel, "(b) 时间块 Bootstrap 的 95% 区间", fonts)

    scenarios = list(dict.fromkeys(row["scenario"] for row in sensitivity))
    candidates = _candidate_order(sensitivity)
    plot = _plot_area(left_panel)
    p_values = [_number(row, "p30_all") for row in sensitivity]
    lower = max(0.0, min(p_values) - 0.08)
    _draw_y_axis(draw, plot, lower, 1.0, fonts, reference=0.95, reference_label="0.95")
    positions = _draw_x_labels(draw, plot, [_scenario_label(value) for value in scenarios], fonts)
    colors = (BLUE, ORANGE, GREEN)
    for index, candidate in enumerate(candidates):
        records = {row["scenario"]: row for row in sensitivity if row["candidate"] == candidate}
        points = []
        for x, scenario in zip(positions, scenarios):
            row = records.get(scenario)
            if row is None:
                raise ValueError(f"q3 sensitivity.csv missing {candidate}/{scenario}")
            points.append((x, _scale(_number(row, "p30_all"), lower, 1.0, plot[1], plot[3])))
        draw.line(points, fill=colors[index % len(colors)], width=4)
        for x, y in points:
            draw.ellipse((x - 5, y - 5, x + 5, y + 5), fill=colors[index % len(colors)])
    _legend(draw, left_panel[0] + 115, left_panel[1] + 64, [(_candidate_label(candidate), colors[index % len(colors)]) for index, candidate in enumerate(candidates)], fonts)

    interval_plot = _plot_area(right_panel)
    bootstrap_values = [_number(row, "p30_all_bootstrap") for row in monte_carlo]
    interval_lower = max(0.0, min(bootstrap_values) - 0.08)
    _draw_y_axis(draw, interval_plot, interval_lower, 1.0, fonts, reference=0.95, reference_label="0.95")
    x_positions = _draw_x_labels(draw, interval_plot, [_candidate_label(candidate) for candidate in candidates], fonts)
    for index, (candidate, x) in enumerate(zip(candidates, x_positions)):
        values = [_number(row, "p30_all_bootstrap") for row in monte_carlo if row["candidate"] == candidate]
        mean, low, high = _interval(values)
        color = colors[index % len(colors)]
        y_low = _scale(low, interval_lower, 1.0, interval_plot[1], interval_plot[3])
        y_high = _scale(high, interval_lower, 1.0, interval_plot[1], interval_plot[3])
        y_mean = _scale(mean, interval_lower, 1.0, interval_plot[1], interval_plot[3])
        draw.line((x, y_low, x, y_high), fill=color, width=6)
        draw.line((x - 13, y_low, x + 13, y_low), fill=color, width=4)
        draw.line((x - 13, y_high, x + 13, y_high), fill=color, width=4)
        draw.ellipse((x - 9, y_mean - 9, x + 9, y_mean + 9), fill=color)

    draw.text((110, 1190), "注：独立标准格（2°覆盖、15°通信、300 s快照）；区间反映模型时间快照重抽样波动。", font=fonts["body"], fill=GRAY)
    return _save(image, figures_dir / "fig_q3_validation.png")


def _draw_q4(
    sensitivity: list[dict[str, str]],
    monte_carlo: list[dict[str, str]],
    figures_dir: Path,
) -> Path:
    _require_columns(sensitivity, {"candidate", "scenario", "annual_avoidances"}, "q4 sensitivity.csv")
    _require_columns(monte_carlo, {"candidate", "replicate", "conjunctions", "avoidances"}, "q4 monte_carlo.csv")
    image, draw, fonts = _new_canvas("问题四：碎片—避撞情景敏感性与年度事件检验")
    left_panel = (90, 150, 1210, 1130)
    right_panel = (1280, 150, 2310, 1130)
    _panel(draw, left_panel, "(a) 年度规避次数对情景参数的响应", fonts)
    _panel(draw, right_panel, "(b) 年度交会与规避次数的 95% 区间", fonts)

    scenarios = list(dict.fromkeys(row["scenario"] for row in sensitivity))
    candidates = _candidate_order(sensitivity)
    plot = _plot_area(left_panel)
    avoidance_values = [_number(row, "annual_avoidances") for row in sensitivity]
    upper = max(1.0, max(avoidance_values) * 1.12)
    _draw_y_axis(draw, plot, 0.0, upper, fonts)
    positions = _draw_x_labels(draw, plot, [_scenario_label(value) for value in scenarios], fonts)
    colors = (BLUE, ORANGE, GREEN)
    for index, candidate in enumerate(candidates):
        records = {row["scenario"]: row for row in sensitivity if row["candidate"] == candidate}
        points = []
        for x, scenario in zip(positions, scenarios):
            row = records.get(scenario)
            if row is None:
                raise ValueError(f"q4 sensitivity.csv missing {candidate}/{scenario}")
            points.append((x, _scale(_number(row, "annual_avoidances"), 0.0, upper, plot[1], plot[3])))
        color = colors[index % len(colors)]
        draw.line(points, fill=color, width=4)
        for x, y in points:
            draw.ellipse((x - 5, y - 5, x + 5, y + 5), fill=color)
    _legend(draw, left_panel[0] + 115, left_panel[1] + 64, [(_candidate_label(candidate), colors[index % len(colors)]) for index, candidate in enumerate(candidates)], fonts)

    interval_plot = _plot_area(right_panel)
    measures = ("conjunctions", "avoidances")
    transformed = [math.log10(max(_number(row, measure), 0.1)) for row in monte_carlo for measure in measures]
    low_exp = math.floor(min(transformed))
    high_exp = math.ceil(max(transformed))
    if low_exp == high_exp:
        high_exp += 1
    _draw_log_y_axis(draw, interval_plot, low_exp, high_exp, fonts)
    categories = [(candidate, measure) for candidate in candidates for measure in measures]
    x_positions = _draw_x_labels(
        draw,
        interval_plot,
        [f"{_candidate_label(candidate)}\n{'交会' if measure == 'conjunctions' else '规避'}" for candidate, measure in categories],
        fonts,
    )
    measure_colors = {"conjunctions": BLUE, "avoidances": ORANGE}
    for (candidate, measure), x in zip(categories, x_positions):
        values = [_number(row, measure) for row in monte_carlo if row["candidate"] == candidate]
        mean, low, high = _interval(values)
        color = measure_colors[measure]
        y_low = _scale(math.log10(max(low, 0.1)), low_exp, high_exp, interval_plot[1], interval_plot[3])
        y_high = _scale(math.log10(max(high, 0.1)), low_exp, high_exp, interval_plot[1], interval_plot[3])
        y_mean = _scale(math.log10(max(mean, 0.1)), low_exp, high_exp, interval_plot[1], interval_plot[3])
        draw.line((x, y_low, x, y_high), fill=color, width=6)
        draw.line((x - 12, y_low, x + 12, y_low), fill=color, width=4)
        draw.line((x - 12, y_high, x + 12, y_high), fill=color, width=4)
        draw.ellipse((x - 9, y_mean - 9, x + 9, y_mean + 9), fill=color)
    _legend(draw, right_panel[0] + 115, right_panel[1] + 64, [("年度交会数", BLUE), ("年度规避次数", ORANGE)], fonts)

    draw.text((110, 1190), "注：结果是给定碎片与避撞参数下的模型情景分析，不是实测轨道风险预测。", font=fonts["body"], fill=GRAY)
    return _save(image, figures_dir / "fig_q4_validation.png")


def _scenario_label(value: str) -> str:
    labels = {
        "baseline": "基准",
        "altitude_525km": "高度525",
        "altitude_575km": "高度575",
        "radius_480km": "半径480",
        "radius_530km": "半径530",
        "processing_0ms": "处理0ms",
        "processing_1ms": "处理1ms",
        "isl_4500km": "ISL 4500",
        "isl_5500km": "ISL 5500",
        "density_x0.5": "密度×0.5",
        "density_x2": "密度×2",
        "speed_8kms": "速度8",
        "speed_12kms": "速度12",
        "threshold_1e-6": "阈值1e-6",
        "threshold_1e-4": "阈值1e-4",
        "capacity_reduction_0.25": "容损0.25",
        "capacity_reduction_0.75": "容损0.75",
    }
    return labels.get(value, value.replace("_", " "))


def _candidate_label(value: str) -> str:
    """Return a compact, unambiguous constellation-size label."""

    match = re.search(r"S(\d+)", value)
    return f"S{match.group(1)}" if match else value


def _save(image: Image.Image, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path, format="PNG", dpi=(300, 300))
    return path


def _draw_log_y_axis(
    draw: ImageDraw.ImageDraw,
    plot: tuple[int, int, int, int],
    low_exp: int,
    high_exp: int,
    fonts: dict[str, ImageFont.FreeTypeFont],
) -> None:
    left, top, right, bottom = plot
    for exponent in range(low_exp, high_exp + 1):
        y = _scale(float(exponent), float(low_exp), float(high_exp), top, bottom)
        draw.line((left, y, right, y), fill=LIGHT_GRAY, width=1)
        _centered_text(draw, (left - 46, y), f"10^{exponent}", fonts["small"], GRAY)
