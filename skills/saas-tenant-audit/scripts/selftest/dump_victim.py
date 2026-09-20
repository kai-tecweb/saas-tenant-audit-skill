"""Prints a stable dump of the victim's (tenant B) item, as tenant B. Used as snapshot_cmd."""
import sys
import urllib.request

req = urllib.request.Request(f"http://127.0.0.1:{sys.argv[1]}/things/202", headers={"Authorization": "Token tokB"})
print(urllib.request.urlopen(req).read().decode())
