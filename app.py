import os
import sqlite3
from datetime import datetime
from functools import wraps

from flask import (
    Flask,
    abort,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from werkzeug.utils import secure_filename


BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, "school.db")
UPLOAD_DIR = os.path.join(BASE_DIR, "static", "images", "uploads")

os.makedirs(UPLOAD_DIR, exist_ok=True)


def create_app() -> Flask:
    app = Flask(__name__, template_folder="templates", static_folder="static")

    app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev-change-me")

    app.config["ADMIN_USERNAME"] = os.environ.get("ADMIN_USERNAME", "admin")
    app.config["ADMIN_PASSWORD"] = os.environ.get("ADMIN_PASSWORD", "password")

    init_db()

    allowed_image_extensions = {"png", "jpg", "jpeg", "webp"}
    gallery_categories = ["Grand Events","Achievements","Students Life","Special Day"]
    faculty_categories = ["admin", "science", "commerce"]

    def allowed_file(filename: str) -> bool:
        if not filename or "." not in filename:
            return False
        ext = filename.rsplit(".", 1)[1].lower()
        return ext in allowed_image_extensions

    def unique_upload_filename(prefix: str, original_filename: str) -> str:
        safe_name = secure_filename(original_filename)
        stamp = datetime.utcnow().strftime("%Y%m%d%H%M%S%f")
        return f"{prefix}_{stamp}_{safe_name}"

    def delete_file_if_exists(path: str) -> None:
        try:
            if path and os.path.exists(path):
                os.remove(path)
        except OSError:
            # File deletion failures shouldn't break DB operations.
            pass

    @app.context_processor
    def inject_globals():
        return {"now_year": datetime.utcnow().year}

    # -------------------------
    # Database helpers
    # -------------------------
    def get_conn():
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn

    def execute(query, params=()):
        with get_conn() as conn:
            cur = conn.execute(query, params)
            conn.commit()
            return cur.lastrowid

    def fetch_all(query, params=()):
        with get_conn() as conn:
            cur = conn.execute(query, params)
            return cur.fetchall()

    def fetch_one(query, params=()):
        with get_conn() as conn:
            cur = conn.execute(query, params)
            return cur.fetchone()

    # -------------------------
    # Public routes
    # -------------------------
    @app.route("/")
    def home():
        notices = []
        rows = fetch_all(
            """
            SELECT id, title, body, publish_date
            FROM notices
            ORDER BY publish_date DESC, id DESC
            LIMIT 5
            """,
        )
        for r in rows:
            publish_date = None
            if r["publish_date"]:
                publish_date = datetime.strptime(r["publish_date"], "%Y-%m-%d").date()
            notices.append(
                {
                    "id": r["id"],
                    "title": r["title"],
                    "body": r["body"],
                    "publish_date": publish_date,
                }
            )

        popups_raw = fetch_all(
            """
            SELECT id, title, image_filename
            FROM popup_banners
            WHERE is_active = 1
            ORDER BY id ASC
            """
        )
        popups = []
        for p in popups_raw:
            popups.append({
                "id": p["id"],
                "title": p["title"],
                "image_url": url_for("static", filename=f"images/uploads/{p['image_filename']}")
            })

        principal_msg = fetch_one("SELECT title, message FROM principal_message WHERE id = 1") or {"title": "Principal Message", "message": "\"Welcome to Friends Public H.S. School. We believe in holistic development and character building. Our goal is to provide a safe and nurturing environment for every child to excel in life.\""}

        return render_template(
            "home.html",
            body_class="bg-[#fcfdfe] text-slate-800",
            notices=notices,
            popups=popups,
            principal_msg=principal_msg,
        )

    @app.route("/about")
    def about():
        return render_template("about.html", body_class="dark-theme")

    @app.route("/academics")
    def academics():
        return render_template("academics.html", body_class="dark-theme")

    @app.route("/gallery")
    def gallery():
        # Expected public sections to keep your UI structure.
        gallery_sections = [
            {"name": "Grand Events", "swiper_class": "eventsSwiper"},
            {"name": "Achievements", "swiper_class": "achievementSwiper"},
            {"name": "Students Life", "swiper_class": "studentSwiper"},
            {"name": "Special Day", "swiper_class": "specialSwiper"},
        ]

        rows = fetch_all(
            """
            SELECT id, category, image_filename, alt_text, caption
            FROM gallery
            ORDER BY category ASC, uploaded_at DESC, id DESC
            """
        )
        by_category = {}
        for r in rows:
            by_category.setdefault(r["category"], []).append(
                {
                    "id": r["id"],
                    "url": url_for("static", filename=f"images/uploads/{r['image_filename']}"),
                    "alt_text": r["alt_text"] or "",
                    "caption": r["caption"],
                }
            )

        # Fallback to preserve the original visual layout when DB is empty.
        if not rows:
            by_category = {
                "Campus Heritage": [
                    {
                        "id": -1,
                        "url": "https://images.unsplash.com/photo-1541339907198-e08756ebafe3?q=80&w=600",
                        "alt_text": "The Main Arena",
                        "caption": "The Main Arena",
                    },
                    {
                        "id": -2,
                        "url": "https://images.unsplash.com/photo-1523050853064-dbad35009711?q=80&w=600",
                        "alt_text": "Campus event",
                        "caption": None,
                    },
                    {
                        "id": -3,
                        "url": "https://images.unsplash.com/photo-1562774053-701939374585?q=80&w=600",
                        "alt_text": "Campus event",
                        "caption": None,
                    },
                    {
                        "id": -4,
                        "url": "https://images.unsplash.com/photo-1509062522246-3755977927d7?q=80&w=600",
                        "alt_text": "Campus event",
                        "caption": None,
                    },
                    {
                        "id": -5,
                        "url": "https://images.unsplash.com/photo-1525921429624-479b6a26d84d?q=80&w=600",
                        "alt_text": "Campus event",
                        "caption": None,
                    },
                ],
                "Grand Events": [
                    {"id": -11, "url": "https://images.unsplash.com/photo-1523580494863-6f3031224c94?q=80&w=600", "alt_text": "Event", "caption": None},
                    {"id": -12, "url": "https://images.unsplash.com/photo-1511671782779-c97d3d27a1d4?q=80&w=600", "alt_text": "Event", "caption": None},
                    {"id": -13, "url": "https://images.unsplash.com/photo-1514525253344-f81bad3b7496?q=80&w=600", "alt_text": "Event", "caption": None},
                    {"id": -14, "url": "https://images.unsplash.com/photo-1492684223066-81342ee5ff30?q=80&w=600", "alt_text": "Event", "caption": None},
                    {"id": -15, "url": "https://images.unsplash.com/photo-1501281668745-f7f57925c3b4?q=80&w=600", "alt_text": "Event", "caption": None},
                ],
                "Sports Glory": [
                    {"id": -21, "url": "https://images.unsplash.com/photo-1546410531-bb4caa6b424d?q=80&w=600", "alt_text": "Sports", "caption": None},
                    {"id": -22, "url": "https://images.unsplash.com/photo-1461896836934-ffe607ba8211?q=80&w=600", "alt_text": "Sports", "caption": None},
                    {"id": -23, "url": "https://images.unsplash.com/photo-1574629810360-7efbbe195018?q=80&w=600", "alt_text": "Sports", "caption": None},
                    {"id": -24, "url": "https://images.unsplash.com/photo-1519861155730-0b5fbf0dd889?q=80&w=600", "alt_text": "Sports", "caption": None},
                    {"id": -25, "url": "https://images.unsplash.com/photo-1504450758481-7338ef752242?q=80&w=600", "alt_text": "Sports", "caption": None},
                ],
            }

        gallery_sections_render = []
        for section in gallery_sections:
            gallery_sections_render.append(
                {
                    "name": section["name"],
                    "swiper_class": section["swiper_class"],
                    "images": by_category.get(section["name"], []),
                }
            )

        return render_template("gallery.html", body_class="dark-theme", gallery_sections=gallery_sections_render)

    @app.route("/faculty")
    def faculty():
        rows = fetch_all(
            """
            SELECT id, name, category, title, image_filename
            FROM faculty
            ORDER BY category ASC, id DESC
            """
        )
        faculty_list = []
        for r in rows:
            faculty_list.append(
                {
                    "id": r["id"],
                    "name": r["name"],
                    "category": r["category"],
                    "title": r["title"],
                    "image_url": url_for("static", filename=f"images/uploads/{r['image_filename']}"),
                }
            )

        if not rows:
            faculty_list = [
                {
                    "id": -1,
                    "name": "Mr. Dhul Singh Patidar",
                    "category": "admin",
                    "title": "Principal & Director",
                    "image_url": url_for("static", filename="images/Principal.jpeg"),
                },
                {
                    "id": -2,
                    "name": "Dr. Anjali Sharma",
                    "category": "science",
                    "title": "HOD - Science Dept.",
                    "image_url": "https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?w=150",
                },
                {
                    "id": -3,
                    "name": "Mr. Rajesh Gupta",
                    "category": "commerce",
                    "title": "Sr. Commerce Mentor",
                    "image_url": "https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=150",
                },
                {
                    "id": -4,
                    "name": "Mrs. Kavita Jain",
                    "category": "science",
                    "title": "Biology Specialist",
                    "image_url": "https://images.unsplash.com/photo-1580894732230-282b963aee58?w=150",
                },
                {
                    "id": -5,
                    "name": "Mr. Vikram Singh",
                    "category": "admin",
                    "title": "Academic Coordinator",
                    "image_url": "https://images.unsplash.com/photo-1560250097-0b93528c311a?w=150",
                },
            ]

        return render_template("faculty.html", body_class="dark-theme", faculty_list=faculty_list)

    @app.route("/contact", methods=["GET", "POST"])
    def contact():
        if request.method == "POST":
            full_name = (request.form.get("full_name") or "").strip()
            email = (request.form.get("email") or "").strip()
            phone = (request.form.get("phone") or "").strip()
            message = (request.form.get("message") or "").strip()

            if not full_name:
                flash("Please enter your name.", "error")
                return redirect(url_for("contact"))

            execute(
                """
                INSERT INTO admissions (student_name, father_name, email, phone, class_seeking, message, source)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (full_name, "", email, phone, "", message, "contact"),
            )
            flash("Message received. We'll get back to you shortly.", "success")
            return redirect(url_for("contact"))

        return render_template("contact.html", body_class="dark-theme")

    @app.route("/admission", methods=["GET", "POST"])
    def admission():
        if request.method == "POST":
            student_name = (request.form.get("student_name") or "").strip()
            father_name = (request.form.get("father_name") or "").strip()
            email = (request.form.get("email") or "").strip()
            phone = (request.form.get("phone") or "").strip()
            class_seeking = (request.form.get("class_seeking") or "").strip()
            message = (request.form.get("message") or "").strip()

            if not student_name:
                flash("Please enter student name.", "error")
                return redirect(url_for("admission"))

            execute(
                """
                INSERT INTO admissions (student_name, father_name, email, phone, class_seeking, message, source)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (student_name, father_name, email, phone, class_seeking, message, "admission"),
            )
            flash("Enquiry submitted successfully. We'll contact you within 24 hours.", "success")
            return redirect(url_for("admission"))

        return render_template("admission.html", body_class="dark-theme")

    # -------------------------
    # Admin auth + pages (stub)
    # -------------------------
    def admin_required(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            if not session.get("admin_logged_in"):
                return redirect(url_for("admin_login"))
            return fn(*args, **kwargs)

        return wrapper

    @app.route("/admin/login", methods=["GET", "POST"])
    def admin_login():
        if request.method == "POST":
            username = (request.form.get("username") or "").strip()
            password = request.form.get("password") or ""

            if username == app.config["ADMIN_USERNAME"] and password == app.config["ADMIN_PASSWORD"]:
                session["admin_logged_in"] = True
                flash("Admin login successful.", "success")
                return redirect(url_for("admin_dashboard"))

            flash("Invalid admin credentials.", "error")
        return render_template("admin/login.html")

    @app.route("/admin/logout")
    def admin_logout():
        session.pop("admin_logged_in", None)
        flash("Logged out.", "success")
        return redirect(url_for("admin_login"))

    @app.route("/admin")
    @app.route("/admin/dashboard")
    @admin_required
    def admin_dashboard():
        notices_count = fetch_one("SELECT COUNT(*) AS c FROM notices")["c"]
        gallery_count = fetch_one("SELECT COUNT(*) AS c FROM gallery")["c"]
        faculty_count = fetch_one("SELECT COUNT(*) AS c FROM faculty")["c"]
        admissions_count = fetch_one("SELECT COUNT(*) AS c FROM admissions")["c"]
        popups_count = fetch_one("SELECT COUNT(*) AS c FROM popup_banners")["c"]

        return render_template(
            "admin/dashboard.html",
            notices_count=notices_count,
            gallery_count=gallery_count,
            faculty_count=faculty_count,
            admissions_count=admissions_count,
            popups_count=popups_count,
        )

    # -------------------------
    # Admin: Notices CRUD
    # -------------------------
    @app.route("/admin/notices", methods=["GET"])
    @admin_required
    def admin_notices():
        notices = fetch_all("SELECT id, title, body, publish_date FROM notices ORDER BY publish_date DESC, id DESC")
        return render_template("admin/notices.html", body_class="", notices=notices, editing_notice=None)

    @app.route("/admin/notices/new", methods=["POST"])
    @admin_required
    def admin_notices_new():
        title = (request.form.get("title") or "").strip()
        body = (request.form.get("body") or "").strip()
        publish_date = (request.form.get("publish_date") or "").strip()

        if not title or not publish_date:
            flash("Title and publish date are required.", "error")
            return redirect(url_for("admin_notices"))

        execute(
            """
            INSERT INTO notices (title, body, publish_date)
            VALUES (?, ?, ?)
            """,
            (title, body, publish_date),
        )
        flash("Notice added.", "success")
        return redirect(url_for("admin_notices"))

    @app.route("/admin/notices/edit/<int:notice_id>", methods=["GET"])
    @admin_required
    def admin_notices_edit(notice_id: int):
        notice = fetch_one("SELECT id, title, body, publish_date FROM notices WHERE id = ?", (notice_id,))
        if not notice:
            abort(404)
        notices = fetch_all("SELECT id, title, body, publish_date FROM notices ORDER BY publish_date DESC, id DESC")
        return render_template("admin/notices.html", body_class="", notices=notices, editing_notice=notice)

    @app.route("/admin/notices/edit/<int:notice_id>", methods=["POST"])
    @admin_required
    def admin_notices_edit_post(notice_id: int):
        title = (request.form.get("title") or "").strip()
        body = (request.form.get("body") or "").strip()
        publish_date = (request.form.get("publish_date") or "").strip()

        if not title or not publish_date:
            flash("Title and publish date are required.", "error")
            return redirect(url_for("admin_notices_edit", notice_id=notice_id))

        execute(
            """
            UPDATE notices
            SET title = ?, body = ?, publish_date = ?
            WHERE id = ?
            """,
            (title, body, publish_date, notice_id),
        )
        flash("Notice updated.", "success")
        return redirect(url_for("admin_notices"))

    @app.route("/admin/notices/delete/<int:notice_id>", methods=["POST"])
    @admin_required
    def admin_notices_delete(notice_id: int):
        execute("DELETE FROM notices WHERE id = ?", (notice_id,))
        flash("Notice deleted.", "success")
        return redirect(url_for("admin_notices"))

    # -------------------------
    # Admin: Gallery CRUD
    # -------------------------
    @app.route("/admin/gallery", methods=["GET"])
    @admin_required
    def admin_gallery():
        rows = fetch_all("SELECT id, category, image_filename, alt_text, caption, uploaded_at FROM gallery ORDER BY uploaded_at DESC, id DESC")
        return render_template("admin/gallery.html", body_class="", gallery_rows=rows, gallery_categories=gallery_categories)

    @app.route("/admin/gallery/upload", methods=["POST"])
    @admin_required
    def admin_gallery_upload():
        category = (request.form.get("category") or "").strip()
        alt_text = (request.form.get("alt_text") or "").strip()
        caption = (request.form.get("caption") or "").strip()
        file = request.files.get("image")

        if category not in gallery_categories:
            flash("Invalid gallery category.", "error")
            return redirect(url_for("admin_gallery"))

        if not file or file.filename == "":
            flash("Please select an image to upload.", "error")
            return redirect(url_for("admin_gallery"))

        if not allowed_file(file.filename):
            flash("Unsupported image format.", "error")
            return redirect(url_for("admin_gallery"))

        new_name = unique_upload_filename("gallery", file.filename)
        file_path = os.path.join(UPLOAD_DIR, new_name)
        file.save(file_path)

        execute(
            """
            INSERT INTO gallery (category, image_filename, alt_text, caption)
            VALUES (?, ?, ?, ?)
            """,
            (category, new_name, alt_text, caption or None),
        )
        flash("Gallery image uploaded.", "success")
        return redirect(url_for("admin_gallery"))

    @app.route("/admin/gallery/delete/<int:image_id>", methods=["POST"])
    @admin_required
    def admin_gallery_delete(image_id: int):
        row = fetch_one("SELECT id, image_filename FROM gallery WHERE id = ?", (image_id,))
        if not row:
            abort(404)

        execute("DELETE FROM gallery WHERE id = ?", (image_id,))

        delete_file_if_exists(os.path.join(UPLOAD_DIR, row["image_filename"]))
        flash("Gallery image deleted.", "success")
        return redirect(url_for("admin_gallery"))

    # -------------------------
    # Admin: Faculty CRUD
    # -------------------------
    @app.route("/admin/faculty", methods=["GET"])
    @admin_required
    def admin_faculty():
        rows = fetch_all("SELECT id, name, category, title, image_filename FROM faculty ORDER BY category ASC, id DESC")
        return render_template("admin/faculty.html", body_class="", faculty_rows=rows, faculty_categories=faculty_categories)

    @app.route("/admin/faculty/new", methods=["POST"])
    @admin_required
    def admin_faculty_new():
        name = (request.form.get("name") or "").strip()
        category = (request.form.get("category") or "").strip()
        title = (request.form.get("title") or "").strip()
        file = request.files.get("image")

        if category not in faculty_categories:
            flash("Invalid faculty category.", "error")
            return redirect(url_for("admin_faculty"))

        if not name or not title:
            flash("Name and title are required.", "error")
            return redirect(url_for("admin_faculty"))

        if not file or file.filename == "":
            flash("Please select an image.", "error")
            return redirect(url_for("admin_faculty"))

        if not allowed_file(file.filename):
            flash("Unsupported image format.", "error")
            return redirect(url_for("admin_faculty"))

        new_name = unique_upload_filename("faculty", file.filename)
        file_path = os.path.join(UPLOAD_DIR, new_name)
        file.save(file_path)

        execute(
            """
            INSERT INTO faculty (name, category, title, image_filename)
            VALUES (?, ?, ?, ?)
            """,
            (name, category, title, new_name),
        )
        flash("Faculty member added.", "success")
        return redirect(url_for("admin_faculty"))

    @app.route("/admin/faculty/edit/<int:faculty_id>", methods=["GET"])
    @admin_required
    def admin_faculty_edit(faculty_id: int):
        row = fetch_one("SELECT id, name, category, title, image_filename FROM faculty WHERE id = ?", (faculty_id,))
        if not row:
            abort(404)
        rows = fetch_all("SELECT id, name, category, title, image_filename FROM faculty ORDER BY category ASC, id DESC")
        return render_template("admin/faculty.html", body_class="", faculty_rows=rows, faculty_categories=faculty_categories, editing_faculty=row)

    @app.route("/admin/faculty/edit/<int:faculty_id>", methods=["POST"])
    @admin_required
    def admin_faculty_edit_post(faculty_id: int):
        name = (request.form.get("name") or "").strip()
        category = (request.form.get("category") or "").strip()
        title = (request.form.get("title") or "").strip()
        file = request.files.get("image")

        if category not in faculty_categories:
            flash("Invalid faculty category.", "error")
            return redirect(url_for("admin_faculty_edit", faculty_id=faculty_id))

        if not name or not title:
            flash("Name and title are required.", "error")
            return redirect(url_for("admin_faculty_edit", faculty_id=faculty_id))

        existing = fetch_one("SELECT id, image_filename FROM faculty WHERE id = ?", (faculty_id,))
        if not existing:
            abort(404)

        new_filename = existing["image_filename"]
        if file and file.filename:
            if not allowed_file(file.filename):
                flash("Unsupported image format.", "error")
                return redirect(url_for("admin_faculty_edit", faculty_id=faculty_id))
            new_filename = unique_upload_filename("faculty", file.filename)
            file.save(os.path.join(UPLOAD_DIR, new_filename))
            delete_file_if_exists(os.path.join(UPLOAD_DIR, existing["image_filename"]))

        execute(
            """
            UPDATE faculty
            SET name = ?, category = ?, title = ?, image_filename = ?
            WHERE id = ?
            """,
            (name, category, title, new_filename, faculty_id),
        )
        flash("Faculty member updated.", "success")
        return redirect(url_for("admin_faculty"))

    @app.route("/admin/faculty/delete/<int:faculty_id>", methods=["POST"])
    @admin_required
    def admin_faculty_delete(faculty_id: int):
        row = fetch_one("SELECT id, image_filename FROM faculty WHERE id = ?", (faculty_id,))
        if not row:
            abort(404)
        execute("DELETE FROM faculty WHERE id = ?", (faculty_id,))
        delete_file_if_exists(os.path.join(UPLOAD_DIR, row["image_filename"]))
        flash("Faculty member deleted.", "success")
        return redirect(url_for("admin_faculty"))

    # -------------------------
    # Admin: Admissions view
    # -------------------------
    @app.route("/admin/admissions", methods=["GET"])
    @admin_required
    def admin_admissions():
        rows = fetch_all(
            """
            SELECT id, student_name, father_name, email, phone, class_seeking, message, source, created_at
            FROM admissions
            ORDER BY created_at DESC, id DESC
            """
        )
        return render_template("admin/admissions.html", body_class="", admissions_rows=rows)

    @app.route("/admin/delete_query/<int:query_id>", methods=["POST"])
    @admin_required
    def admin_delete_query(query_id: int):
        row = fetch_one("SELECT id FROM admissions WHERE id = ?", (query_id,))
        if not row:
            abort(404)
        execute("DELETE FROM admissions WHERE id = ?", (query_id,))
        flash("Query deleted successfully.", "success")
        return redirect(url_for("admin_admissions"))

    # -------------------------
    # Admin: Popup Banners CRUD
    # -------------------------
    @app.route("/admin/popups", methods=["GET"])
    @admin_required
    def admin_popups():
        rows = fetch_all("SELECT id, title, image_filename, is_active, created_at FROM popup_banners ORDER BY created_at DESC, id DESC")
        return render_template("admin/popups.html", body_class="", popup_rows=rows)

    @app.route("/admin/popups/upload", methods=["POST"])
    @admin_required
    def admin_popups_upload():
        title = (request.form.get("title") or "").strip()
        file = request.files.get("image")

        if not file or file.filename == "":
            flash("Please select an image to upload.", "error")
            return redirect(url_for("admin_popups"))

        if not allowed_file(file.filename):
            flash("Unsupported image format.", "error")
            return redirect(url_for("admin_popups"))

        new_name = unique_upload_filename("popup", file.filename)
        file_path = os.path.join(UPLOAD_DIR, new_name)
        file.save(file_path)

        execute(
            """
            INSERT INTO popup_banners (title, image_filename, is_active)
            VALUES (?, ?, 1)
            """,
            (title or None, new_name),
        )
        flash("Popup banner uploaded.", "success")
        return redirect(url_for("admin_popups"))

    @app.route("/admin/popups/toggle/<int:popup_id>", methods=["POST"])
    @admin_required
    def admin_popups_toggle(popup_id: int):
        row = fetch_one("SELECT id, is_active FROM popup_banners WHERE id = ?", (popup_id,))
        if not row:
            abort(404)
        new_status = 0 if row["is_active"] else 1
        execute("UPDATE popup_banners SET is_active = ? WHERE id = ?", (new_status, popup_id))
        flash(f"Popup banner {'activated' if new_status else 'deactivated'}.", "success")
        return redirect(url_for("admin_popups"))

    @app.route("/admin/popups/delete/<int:popup_id>", methods=["POST"])
    @admin_required
    def admin_popups_delete(popup_id: int):
        row = fetch_one("SELECT id, image_filename FROM popup_banners WHERE id = ?", (popup_id,))
        if not row:
            abort(404)

        execute("DELETE FROM popup_banners WHERE id = ?", (popup_id,))
        delete_file_if_exists(os.path.join(UPLOAD_DIR, row["image_filename"]))
        flash("Popup banner deleted.", "success")
        return redirect(url_for("admin_popups"))

    # -------------------------
    # Admin: Principal Message
    # -------------------------
    @app.route("/admin/principal_message", methods=["GET", "POST"])
    @admin_required
    def admin_principal_message():
        if request.method == "POST":
            title = (request.form.get("title") or "").strip()
            message = (request.form.get("message") or "").strip()

            if not message:
                flash("Message is required.", "error")
            else:
                execute(
                    """
                    INSERT INTO principal_message (id, title, message, updated_at) 
                    VALUES (1, ?, ?, datetime('now'))
                    ON CONFLICT(id) DO UPDATE SET title=excluded.title, message=excluded.message, updated_at=excluded.updated_at
                    """,
                    (title, message)
                )
                flash("Principal message updated successfully.", "success")
            return redirect(url_for("admin_principal_message"))

        msg = fetch_one("SELECT title, message FROM principal_message WHERE id = 1")
        if not msg:
            msg = {"title": "Principal Message", "message": "\"Welcome to Friends Public H.S. School. We believe in holistic development and character building. Our goal is to provide a safe and nurturing environment for every child to excel in life.\""}
            
        return render_template("admin/principal_message.html", body_class="", msg=msg)

    return app


def init_db():
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS notices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                body TEXT,
                publish_date TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
            """
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS gallery (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT NOT NULL,
                image_filename TEXT NOT NULL,
                alt_text TEXT,
                caption TEXT,
                uploaded_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
            """
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS faculty (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                category TEXT NOT NULL,
                title TEXT NOT NULL,
                image_filename TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
            """
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS admissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_name TEXT NOT NULL,
                father_name TEXT,
                email TEXT,
                phone TEXT,
                class_seeking TEXT,
                message TEXT,
                source TEXT NOT NULL DEFAULT 'admission',
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
            """
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS popup_banners (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                image_filename TEXT NOT NULL,
                is_active INTEGER DEFAULT 1,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
            """
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS principal_message (
                id INTEGER PRIMARY KEY,
                title TEXT,
                message TEXT NOT NULL,
                updated_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
            """
        )
        
        conn.execute(
            """
            INSERT OR IGNORE INTO principal_message (id, title, message)
            VALUES (1, 'Principal Message', '"Welcome to Friends Public H.S. School. We believe in holistic development and character building. Our goal is to provide a safe and nurturing environment for every child to excel in life."')
            """
        )

        conn.commit()
    finally:
        conn.close()


app = create_app()


if __name__ == "__main__":
    app.run(debug=True)



