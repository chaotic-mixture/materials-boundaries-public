"""Compare two source-screened rPP composites. Run with Python 3."""
import json
from pathlib import Path
from decimal import Decimal


def compare(left, right):
    fields = ("source", "matrix", "fiber", "process", "property", "unit", "statistic")
    matched, missing, conflicts = [], [], []
    for key in fields:
        if not left.get(key) or not right.get(key):
            missing.append(key)
        elif left[key] != right[key]:
            conflicts.append(key)
        else:
            matched.append(key)
    result = dict(records=[left, right], matched_fields=matched, missing_fields=missing,
                  conflicting_fields=conflicts, scope="同来源、不同填料质量分数的描述性均值比较")
    if not missing and not conflicts:
        result["difference_right_minus_left"] = str(Decimal(right["mean"]) - Decimal(left["mean"]))
    result["limits"] = ["基体批次是否相同未知", "独立配混批次数未知", "孔隙率未测量",
                        "试件筛选的排除数未知；均值差不能证明批间复现或因果效应"]
    return result


if __name__ == "__main__":
    records = json.loads(Path(__file__).with_name("records.json").read_bytes())
    print(json.dumps(compare(*records), ensure_ascii=False, indent=2))
