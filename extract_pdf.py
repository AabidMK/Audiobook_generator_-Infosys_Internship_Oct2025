import sys
from pdfminer.high_level import extract_text
p = 'AI AudioBook Generator.pdf'
try:
    text = extract_text(p)
    out = 'AI_AudioBook_Generator_extracted.txt'
    with open(out, 'w', encoding='utf-8') as f:
        f.write(text)
    print(out)
except Exception as e:
    print('ERROR:', e)
    sys.exit(1)
