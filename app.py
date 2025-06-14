from flask import Flask, request, render_template, send_file
import barcode
from barcode.writer import ImageWriter
from PIL import Image, ImageDraw, ImageFont
import io
import zipfile

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        raw = request.form.get('codes', '')
        codes = [line.strip() for line in raw.splitlines() if line.strip()]
        return render_template('index.html', codes=codes, raw_input=raw)
    return render_template('index.html', codes=None, raw_input='')

def generate_barcode_image(code: str) -> bytes:
    buffer = io.BytesIO()
    code128 = barcode.get('code128', code, writer=ImageWriter())
    code128.write(buffer, {
        'module_height': 200.0,      # BARKOD yüksekliği maksimum
        'module_width': 0.75,        # kalınlık yüksek
        'font_size': 0,
        'quiet_zone': 4,
        'write_text': False
    })
    buffer.seek(0)
    barcode_img = Image.open(buffer)
    width, height = 1500, 1000
    etiket = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(etiket)

    try:
        font = ImageFont.truetype("arial.ttf", 240)  
    except:
        font = ImageFont.load_default()

    try:
        parts = code.split('-')
        # "B01-01 01-01"
        text_line = f"{parts[1]}-{parts[2]}  {parts[3]}-{parts[4]}"
    except:
        text_line = code

    draw.text((width // 2, 150), text_line, font=font, fill="black", anchor="mm")

    barcode_width = 1560
    barcode_height = 650
    barcode_img = barcode_img.resize((barcode_width, barcode_height))
    barcode_x = (width - barcode_width) // 2
    barcode_y = 300
    etiket.paste(barcode_img, (barcode_x, barcode_y))

    output = io.BytesIO()
    etiket.save(output, format="PNG", quality=100)
    output.seek(0)
    return output.read()

@app.route('/etiket/<code>')
def etiket(code):
    image_data = generate_barcode_image(code)
    return send_file(
        io.BytesIO(image_data),
        mimetype='image/png',
        as_attachment=True,
        download_name=f"{code}.png"
    )

@app.route('/download-all', methods=['POST'])
def download_all():
    raw = request.form.get('codes', '')
    codes = [line.strip() for line in raw.splitlines() if line.strip()]
    temp_zip = io.BytesIO()

    with zipfile.ZipFile(temp_zip, 'w') as zipf:
        for code in codes:
            image_data = generate_barcode_image(code)
            zipf.writestr(f"{code}.png", image_data)

    temp_zip.seek(0)
    return send_file(
        temp_zip,
        mimetype='application/zip',
        as_attachment=True,
        download_name="etiketler.zip"
    )

if __name__ == '__main__':
    app.run(debug=True)
