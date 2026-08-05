with open("scripts/probe_ayla.py", "r") as f:
    lines = f.readlines()

with open("scripts/probe_ayla.py", "w") as f:
    for line in lines:
        if 're.sub(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", "***REDACTED_EMAIL***", data)' in line:
            f.write('            data = re.sub(\n')
            f.write('                r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+",\n')
            f.write('                "***REDACTED_EMAIL***",\n')
            f.write('                data,\n')
            f.write('            )\n')
        elif 'data = re.sub(r"\\b([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})\\b", "***REDACTED_MAC***", data)' in line:
            f.write('        data = re.sub(\n')
            f.write('            r"\\b([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})\\b",\n')
            f.write('            "***REDACTED_MAC***",\n')
            f.write('            data,\n')
            f.write('        )\n')
        elif 'parser.add_argument("--list-properties", action="store_true", help="Print property values in terminal")' in line:
            f.write('    parser.add_argument(\n')
            f.write('        "--list-properties",\n')
            f.write('        action="store_true",\n')
            f.write('        help="Print property values in terminal",\n')
            f.write('    )\n')
        elif 'parser.add_argument("--write-fixture", metavar="PATH", help="Write sanitized JSON to this path")' in line:
            f.write('    parser.add_argument(\n')
            f.write('        "--write-fixture",\n')
            f.write('        metavar="PATH",\n')
            f.write('        help="Write sanitized JSON to this path",\n')
            f.write('    )\n')
        elif 'parser.add_argument("--force", action="store_true", help="Overwrite fixture if it exists")' in line:
            f.write('    parser.add_argument(\n')
            f.write('        "--force",\n')
            f.write('        action="store_true",\n')
            f.write('        help="Overwrite fixture if it exists",\n')
            f.write('    )\n')
        elif '_LOGGER.error("ECOWATER_USERNAME and ECOWATER_PASSWORD environment variables are required.")' in line:
            f.write('        _LOGGER.error(\n')
            f.write('            "ECOWATER_USERNAME and ECOWATER_PASSWORD environment variables are required."\n')
            f.write('        )\n')
        elif '_LOGGER.error(f"Fixture path {path} exists! Use --force to overwrite.")' in line:
            f.write('                    _LOGGER.error(\n')
            f.write('                        f"Fixture path {path} exists! Use --force to overwrite."\n')
            f.write('                    )\n')
        elif '_LOGGER.warning("Writing sanitized fixture. PLEASE REVIEW IT MANUALLY BEFORE COMMITTING.")' in line:
            f.write('                    _LOGGER.warning(\n')
            f.write('                        "Writing sanitized fixture. PLEASE REVIEW IT MANUALLY BEFORE COMMITTING."\n')
            f.write('                    )\n')
        else:
            f.write(line)
