import urllib.request
try:
    req = urllib.request.Request("http://127.0.0.1:5000/employees/delete/1", method="POST")
    with urllib.request.urlopen(req) as response:
        print(response.status)
except urllib.error.HTTPError as e:
    print("HTTP Error:", e.code)
    print(e.read().decode())
