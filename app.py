import os
from uuid import uuid4
from datetime import datetime, date, timezone
from io import BytesIO

from flask import (
    Flask, render_template, request, redirect, url_for,
    flash, send_file, session, send_from_directory
)
from werkzeug.utils import secure_filename
import pandas as pd

from config import Config
from models import db, GuestFollow

app = Flask(__name__)
app.config.from_object(Config)
app.config['MAX_CONTENT_LENGTH'] = app.config['MAX_UPLOAD_MB'] * 1024 * 1024

@app.context_processor
def inject_datetime():
    from datetime import datetime as _dt
    return {"datetime": _dt}

db.init_app(app)
with app.app_context():
    db.create_all()

try:
    from zoneinfo import ZoneInfo
    JKT = ZoneInfo("Asia/Jakarta")
except Exception:
    JKT = None

ALLOWED_EXT = {"jpg", "jpeg", "png"}
os.makedirs(app.config['UPLOAD_DIR'], exist_ok=True)

# =====================================================
# ==================== ROUTES ==========================
# =====================================================

@app.get('/')
def index():
    today_str = datetime.now().strftime('%Y-%m-%d')
    return render_template('index.html', today_str=today_str)

@app.post('/upload_follow_proof')
def upload_follow_proof():
    file = request.files.get('proofFile')
    if not file or not file.filename:
        return {'ok': False, 'msg': 'tidak ada file'}
    ext = secure_filename(file.filename).rsplit('.', 1)[1].lower()
    if ext not in ALLOWED_EXT:
        return {'ok': False, 'msg': 'format salah'}
    filename = f"follow_{uuid4().hex}.{ext}"
    file.save(os.path.join(app.config['UPLOAD_DIR'], filename))
    session['follow_proof_filename'] = filename
    return {'ok': True, 'filename': filename}

@app.post('/form')
def submit_form():
    nik = request.form.get('nik', '').strip() or None
    name = request.form.get('name', '').strip()
    address = request.form.get('address', '').strip() or None
    institution = request.form.get('institution', '').strip() or None
    purpose = request.form.get('purpose', '').strip()
    phone = request.form.get('phone', '').strip() or None
    photo = request.files.get('photo_camera')

    # === Ambil bukti follow dari session (kalau ada) ===
    follow_filename = session.get('follow_proof_filename')

    if not name or not purpose:
        flash('Nama dan keperluan wajib diisi', 'danger')
        return redirect(url_for('form_page'))

    filename = None
    if photo and photo.filename:
        ext = secure_filename(photo.filename).rsplit('.', 1)[1].lower()
        if ext not in ALLOWED_EXT:
            flash('Format foto harus JPG/PNG', 'danger')
            return redirect(url_for('form_page'))
        filename = f"{uuid4().hex}.{ext}"
        photo.save(os.path.join(app.config['UPLOAD_DIR'], filename))

    guest = GuestFollow(   # pakai model baru kamu
        nik=nik, name=name, address=address,
        institution=institution, purpose=purpose,
        phone=phone, photo_filename=filename,
        follow_proof=follow_filename   # <--- simpan di database
    )
    db.session.add(guest)
    db.session.commit()

    # Bersihkan session agar tidak nyangkut di data berikutnya
    session.pop('follow_proof_filename', None)

    flash('Terima kasih! Data kamu sudah tercatat.', 'success')
    return redirect(url_for('form_page'))


@app.get('/form')
def form_page():
    today_str = datetime.now().strftime('%Y-%m-%d')
    return render_template('form.html', today_str=today_str)

# =====================================================
# ================= ADMIN AREA ========================
# =====================================================

def login_required(view):
    from functools import wraps
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return redirect(url_for('admin_login'))
        return view(*args, **kwargs)
    return wrapped

@app.get('/admin/login')
def admin_login():
    return render_template('admin_login.html')

@app.post('/admin/login')
def admin_login_post():
    if request.form.get('password') == app.config['ADMIN_PASSWORD']:
        session['admin_logged_in'] = True
        return redirect(url_for('admin_dashboard'))
    flash('Password salah', 'danger')
    return redirect(url_for('admin_login'))

@app.get('/admin/logout')
def admin_logout():
    session.clear()
    flash('Anda sudah keluar.', 'success')
    return redirect(url_for('index'))

@app.get('/admin')
@login_required
def admin_dashboard():
    q = GuestFollow.query.order_by(GuestFollow.created_at.desc())

    # Filter berdasarkan tanggal (opsional)
    from_str = request.args.get('from')
    to_str = request.args.get('to')

    def parse_date(s):
        try:
            return datetime.strptime(s, '%Y-%m-%d').date()
        except Exception:
            return None

    d_from = parse_date(from_str)
    d_to = parse_date(to_str)

    if d_from:
        q = q.filter(GuestFollow.created_at >= datetime.combine(d_from, datetime.min.time()))
    if d_to:
        q = q.filter(GuestFollow.created_at <= datetime.combine(d_to, datetime.max.time()))

    guests = q.all()
    return render_template(
        'admin_dashboard.html',
        guests=guests,
        from_str=from_str or '',
        to_str=to_str or ''
    )

@app.get('/admin/export.xlsx')
@login_required
def export_excel():
    q = GuestFollow.query.order_by(GuestFollow.created_at.desc())

    # Filter tanggal jika user isi "from" dan "to"
    from_str = request.args.get('from')
    to_str = request.args.get('to')

    def parse_date(s):
        try:
            return datetime.strptime(s, '%Y-%m-%d').date()
        except Exception:
            return None

    d_from = parse_date(from_str)
    d_to = parse_date(to_str)
    if d_from:
        q = q.filter(GuestFollow.created_at >= datetime.combine(d_from, datetime.min.time()))
    if d_to:
        q = q.filter(GuestFollow.created_at <= datetime.combine(d_to, datetime.max.time()))

    guests = q.all()

    # Buat DataFrame untuk Excel
    rows = []
    for g in guests:
        rows.append([
            g.id,
            g.nik or '',
            g.name,
            g.address or '',
            g.institution or '',
            g.purpose,
            g.phone or '',
            g.photo_filename or '',
            g.follow_proof or '',
            g.created_at.strftime('%Y-%m-%d %H:%M:%S')
        ])

    df = pd.DataFrame(rows, columns=[
        "ID", "NIK", "Nama", "Alamat", "Instansi", "Keperluan",
        "Nomor HP", "Foto", "Bukti Follow", "Waktu (UTC)"
    ])

    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='BukuTamu')
    output.seek(0)

    return send_file(
        output,
        as_attachment=True,
        download_name=f"bukutamu_{date.today()}.xlsx",
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

@app.get('/media/<path:filename>')
def media(filename):
    return send_from_directory(app.config['UPLOAD_DIR'], filename)

if __name__ == '__main__':
    # app.run(debug=True)
    app.run(host='0.0.0.0', port=5000, debug=True)
