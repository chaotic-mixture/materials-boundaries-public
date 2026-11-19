"""Compare source-qualified endpoints for the two recycled-PP studies."""
import argparse
import json
from pathlib import Path
import sys

RULES = {
    "matrix": "核对树脂来源、牌号和预配方组成",
    "matrix_grade_or_stream": "核对树脂牌号、回收来源及进入复合配方前的预配方",
    "compatibilizer": "分离 MAPP 效应需要相同基体和填料的配对对照",
    "filler": "核对填料来源、形态与处理工艺",
    "filler_processing": "核对填料干燥、粒级、表面处理和商品来源",
    "filler_wt_percent": "核对填料质量分数及分母",
    "compounding_and_molding_process": "核对混炼、成型温度、压力及工艺路线",
    "endpoint": "取得相同端点的数据，或由原始曲线按相同定义重算",
    "unit": "确认量纲及换算",
    "matrix_lot": "补充可追溯的基体批次及独立制备批次数",
    "matched_test_protocol": "核对两文的试样几何、调湿、加载速率和应变测量方式",
}


def compare_pair(left, right):
    checks = {}
    for field, requirement in RULES.items():
        a, b = left.get(field), right.get(field)
        status = "缺证" if a is None or b is None else "一致" if a == b else "不同"
        checks[field] = {"left": a, "right": b, "status": status}
        if status != "一致":
            checks[field]["evidence_needed"] = requirement
    if any(checks[k]["status"] != "一致" for k in ("endpoint", "unit")):
        verdict = "端点或单位未对齐，不能直接比较数值"
    elif any(row["status"] != "一致" for row in checks.values()):
        verdict = "可并列展示来源均值；条件不足以作受控比较"
    else:
        verdict = "所列条件一致，可作描述性比较"
    return {"records": [left, right], "conditions": checks, "verdict": verdict}


if __name__ == "__main__":
    # Source labels include non-ASCII product names such as SÉETEC; keep the
    # documented CLI usable in Windows shells whose default encoding is GBK.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("case", choices=("strength", "strain"), default="strength", nargs="?")
    case = parser.parse_args().case
    records = json.loads(Path(__file__).with_name("cross-source.json").read_bytes())
    print(json.dumps(compare_pair(records["garcia-" + case], records["cunha-" + case]),
                     ensure_ascii=False, indent=2))
