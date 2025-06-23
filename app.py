from flask import Flask, request, render_template, send_file
import barcode
from barcode.writer import ImageWriter
from PIL import Image, ImageDraw, ImageFont
import qrcode
import io
import zipfile

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        raw = request.form.get('codes', '')
        code_type = request.form.get('code_type', 'qr')  # barcode değil, qr olacak
        codes = [line.strip() for line in raw.splitlines() if line.strip()]
        return render_template('index.html', codes=codes, raw_input=raw, selected_type=code_type)
    
    # İlk GET isteğinde de QR varsayılan olacak
    return render_template('index.html', codes=None, raw_input='', selected_type='qr')

def generate_image(code: str, code_type: str = 'qr') -> bytes:
    # İlk etapta yatay A6 (100x150 mm = 1181x1772 px @ 300dpi)
    width, height = 1772, 1181
    etiket = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(etiket)

    try:
        font = ImageFont.truetype("arialbd.ttf", 285)
    except:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 240)

    try:
        parts = code.split('-')
        line1 = f"{parts[1]}-{parts[2]}"
        line2 = f"{parts[3]}-{parts[4]}"
    except:
        line1 = code
        line2 = ""

    spacing = 60
    bbox1 = draw.textbbox((0, 0), line1, font=font)
    bbox2 = draw.textbbox((0, 0), line2, font=font)
    h1 = bbox1[3] - bbox1[1]
    h2 = bbox2[3] - bbox2[1]
    total_text_height = h1 + h2 + spacing

    # Yazı konumu
    text_x = 50
    text_y = (height - total_text_height) // 2
    draw.text((text_x, text_y), line1, font=font, fill="black")

    # Alt satır ortalansın
    line1_width = bbox1[2] - bbox1[0]
    line2_width = bbox2[2] - bbox2[0]
    line2_x = text_x + (line1_width - line2_width) // 2
    draw.text((line2_x, text_y + h1 + spacing), line2, font=font, fill="black")

    # QR veya barkod
    if code_type == 'qr':
        qr = qrcode.QRCode(box_size=12, border=1)
        qr.add_data(code)
        qr.make(fit=True)
        qr_img = qr.make_image(fill_color="black", back_color="white").convert("RGB")
        qr_img = qr_img.resize((675,675), Image.LANCZOS)
    else:
        buffer = io.BytesIO()
        code128 = barcode.get('code128', code, writer=ImageWriter())
        code128.write(buffer, {
            'module_height': 120.0,
            'module_width': 0.4,
            'font_size': 0,
            'quiet_zone': 4,
            'write_text': False
        })
        buffer.seek(0)
        qr_img = Image.open(buffer).resize((720, 300))

    # QR konumu (sağa yaslı, ortalı)
    qr_x = width - qr_img.width - 60
    qr_y = (height - qr_img.height) // 2
    etiket.paste(qr_img, (qr_x, qr_y))

    # Tüm etiketi 90 derece saat yönünde döndür → 150 mm uzun kenar olacak
    etiket = etiket.rotate(90, expand=True)

    output = io.BytesIO()
    etiket.save(output, format="PNG", dpi=(300, 300))
    output.seek(0)
    return output.read()

@app.route('/etiket/<code>')
def etiket(code):
    code_type = request.args.get('type', 'barcode')
    image_data = generate_image(code, code_type)
    return send_file(
        io.BytesIO(image_data),
        mimetype='image/png',
        as_attachment=True,
        download_name=f"{code}.png"
    )

@app.route('/download-all', methods=['POST'])
def download_all():
    raw = request.form.get('codes', '')
    code_type = request.form.get('code_type', 'barcode')
    codes = [line.strip() for line in raw.splitlines() if line.strip()]
    temp_zip = io.BytesIO()

    with zipfile.ZipFile(temp_zip, 'w') as zipf:
        for code in codes:
            image_data = generate_image(code, code_type)
            zipf.writestr(f"{code}.png", image_data)

    temp_zip.seek(0)
    return send_file(
        temp_zip,
        mimetype='application/zip',
        as_attachment=True,
        download_name="etiketler.zip"
    )

@app.route('/print-all', methods=['POST'])
def print_all():
    raw = request.form.get('codes', '')
    code_type = request.form.get('code_type', 'barcode')
    codes = [line.strip() for line in raw.splitlines() if line.strip()]
    return render_template('print_all.html', codes=codes, selected_type=code_type)

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0")

