import getpass
import json

from packaging import version

try:
    import main
except Exception as e:
    print(f"Could not import main module: {e}")
    main = None

data = {
    "masks": {
        "msword": [
            "Microsoft Word",
            "Microsoft Office",
            "https://microsoft.com",
            "msword-64.png",
            "msword-128.png"
        ],
        "mspowerpoint": [
            "Microsoft PowerPoint",
            "Microsoft Office",
            "https://microsoft.com",
            "mspowerpoint-64.png",
            "mspowerpoint-128.png"
        ],
        "msexcel": [
            "Microsoft Excel",
            "Microsoft Office",
            "https://microsoft.com",
            "msexcel-64.png",
            "msexcel-128.png"
        ],
        "photoshop": [
            "Adobe Photoshop",
            "Adobe Creative Cloud",
            "https://adobe.com",
            "photoshop-64.png",
            "photoshop-128.png"
        ],
        "chrome": [
            "Google Chrome",
            "Google",
            "https://google.com",
            "chrome-64.png",
            "chrome-128.png"
        ],
    },
    "default": {
        "mask": "msword",
        "title": None, # Will use the Platform release, will be overridden by a mask
        "theme": "dark",
        "api": "https://api.chattingapp.repl.co/pyb",
        "connect": True,
        "adblock": True,
        "qapp_flags": [],
    },
}

def smain(path: str = "config.json"):
    if not main is None:
        aversion: str = main.app_version
    else:
        cho = input("App Version: ")
        if type(version.parse(cho)) is version.LegacyVersion:
            input("Invalid version.\nPress Enter to exit.")
            raise SystemExit
        else:
            aversion: str = cho
        
    # Contains info on how and when the json was written
    data["info"] = {"version": aversion, "creator": getpass.getuser()}
    
    print("Writting config...")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    
    print("Config written, see ./config.json for the results!")

if __name__ == "__main__":
    smain()