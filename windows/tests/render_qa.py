"""Optional read-only PDF-to-PNG visual QA (pypdfium2 installed separately)."""
from pathlib import Path
import json
import sys

from real_build import png

root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(root / '.runtime/render'))
import pypdfium2 as pdfium

qa = root / '.runtime/qa'
result = json.loads((qa / 'results.json').read_text(encoding='utf-8'))
output = root / 'windows/build/qa-images'
output.mkdir(parents=True, exist_ok=True)
for name, file in [('template', root / 'template.pdf'), ('korean', result['report']['pdf']), ('bundle', result['current_draft']['pdf'])]:
    document = pdfium.PdfDocument(file)
    for index in range(len(document)):
        page = document[index]
        bitmap = page.render(scale=1.5, force_bitmap_format=pdfium.raw.FPDFBitmap_BGR, rev_byteorder=True)
        assert bitmap.n_channels == 3
        data = bytes(bitmap.buffer)
        pixels = b''.join(data[y * bitmap.stride:y * bitmap.stride + bitmap.width * 3] for y in range(bitmap.height))
        target = output / f'{name}-{index + 1}.png'
        target.write_bytes(png(bitmap.width, bitmap.height, pixels))
        print(target)
        bitmap.close()
        page.close()
    document.close()
