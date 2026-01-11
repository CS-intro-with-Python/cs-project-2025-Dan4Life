import requests


def main():
    response = requests.get("http://localhost:8080/api/status", timeout=5)
    response.raise_for_status()
    payload = response.json()
    if payload.get("ok") is not True:
        raise SystemExit("Status check failed")
    print("Status check ok")


if __name__ == "__main__":
    main()
