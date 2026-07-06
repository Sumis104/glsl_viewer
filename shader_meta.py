import re

def parse_metadata(source):
    meta = {}
    for line in source.splitlines():   # ← リスト手書きじゃなくファイル全文から
        m = re.search(r'uniform\s+\w+\s+(\w+)', line)
        if not m:
            continue
        name = m.group(1)

        d = re.search(r'default:\s*([-\d.\s]+)', line)
        nums = []
        if d:
            nums = [float(x) for x in re.findall(r'[-\d.]+', d.group(1))]

        # ここから追加: range対応
        r = re.search(r'range:\s*([-\d.]+)\s+([-\d.]+)', line)
        range_val = None
        if r:
            range_val = (float(r.group(1)), float(r.group(2)))

        meta[name] = {"default": nums, "range": range_val}
    return meta