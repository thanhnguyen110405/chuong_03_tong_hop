from flask import Flask, request, url_for, abort, redirect, make_response
from markupsafe import escape

app = Flask(__name__)
# Cấu hình JSON hiển thị tiếng Việt có dấu
app.json.ensure_ascii = False 

# Dữ liệu mẫu
STUDENTS = { 
    "23T1020001": {"name": "Nguyễn Văn An", "lop": "K47A", "scores": {"PMMNM": 8.5, "CSDL": 7.0, "MMT": 9.0}}, 
    "23T1020002": {"name": "Trần Thị Bình", "lop": "K47A", "scores": {"PMMNM": 6.0, "CSDL": 5.5, "MMT": 7.0}}, 
    "23T1020003": {"name": "Lê Hoàng Cường", "lop": "K47B", "scores": {"PMMNM": 9.5, "CSDL": 9.0}}, 
    "23T1020004": {"name": "Phạm Minh Dũng", "lop": "K47B", "scores": {"PMMNM": 4.0, "CSDL": 3.5, "MMT": 5.0}}, 
    "23T1020005": {"name": "Hoàng Thu Hà", "lop": "K47A", "scores": {}}, 
    "23T1020006": {"name": "Võ Quốc Khánh", "lop": "K47C", "scores": {"PMMNM": 7.5, "MMT": 8.0}}, 
}

# --- PHẦN 0: HÀM PHỤ VÀ KHUNG TRANG ---

def average(scores):
    if not scores:
        return None
    return round(sum(scores.values()) / len(scores), 2)

def rank(avg):
    if avg is None:
        return "Chưa có điểm"
    if avg >= 8.5:
        return "Giỏi"
    if avg >= 7.0:
        return "Khá"
    if avg >= 5.0:
        return "Trung bình"
    return "Yếu"

def student_summary(mssv):
    if mssv not in STUDENTS:
        return None
    sv = STUDENTS[mssv]
    avg = average(sv["scores"])
    return {
        "mssv": mssv,
        "name": sv["name"],
        "lop": sv["lop"],
        "scores": sv["scores"],
        "average": avg,
        "rank": rank(avg)
    }

def layout(title, body):
    safe_title = escape(title)
    return f"""<!DOCTYPE html>
<html>
<head><title>{safe_title} - Sổ điểm</title></head>
<body>
    <nav>
        <a href="{url_for('home')}">Trang chủ</a> · 
        <a href="{url_for('student_list')}">Sinh viên</a> · 
        <a href="{url_for('search_student')}">Tìm kiếm sinh viên</a>
    </nav>
    <hr>
    {body}
</body>
</html>"""


# --- PHẦN 1: GIAO DIỆN WEB ---

@app.route("/")
def home():
    so_sv = len(STUDENTS)
    cac_lop = set(sv["lop"] for sv in STUDENTS.values())
    body = f"""
        <h2>Trang chủ Sổ điểm</h2>
        <p>Tổng số sinh viên: <strong>{so_sv}</strong></p>
        <p>Số lớp: <strong>{len(cac_lop)}</strong></p>
        <ul>
            <li><a href="{url_for('student_list')}">Xem danh sách sinh viên (HTML)</a></li>
            <li><a href="{url_for('api_students')}">Xem danh sách sinh viên (API JSON)</a></li>
        </ul>
    """
    return layout("Trang chủ", body)

@app.route("/students")
def student_list():
    lop_filter = request.args.get("lop", "").strip().upper()
    cac_lop = sorted(set(sv["lop"] for sv in STUDENTS.values()))
    
    # Thanh lọc lớp
    nav_filter = f'<a href="{url_for("student_list")}">Tất cả</a>'
    for l in cac_lop:
        nav_filter += f' | <a href="{url_for("student_list", lop=l)}">{escape(l)}</a>'
    
    table_rows = ""
    count = 0
    for mssv in STUDENTS:
        sv = student_summary(mssv)
        if lop_filter and sv["lop"].upper() != lop_filter:
            continue
        count += 1
        avg_str = str(sv["average"]) if sv["average"] is not None else "—"
        table_rows += f"""
        <tr>
            <td><a href="{url_for('student_detail', mssv=mssv)}">{escape(mssv)}</a></td>
            <td>{escape(sv['name'])}</td>
            <td>{escape(sv['lop'])}</td>
            <td>{escape(avg_str)}</td>
            <td>{escape(sv['rank'])}</td>
        </tr>"""
    
    if count > 0:
        content = f"""
        <table border="1" cellpadding="5" cellspacing="0">
            <tr><th>MSSV</th><th>Họ tên</th><th>Lớp</th><th>Điểm TB</th><th>Xếp loại</th></tr>
            {table_rows}
        </table>"""
    else:
        content = "<p>Không có sinh viên phù hợp.</p>"
        
    body = f"<h2>Danh sách sinh viên</h2><p>Lọc: {nav_filter}</p>{content}"
    return layout("Danh sách sinh viên", body)

@app.route("/students/<mssv>")
def student_detail(mssv):
    sv = student_summary(mssv)
    if not sv:
        abort(404, description=f"Không có sinh viên với MSSV = {mssv}.")
        
    avg_str = str(sv["average"]) if sv["average"] is not None else "—"
    scores_rows = "".join([f"<tr><td>{escape(hp)}</td><td>{escape(str(diem))}</td></tr>" for hp, diem in sv["scores"].items()])
    
    scores_table = f"""
    <table border="1" cellpadding="5" cellspacing="0">
        <tr><th>Học phần</th><th>Điểm</th></tr>
        {scores_rows}
    </table>""" if sv["scores"] else "<p>Chưa có điểm học phần nào.</p>"
    
    body = f"""
        <h2>Chi tiết sinh viên: {escape(sv['name'])}</h2>
        <p><strong>MSSV:</strong> {escape(sv['mssv'])}</p>
        <p><strong>Lớp:</strong> <a href="{url_for('student_list', lop=sv['lop'])}">{escape(sv['lop'])}</a></p>
        <p><strong>Điểm TB:</strong> {escape(avg_str)} | <strong>Xếp loại:</strong> {escape(sv['rank'])}</p>
        <p>
            <a href="{url_for('export_csv', mssv=mssv)}">Tải bảng điểm (CSV)</a> | 
            Link rút gọn: <code>{url_for('sv_short', mssv=mssv)}</code>
        </p>
        <h3>Bảng điểm</h3>
        {scores_table}
    """
    return layout(f"Chi tiết {mssv}", body)

@app.route("/sv/<mssv>")
def sv_short(mssv):
    return redirect(url_for('student_detail', mssv=mssv), code=301)

@app.route("/students/<mssv>/export")
def export_csv(mssv):
    sv = student_summary(mssv)
    if not sv:
        abort(404, description=f"Không có sinh viên với MSSV = {mssv}.")
        
    csv_lines = ["hoc_phan,diem"]
    for hp, diem in sv["scores"].items():
        csv_lines.append(f"{hp},{diem}")
    csv_data = "\n".join(csv_lines)
    
    response = make_response(csv_data)
    response.headers["Content-Type"] = "text/csv; charset=utf-8"
    response.headers["Content-Disposition"] = f"attachment; filename=diem_{mssv}.csv"
    return response

@app.route("/search")
def search_student():
    q = request.args.get("q", "")
    safe_q = escape(q)
    
    body = f"""
        <h2>Tìm kiếm sinh viên</h2>
        <form method="GET" action="{url_for('search_student')}">
            <input type="text" name="q" value="{safe_q}" placeholder="Nhập tên hoặc MSSV...">
            <button type="submit">Tìm</button>
        </form>
    """
    if q:
        results = []
        for mssv, data in STUDENTS.items():
            if q.lower() in data["name"].lower() or q.lower() in mssv.lower():
                results.append(mssv)
                
        body += f"<p>Tìm thấy {len(results)} kết quả cho “{safe_q}”</p><ul>"
        for m in results:
            s = STUDENTS[m]
            body += f'<li><a href="{url_for("student_detail", mssv=m)}">{escape(m)} - {escape(s["name"])}</a></li>'
        body += "</ul>"
        
    return layout("Tìm kiếm", body)


# --- PHẦN 2: API JSON ---

@app.route("/api/students")
def api_students():
    lop_filter = request.args.get("lop", "").strip().upper()
    min_avg_raw = request.args.get("min_avg")
    
    min_avg = None
    if min_avg_raw is not None:
        try:
            min_avg = float(min_avg_raw)
        except ValueError:
            abort(400, description="Giá trị min_avg không hợp lệ.")
            
    res = []
    for mssv in STUDENTS:
        sv = student_summary(mssv)
        if lop_filter and sv["lop"].upper() != lop_filter:
            continue
        if min_avg is not None:
            if sv["average"] is None or sv["average"] < min_avg:
                continue
        res.append(sv)
    return res

@app.route("/api/students/<mssv>")
def api_student_detail(mssv):
    sv = student_summary(mssv)
    if not sv:
        abort(404, description=f"Không có sinh viên với MSSV = {mssv}.")
    return sv

@app.route("/api/students/<mssv>/scores/<course>", methods=["GET", "PUT", "DELETE"])
def api_course_score(mssv, course):
    if mssv not in STUDENTS:
        abort(404, description=f"Không có sinh viên với MSSV = {mssv}.")
        
    course = course.upper()
    scores = STUDENTS[mssv]["scores"]
    
    if request.method == "GET":
        if course not in scores:
            abort(404, description=f"Học phần {course} chưa có điểm.")
        return {"mssv": mssv, "course": course, "score": scores[course]}
        
    elif request.method == "DELETE":
        if course not in scores:
            abort(404, description=f"Học phần {course} chưa có điểm.")
        del scores[course]
        return "", 204
        
    elif request.method == "PUT":
        score_raw = request.args.get("score")
        if score_raw is None:
            abort(400, description="Thiếu tham số score.")
        try:
            score = float(score_raw)
            if score < 0 or score > 10:
                raise ValueError
        except ValueError:
            abort(400, description="Điểm score phải là số trong khoảng [0, 10].")
            
        is_new = course not in scores
        scores[course] = score
        
        body = {
            "mssv": mssv,
            "course": course,
            "score": score,
            "average": average(scores)
        }
        
        if is_new:
            resp = make_response(body, 201)
            resp.headers["Location"] = url_for("api_course_score", mssv=mssv, course=course)
            return resp
        return body, 200


# --- PHẦN 3: XỬ LÝ LỖI THỐNG NHẤT ---

ERROR_TITLES = {
    400: "Dữ liệu không hợp lệ",
    404: "Không tìm thấy",
    405: "Phương thức không được hỗ trợ"
}

@app.errorhandler(400)
@app.errorhandler(404)
@app.errorhandler(405)
def handle_error(error):
    title = ERROR_TITLES.get(error.code, "Lỗi hệ thống")
    description = getattr(error, 'description', str(error))
    
    if request.path.startswith("/api/"):
        return {"error": title, "detail": description}, error.code
        
    body = f"<h2>Lỗi {error.code}: {escape(title)}</h2><p>{escape(description)}</p>"
    return layout(title, body), error.code