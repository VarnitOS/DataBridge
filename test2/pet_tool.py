import sys, json

tools = {
    "find_pet_link": {
        "description": "Find a link for a pet (dog or cat).",
        "args": ["query"]
    }
}

def main():
    for line in sys.stdin:
        req = json.loads(line)
        if req.get("type") == "list_tools":
            sys.stdout.write(json.dumps({"tools": tools}) + "\n")
            sys.stdout.flush()
        elif req.get("type") == "call_tool":
            query = req["args"]["query"]
            if "dog" in query.lower():
                link = "https://en.wikipedia.org/wiki/Dog"
            elif "cat" in query.lower():
                link = "https://en.wikipedia.org/wiki/Cat"
            else:
                link = "No link found."
            sys.stdout.write(json.dumps({"content": link}) + "\n")
            sys.stdout.flush()

if __name__ == "__main__":
    main()

