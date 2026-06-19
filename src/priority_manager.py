PROCESS_PRIORITY = {

    # Critical Processes
    "System": "CRITICAL",
    "svchost.exe": "CRITICAL",
    "mysqld.exe": "CRITICAL",

    # High Priority
    "python.exe": "HIGH",

    # Medium Priority
    "Code.exe": "MEDIUM",

    # Low Priority
    "chrome.exe": "LOW",
    "spotify.exe": "LOW",
    "notepad.exe": "LOW"
}


def get_priority(process_name: str) -> str:

    return PROCESS_PRIORITY.get(
        process_name,
        "LOW"
    )