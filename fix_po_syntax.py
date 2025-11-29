def fix_po_syntax():
    with open('e:/AI/locale/rw/LC_MESSAGES/django.po', 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    cleaned_lines = []
    i = 0
    
    while i < len(lines):
        line = lines[i]
        
        # Check for standalone msgid_plural
        if line.strip().startswith('msgid_plural ""') and i > 0:
            # Check if the previous line is not a msgid
            prev_line = lines[i-1].strip()
            if not (prev_line.startswith('msgid') or prev_line.startswith('#:') or prev_line.startswith('#,')):
                print(f"Removing standalone msgid_plural at line {i+1}")
                i += 1
                continue
        
        # Check for missing msgstr
        if line.strip().startswith('msgid') and not line.strip() == 'msgid ""':
            # Get the complete msgid
            msgid_lines = [line]
            j = i + 1
            while j < len(lines) and (lines[j].strip().startswith('"') or lines[j].strip() == ''):
                msgid_lines.append(lines[j])
                j += 1
            
            # Check if there's a msgstr after the msgid
            has_msgstr = False
            k = j
            while k < len(lines) and lines[k].strip() == '':
                k += 1
            
            if k < len(lines) and lines[k].strip().startswith('msgstr'):
                has_msgstr = True
            elif k < len(lines) and lines[k].strip().startswith('msgid'):
                # This is a missing msgstr case
                has_msgstr = False
            
            if not has_msgstr and not line.strip() == 'msgid ""':
                print(f"Adding missing msgstr for msgid at line {i+1}")
                cleaned_lines.extend(msgid_lines)
                cleaned_lines.append('msgstr ""\n')
                i = j
                continue
        
        cleaned_lines.append(line)
        i += 1
    
    # Write the cleaned content back
    with open('e:/AI/locale/rw/LC_MESSAGES/django.po', 'w', encoding='utf-8') as f:
        f.writelines(cleaned_lines)
    
    print("PO file syntax errors fixed successfully!")

if __name__ == "__main__":
    fix_po_syntax()