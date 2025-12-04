def fix_po_file():
    with open("e:/AI/locale/rw/LC_MESSAGES/django.po", "r", encoding="utf-8") as f:
        lines = f.readlines()

    # Fix the header to include charset properly
    if lines[0].startswith("# Kinyarwanda translations"):
        # Update the Content-Type line to ensure charset is properly specified
        for i in range(len(lines)):
            if lines[i].startswith('"Content-Type:'):
                lines[i] = '"Content-Type: text/plain; charset=UTF-8\\n"\n'
                break

    # Remove duplicate entries
    seen_msgids = {}
    cleaned_lines = []
    i = 0

    while i < len(lines):
        line = lines[i]

        # Check for msgid lines
        if line.startswith("msgid"):
            # Get the complete msgid (might span multiple lines)
            msgid_lines = [line]
            j = i + 1
            while j < len(lines) and lines[j].startswith('"'):
                msgid_lines.append(lines[j])
                j += 1

            msgid = "".join(msgid_lines).strip()

            # Skip empty msgids that are not headers
            if (
                msgid == 'msgid ""'
                and i > 0
                and not lines[i - 1].strip().startswith("#")
            ):
                print(f"Skipping empty msgid at line {i+1}")
                i = j
                continue

            # Check if we've seen this msgid before
            if msgid in seen_msgids:
                print(f"Removing duplicate msgid at line {i+1}: {msgid}")
                # Skip this msgid and its corresponding msgstr
                k = j
                # Skip until we find the next msgid or reach end
                while k < len(lines) and not lines[k].startswith("msgid"):
                    k += 1
                i = k
                continue
            else:
                seen_msgids[msgid] = i
                # Add all the msgid lines
                cleaned_lines.extend(msgid_lines)
                i = j
        else:
            cleaned_lines.append(line)
            i += 1

    # Write the cleaned content back
    with open("e:/AI/locale/rw/LC_MESSAGES/django.po", "w", encoding="utf-8") as f:
        f.writelines(cleaned_lines)

    print("PO file cleaned successfully!")


if __name__ == "__main__":
    fix_po_file()
