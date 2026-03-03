"""
Zen AM Thumbnail Server
=======================
Flask webhook server for Railway deployment.
n8n sends line1 + line2 → server generates PNG → returns base64 image.

Endpoint: POST /generate
Body: { "line1": "IT'S RELEASE", "line2": "SEASON" }
Returns: { "success": true, "image_base64": "...", "filename": "zen_am_thumb.png" }
"""

from flask import Flask, request, jsonify
from PIL import Image, ImageDraw, ImageFont
import base64
import io
import os

app = Flask(__name__)

# ── COLORS ───────────────────────────────────────────────────────────────────
GOLD  = (242, 201, 76)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

# ── LAYOUT ───────────────────────────────────────────────────────────────────
ZONE_CX  = 650
ZONE_Y   = 219
ZONE_BOT = 541
MAX_W    = 742
SP1_RATIO = -0.084
SP2_RATIO = -0.055

# ── PATHS ────────────────────────────────────────────────────────────────────
DIR      = os.path.dirname(os.path.abspath(__file__))
TEMPLATE = os.path.join(DIR, 'zen_am_template.png')
FONT     = os.path.join(DIR, 'Antonio-Bold.ttf')


# ── THUMBNAIL LOGIC ──────────────────────────────────────────────────────────

def char_w(ch, font):
    bb = font.getbbox(ch)
    return bb[2] - bb[0]

def text_w(text, font, spacing):
    if not text:
        return 0
    return sum(char_w(c, font) for c in text) + spacing * (len(text) - 1)

def actual_height(text, font):
    bb = font.getbbox(text)
    return bb[3] - bb[1]

def find_size(text, target_w, max_h, sp_ratio):
    lo, hi = 20, 400
    best = 20
    while lo <= hi:
        mid = (lo + hi) // 2
        f = ImageFont.truetype(FONT, mid)
        sp = int(mid * sp_ratio)
        tw = text_w(text, f, sp)
        bb = f.getbbox('A')
        h = bb[3] - bb[1]
        if tw <= target_w and h <= max_h:
            best = mid
            lo = mid + 1
        else:
            hi = mid - 1
    return best

def draw_line_centered(draw, text, font, spacing, color, cx, y):
    tw = text_w(text, font, spacing)
    x = cx - tw // 2
    for ch in text:
        for dx, dy in [(-3,0),(3,0),(0,-3),(0,3),(-2,-2),(2,-2),(-2,2),(2,2)]:
            draw.text((x+dx, y+dy), ch, font=font, fill=BLACK)
        draw.text((x, y), ch, font=font, fill=color)
        x += char_w(ch, font) + spacing

def generate_thumbnail(line1, line2):
    img = Image.open(TEMPLATE).convert('RGB')
    draw = ImageDraw.Draw(img)

    line1 = line1.upper().strip()
    line2 = line2.upper().strip()

    total_zone_h = ZONE_BOT - ZONE_Y
    line2_max_h  = int(total_zone_h * 0.55)
    line1_max_h  = int(total_zone_h * 0.45)

    # Line 2 is larger — anchors the width
    sz2   = find_size(line2, MAX_W, line2_max_h, SP2_RATIO)
    font2 = ImageFont.truetype(FONT, sz2)
    sp2   = int(sz2 * SP2_RATIO)
    w2    = text_w(line2, font2, sp2)
    h2    = actual_height(line2, font2)

    # Line 1 matches line 2 width
    sz1   = find_size(line1, w2, line1_max_h, SP1_RATIO)
    font1 = ImageFont.truetype(FONT, sz1)
    sp1   = int(sz1 * SP1_RATIO)
    h1    = actual_height(line1, font1)

    # Center block vertically, lines touching
    total_actual_h = h1 + h2
    block_y = ZONE_Y + (total_zone_h - total_actual_h) // 2
    line1_y = block_y
    line2_y = block_y + h1

    draw_line_centered(draw, line1, font1, sp1, GOLD,  ZONE_CX, line1_y)
    draw_line_centered(draw, line2, font2, sp2, WHITE, ZONE_CX, line2_y)

    # Return as bytes
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    return buf.read()


# ── ROUTES ───────────────────────────────────────────────────────────────────

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok', 'service': 'Zen AM Thumbnail Generator'})

@app.route('/generate', methods=['POST'])
def generate():
    try:
        data = request.get_json()

        if not data:
            return jsonify({'success': False, 'error': 'No JSON body received'}), 400

        line1 = data.get('line1', '').strip()
        line2 = data.get('line2', '').strip()

        if not line1 or not line2:
            return jsonify({'success': False, 'error': 'line1 and line2 are required'}), 400

        # Generate thumbnail
        png_bytes = generate_thumbnail(line1, line2)

        # Return as base64 so n8n can receive it easily
        encoded = base64.b64encode(png_bytes).decode('utf-8')

        return jsonify({
            'success': True,
            'image_base64': encoded,
            'filename': f'zen_am_thumb_{line1[:20].replace(" ", "_")}.png',
            'line1': line1.upper(),
            'line2': line2.upper()
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
