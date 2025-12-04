def fix_po_duplicates():
    with open("e:/AI/locale/rw/LC_MESSAGES/django.po", "r", encoding="utf-8") as f:
        lines = f.readlines()

    # Find and remove duplicate msgid entries
    seen_msgids = set()
    cleaned_lines = []
    i = 0

    while i < len(lines):
        line = lines[i]
        cleaned_lines.append(line)

        if line.startswith("msgid"):
            # Get the full msgid (might span multiple lines)
            msgid_lines = [line]
            j = i + 1
            while j < len(lines) and lines[j].startswith('"'):
                msgid_lines.append(lines[j])
                j += 1

            msgid = "".join(msgid_lines).strip()

            if msgid in seen_msgids:
                # Skip this msgid and its corresponding msgstr
                print(f"Removing duplicate at line {i+1}: {msgid}")
                # Remove the msgid lines we just added
                for _ in msgid_lines:
                    cleaned_lines.pop()

                # Skip the msgstr lines
                k = j
                while k < len(lines) and not (
                    lines[k].startswith("msgid") or lines[k].startswith('msgstr ""')
                ):
                    k += 1
                if k < len(lines) and lines[k].startswith("msgstr"):
                    while k < len(lines) and (
                        lines[k].startswith("msgstr") or lines[k].startswith('"')
                    ):
                        k += 1

                i = k
                continue
            else:
                seen_msgids.add(msgid)
                i = j
        else:
            i += 1

    # Write the cleaned content back
    with open("e:/AI/locale/rw/LC_MESSAGES/django.po", "w", encoding="utf-8") as f:
        f.writelines(cleaned_lines)

    print("Duplicate entries removed successfully!")


if __name__ == "__main__":
    fix_po_duplicates()
