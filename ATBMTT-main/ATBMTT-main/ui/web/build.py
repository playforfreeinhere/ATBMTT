"""Bundle the offline web interface into one portable HTML file."""
from pathlib import Path

root = Path(__file__).resolve().parent
html = (root / 'index.html').read_text()
html = html.replace('<link rel="stylesheet" href="styles.css">',
                    '<style>' + (root / 'styles.css').read_text() + '</style>')
html = html.replace('<script src="core.js"></script>',
                    '<script>' + (root / 'core.js').read_text() + '</script>')
html = html.replace('<script src="app.js"></script>',
                    '<script>' + (root / 'app.js').read_text() + '</script>')
output = root.parents[1] / 'giao_dien.html'
output.write_text(html, encoding='utf-8')
print(output)
