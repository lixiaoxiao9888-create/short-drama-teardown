import base64, json, os, subprocess, sys

REPO = "lixiaoxiao9888-create/short-drama-teardown"
ROOT = r"C:\Users\李\.openclaw\workspace\_tmp\sdt-publish"
MSG = ("feat: 扒剧引擎升级 V4.0.1（四段式交付 + 离线单页 HTML 报告 + JSON 字段契约 "
       "+ 抽帧失败报警 + BOM/视觉门禁补丁）")


def gh(args, stdin=None):
    p = subprocess.run(["gh"] + args, input=stdin, capture_output=True, text=True, encoding="utf-8")
    if p.returncode != 0:
        print("FAIL", args[:3], p.stderr[:600])
        sys.exit(1)
    return p.stdout


files = []
skip = {".git"}
for dirpath, dirnames, filenames in os.walk(ROOT):
    dirnames[:] = [d for d in dirnames if d not in skip and d != "__pycache__"]
    for fn in filenames:
        if fn.endswith(".pyc"):
            continue
        full = os.path.join(dirpath, fn)
        rel = os.path.relpath(full, ROOT).replace("\\", "/")
        if rel.startswith(".git/"):
            continue
        files.append((rel, full))
files.sort()
print("files:", len(files))

head = json.loads(gh(["api", f"repos/{REPO}/commits/main"]))
parent = head["sha"]
base_tree = head["commit"]["tree"]["sha"]

entries = []
for rel, full in files:
    with open(full, "rb") as fh:
        content = base64.b64encode(fh.read()).decode("ascii")
    blob = json.loads(gh(["api", "--method", "POST", "--input", "-", f"repos/{REPO}/git/blobs"],
                         stdin=json.dumps({"content": content, "encoding": "base64"})))
    entries.append({"path": rel, "mode": "100644", "type": "blob", "sha": blob["sha"]})
    print("  blob", rel, blob["sha"][:7])

tree = json.loads(gh(["api", "--method", "POST", "--input", "-", f"repos/{REPO}/git/trees"],
                     stdin=json.dumps({"base_tree": base_tree, "tree": entries})))
commit = json.loads(gh(["api", "--method", "POST", "--input", "-", f"repos/{REPO}/git/commits"],
                       stdin=json.dumps({"message": MSG, "tree": tree["sha"], "parents": [parent]})))
json.loads(gh(["api", "--method", "PATCH", "--input", "-", f"repos/{REPO}/git/refs/heads/main"],
              stdin=json.dumps({"sha": commit["sha"], "force": False})))
print("parent:", parent[:7], "-> commit:", commit["sha"][:7], "tree:", tree["sha"][:7])
