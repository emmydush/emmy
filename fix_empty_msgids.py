def fix_empty_msgids():
    with open('e:/AI/locale/rw/LC_MESSAGES/django.po', 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Find empty msgid entries that are not headers
    cleaned_lines = []
    i = 0
    
    while i < len(lines):
        line = lines[i]
        
        # Check if this is an empty msgid that's not a header
        if line.strip() == 'msgid ""' and i > 0 and not lines[i-1].strip().startswith('#'):
            # Skip this empty msgid and its corresponding empty msgstr
            print(f"Removing empty msgid at line {i+1}")
            i += 2  # Skip both the msgid "" and msgstr "" lines
            continue
        
        cleaned_lines.append(line)
        i += 1
    
    # Write the cleaned content back
    with open('e:/AI/locale/rw/LC_MESSAGES/django.po', 'w', encoding='utf-8') as f:
        f.writelines(cleaned_lines)
    
    print("Empty msgid entries removed successfully!")

if __name__ == "__main__":
    fix_empty_msgids()