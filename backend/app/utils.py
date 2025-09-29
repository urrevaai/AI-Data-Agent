import re

def sanitize_name(name: str) -> str:
    """
    Sanitizes a string to be a valid SQL table or column name.
    """
    name = re.sub(r'[^a-zA-Z0-9_]', '_', str(name))
    name = name.lower()

    if name and name[0].isdigit():
        name = '_' + name

    name = name.strip('_')

    if not name:
        return "unnamed_column"

    return name