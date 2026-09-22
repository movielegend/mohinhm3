import base64
from pathlib import Path

tpl = Path('ha109-viewer-template.html').read_text(encoding='utf-8')
html = Path('xem-mo-hinh-ha109.html').read_text(encoding='utf-8')

js_marker_start = '<script type="module">'
js_marker_end = '</script></head>'

js_start = html.find(js_marker_start) + len(js_marker_start)
js_end = html.find(js_marker_end, js_start)
js_code = html[js_start:js_end]

glb_data = Path('ha109-projector.glb').read_bytes()
b64_glb = base64.b64encode(glb_data).decode('ascii')

final_html = tpl.replace('MODEL_VIEWER_JS', js_code).replace('MODEL_DATA', b64_glb)

Path('xem-mo-hinh-ha109.html').write_text(final_html, encoding='utf-8')
print("Compiled xem-mo-hinh-ha109.html successfully, size:", len(final_html))
