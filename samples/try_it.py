import json
import urllib.request

xml = open("samples/surefire-report.xml", encoding="utf-8").read()
body = json.dumps({"report_xml": xml, "max_failures": 10}).encode("utf-8")
req = urllib.request.Request(
    "http://127.0.0.1:8000/summarize",
    data=body,
    headers={"Content-Type": "application/json"},
)
print(json.dumps(json.load(urllib.request.urlopen(req)), indent=2))