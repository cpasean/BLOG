"""Write data/comments.json: comment count per post from GitHub Discussions (giscus, mapping=pathname).
Runs in the deploy workflow with GITHUB_TOKEN. Safe to fail: the site then shows 0 comments."""
import json, os, re, sys, urllib.request
from pathlib import Path

token = os.environ.get("GITHUB_TOKEN")
repo = os.environ.get("GITHUB_REPOSITORY", "cpasean/BLOG")
out = Path(__file__).resolve().parent.parent / "data" / "comments.json"
out.parent.mkdir(exist_ok=True)
counts = {}
if token:
    owner, name = repo.split("/")
    q = """query($o:String!,$n:String!,$c:String){repository(owner:$o,name:$n){discussions(first:100,after:$c){
      pageInfo{hasNextPage endCursor} nodes{title comments{totalCount} } }}}"""
    cursor = None
    try:
        while True:
            body = json.dumps({"query": q, "variables": {"o": owner, "n": name, "c": cursor}}).encode()
            req = urllib.request.Request("https://api.github.com/graphql", data=body,
                                         headers={"Authorization": f"bearer {token}", "Content-Type": "application/json"})
            d = json.load(urllib.request.urlopen(req, timeout=20))["data"]["repository"]["discussions"]
            for n in d["nodes"]:
                m = re.search(r"post/([^/]+)/?$", n["title"].strip())
                if m:
                    counts[m.group(1)] = counts.get(m.group(1), 0) + n["comments"]["totalCount"]
            if not d["pageInfo"]["hasNextPage"]:
                break
            cursor = d["pageInfo"]["endCursor"]
    except Exception as e:  # discussions disabled or no access yet
        print("comment counts skipped:", e, file=sys.stderr)
out.write_text(json.dumps(counts, indent=0, sort_keys=True), encoding="utf-8")
print(f"comment counts for {len(counts)} posts")
