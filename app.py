import streamlit as st
import pandas as pd
from io import BytesIO
from datetime import date
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Pt
from docx.oxml.ns import qn

# -------------------- Data helpers --------------------
def make_course(name: str, code: str, cfu: int = 6, dept: str = "DIETI", year: str = "Second", semester: str = "Second"):
    return {
        "name": name,
        "code": code,
        "cfu": int(cfu),
        "dept": dept,
        "year": year,
        "semester": semester,
    }

def course_label(c):
    return f"{c['name']} ({c['code']}, {c['cfu']} CFU)"

# Fixed second-year components (now like normal courses)
FIXED_COMPONENTS = [
    make_course("Internship-Stage or Project", "U7901", 8),
    make_course("Thesis and Final Exam", "U7902", 16),
    make_course("Other activities", "U7903", 6),
]

# -------------------- Document helpers --------------------
def academic_year_to_aa_format(academic_year: str) -> str:
    """Convert '2025-2026' -> '2025/26'. If already like '2025/26', return as-is."""
    if "-" in academic_year:
        try:
            y1, y2 = academic_year.split("-")
            return f"{y1}/{str(int(y2)%100).zfill(2)}"
        except Exception:
            return academic_year
    return academic_year


def build_study_plan_docx(
    name: str,
    matricula: str,
    pob: str,
    dob_str: str,
    phone: str,
    email: str,
    academic_year: str,
    year_of_degree: str,
    degree_type: str,
    degree_name: str,
    main_path: str,
    sub_path: str,
    courses: list,
) -> BytesIO:
    doc = Document()

    # ---- Global font: Times New Roman 12 pt ----
    normal = doc.styles["Normal"]
    normal.font.name = "Times New Roman"
    normal.font.size = Pt(12)
    try:
        normal._element.rPr.rFonts.set(qn('w:eastAsia'), 'Times New Roman')
    except Exception:
        pass

    # Header block (centered & bold)
    header_lines = [
        "Università degli Studi di Napoli Federico II",
        "Corso di Studio",
        f"Laurea Magistrale in {degree_name}",
        "Piano di Studi",
        f"A.A {academic_year_to_aa_format(academic_year)}",
    ]
    for line in header_lines:
        p = doc.add_paragraph()
        run = p.add_run(line)
        run.bold = True
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER

    # Indirizzo (sub path) and coordinator line
    doc.add_paragraph(f"Indirizzo: {sub_path}")
    doc.add_paragraph("Da consegnare al Coordinatore del Corso, Prof. Giuseppe Longo")
    doc.add_paragraph("")

    # Body text (anagraphica)
    doc.add_paragraph(
        f"Il/La sottoscritto/a {name}, matr. {matricula}, nato/a a {pob} il {dob_str}, cell. {phone}, e-mail {email}"
    )

    doc.add_paragraph(
        f"iscritto/a nell’A.A. {academic_year_to_aa_format(academic_year)} al {year_of_degree} anno del Corso di {degree_type} in {degree_name}, "
        "chiede alla Commissione di Coordinamento Didattico del Corso di Studio l’approvazione del presente Piano di Studio (PdS)."
    )

    doc.add_paragraph("")

    # Table (6 columns x 8 rows: 1 header + 7 items)
    table = doc.add_table(rows=8, cols=6)
    # visible borders like "All Borders"
    table.style = 'Table Grid'
    hdr = table.rows[0].cells
    hdr[0].text = "Insegnamento"
    hdr[1].text = "Corso Di Laurea Da Cui È Offerto"
    hdr[2].text = "Codice Insegnamento"
    hdr[3].text = "CFU"
    hdr[4].text = "Anno"
    hdr[5].text = "Semestre"

    # Fill rows with: 2 curricular + 2 free + 3 fixed = 7 rows
    for i, c in enumerate(courses[:7], start=1):
        row = table.rows[i].cells
        row[0].text = c["name"]
        row[1].text = c["dept"]
        row[2].text = c["code"]
        row[3].text = str(c["cfu"])
        row[4].text = str(c["year"])
        row[5].text = str(c["semester"])

    doc.add_paragraph("")

    # Modalità di compilazione
    p = doc.add_paragraph()
    r = p.add_run("Modalità di compilazione:")
    r.bold = True
    bullets = [
        "Si possono includere nel PdS sia insegnamenti consigliati dal Corso di Studio (elencati e di immediata approvazione) sia insegnamenti offerti presso l’Ateneo (riportare nome insegnamento, codice esame, Corso di Studio) purchè costituiscano un percorso didattico complementare, coerente con il Corso di Studio",
        "É ammesso il superamento del numero dei CFU previsti",
    ]
    for b in bullets:
        doc.add_paragraph(b, style="List Bullet")

    doc.add_paragraph("")
    today_str = date.today().strftime("%d/%m/%Y")
    doc.add_paragraph(f"Napoli ({today_str})")
    doc.add_paragraph("firma dello studente")

    # Save to buffer
    buf = BytesIO()
    doc.save(buf)
    buf.seek(0)
    return buf


def main():
    st.set_page_config(page_title="Master's Study Plan", page_icon="🎓", layout="wide")
    st.markdown(
        """
        <style>
            .title {text-align: center; color: #4CAF50;}
            .sidebar .sidebar-content {background-color: #f0f2f6;}
            .stButton>button {background-color: #4CAF50; color: white; border-radius: 8px;}
            .stDownloadButton>button {background-color: #008CBA; color: white; border-radius: 8px;}
            .card {padding: 1rem; border-radius: 12px; background: #ffffff; box-shadow: 0 2px 10px rgba(0,0,0,0.06);}            
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.title("🎓 Master's Study Plan Generator")

    # -------------------- Auth --------------------
    teacher_logged_in = False
    with st.sidebar:
        st.subheader("🔑 Teacher Login")
        teacher_id = st.text_input("Enter ID:", type="password")
        teacher_pass = st.text_input("Enter Password:", type="password")
        if teacher_id == "Professor@unina.it" and teacher_pass == "ISPD03":
            teacher_logged_in = True
            st.success("✅ Logged in successfully!")

    # -------------------- Predefined catalog --------------------
    if "catalog" not in st.session_state:
        st.session_state.catalog = {
            "Data Science for Information Technologies": {
                "STATISTICS AND ROBOTICS FOR HEALTH": [
                    make_course("Advanced Statistical Learning and modeling mod A & B", "U7001", 12),
                    make_course("Robotics from Bio-Engineering", "U7002", 6),
                ],
                "DATA SCIENCE FOR SIGNAL AND VIDEO PROCESSING": [
                    make_course("Information Theory and Signal Processing", "U7101", 12),
                    make_course("Image and Video Processing for Autonomous driving", "U7102", 6),
                ],
                "DATA SCIENCE FOR DATA SECURITY": [
                    make_course("Data security and computer forensic", "U7201", 12),
                    make_course("Algorithm design", "U7202", 6),
                ],
                "DATA SCIENCE FOR INDUSTRIAL APPLICATIONS": [
                    make_course("Advanced Statistical Learning and modeling mod A & B", "U7301", 12),
                    make_course("Statistical methods for industrial process monitoring", "U7302", 6),
                ],
                "DATA SCIENCE FOR TEXT AND SPEECH PROCESSING": [
                    make_course("Multimedia Information Retrieval & Text Mining", "U7401", 12),
                    make_course("Natural language processing", "U7402", 6),
                ],
            },
            "Data Science for Public Administration, Economics and Management": {
                "Data Science for Public Administration, Economics and Management": [
                    make_course("Computational Statistics and Generalized Linear Models", "U7501", 12),
                    make_course("Introduction to Economy and Econometrics", "U7502", 6),
                ]
            },
            "Data Science for Fundamental Sciences": {
                "Mathematical Methodologies": [
                    make_course("Algorithms and Parallel Computing-Computational Complexity", "U7701", 12),
                    make_course("Operational Research", "U7702", 6),
                ],
                "Data science for hard sciences": [
                    make_course("Machine Learning for Physics-Astroinformatics", "U7703", 12),
                    make_course("Computational Methods for Physics", "U7704", 6),
                ],
                "Data Science for Life Sciences": [
                    make_course("Biochemistry and Computational Biochemistry", "U7705", 12),
                    make_course("Biologia Computazionale e Statistica", "U7706", 6),
                ],
            },
            "Data Science for Intelligent Systems": {
                "Data Science for Intelligent Systems": [
                    make_course("Computational Intelligence and Machine Learning for Physics", "U7801", 12),
                    make_course("Computational Neurosciences", "U7802", 6),
                ]
            },
        }

    if "specializations" in st.session_state and isinstance(st.session_state["specializations"], dict):
        it = st.session_state.catalog.get("Data Science for Information Technologies", {})
        it.update(st.session_state.specializations)
        st.session_state.catalog["Data Science for Information Technologies"] = it
        del st.session_state["specializations"]

    if "free_choice_courses" not in st.session_state:
        base_free = [
            make_course("Methods for Artificial Intelligence", "U7601", 6),
            make_course("Human robot interaction", "U7602", 6),
            make_course("Biometric Systems", "U7603", 6),
            make_course("Computer graphics", "U7604", 6),
            make_course("Algebraic methods for cryptography", "U7605", 6),
            make_course("Environmental risk monitoring and evaluation", "U7606", 6),
            make_course("Advanced non linear methods for industrial signal processing", "U7607", 6),
            make_course("Techniques of Text analysis and Computational Linguistic", "U7608", 6),
            make_course("Speech processing", "U7609", 6),
        ]
        extra_names_codes = [
            ("Statistical Methods for Evaluation", "U8001"),
            ("Mathematics for Economics and Finance", "U8002"),
            ("SW and methods for statistical analysis of economic data", "U8003"),
            ("Preference Learning", "U8004"),
            ("x-Informatics", "U8005"),
            ("AI and Quantum Computing", "U8006"),
            ("Real and Functional Analysis", "U8007"),
            ("Signal Theory", "U8008"),
            ("Information Theory", "U8009"),
            ("Probability Theory", "U8010"),
            ("Astroinformatics", "U8011"),
            ("Computational Thermodynamics", "U8012"),
            ("Quantum Computing Systems", "U8013"),
            ("Mathematical Physics Models", "U8014"),
            ("Fisica Medica", "U8015"),
            ("Metodologie per l’analisi delle immagini", "U8016"),
            ("Foundation of Robotics", "U8017"),
            ("Machine Learning and Big Data per la salute", "U8018"),
            ("Computational Chemistry", "U8019"),
            ("Artificial Intelligence and Quantum Computing", "U8020"),
            ("Machine Learning for Physics", "U8021"),
        ]
        names_set = {c["name"] for c in base_free}
        for nm, code in extra_names_codes:
            if nm not in names_set:
                base_free.append(make_course(nm, code, 6))
                names_set.add(nm)
        st.session_state.free_choice_courses = base_free

    recommended_by_path = {
        "Data Science for Information Technologies": {
            "STATISTICS AND ROBOTICS FOR HEALTH": [
                "Methods for Artificial Intelligence",
                "Human robot interaction",
            ],
            "DATA SCIENCE FOR SIGNAL AND VIDEO PROCESSING": [
                "Biometric Systems",
                "Computer graphics",
            ],
            "DATA SCIENCE FOR DATA SECURITY": [
                "Algebraic methods for cryptography",
                "Free Choice (6 CFU)",
            ],
            "DATA SCIENCE FOR INDUSTRIAL APPLICATIONS": [
                "Environmental risk monitoring and evaluation",
                "Advanced non linear methods for industrial signal processing",
            ],
            "DATA SCIENCE FOR TEXT AND SPEECH PROCESSING": [
                "Techniques of Text analysis and Computational Linguistic",
                "Speech processing",
            ],
        },
        "Data Science for Public Administration, Economics and Management": {
            "Data Science for Public Administration, Economics and Management": [
                "Statistical Methods for Evaluation",
                "Mathematics for Economics and Finance",
                "SW and methods for statistical analysis of economic data",
                "Preference Learning",
            ]
        },
        "Data Science for Fundamental Sciences": {
            "Mathematical Methodologies": [
                "x-Informatics",
                "AI and Quantum Computing",
                "Real and Functional Analysis",
                "Signal Theory",
                "Information Theory",
                "Probability Theory",
            ],
            "Data science for hard sciences": [
                "Astroinformatics",
                "AI and Quantum Computing",
                "Computational Thermodynamics",
                "Quantum Computing Systems",
                "Mathematical Physics Models",
            ],
            "Data Science for Life Sciences": [
                "Fisica Medica",
                "Metodologie per l’analisi delle immagini",
                "Foundation of Robotics",
                "Machine Learning and Big Data per la salute",
                "Computational Chemistry",
            ],
        },
        "Data Science for Intelligent Systems": {
            "Data Science for Intelligent Systems": [
                "Astroinformatics",
                "Quantum Computing Systems",
                "Artificial Intelligence and Quantum Computing",
                "Machine Learning for Physics",
            ]
        },
    }

    # -------------------- Catalog overview --------------------
    with st.expander("📚 Catalog Overview (Codes, CFUs, Dept, Year, Semester)"):
        rows = []
        for main_path, subpaths in st.session_state.catalog.items():
            for sub_path, courses in subpaths.items():
                for idx, c in enumerate(courses, start=1):
                    rows.append({
                        "Type": "Curricular",
                        "Main Path": main_path,
                        "Sub Path": sub_path,
                        "Slot": f"Curricular {idx}",
                        "Course": c["name"],
                        "Code": c["code"],
                        "CFU": c["cfu"],
                        "Dept": c["dept"],
                        "Year": c["year"],
                        "Semester": c["semester"],
                    })
        for c in st.session_state.free_choice_courses:
            rows.append({
                "Type": "Free Choice",
                "Main Path": "—",
                "Sub Path": "—",
                "Slot": "—",
                "Course": c["name"],
                "Code": c["code"],
                "CFU": c["cfu"],
                "Dept": c["dept"],
                "Year": c["year"],
                "Semester": c["semester"],
            })
        for c in FIXED_COMPONENTS:
            rows.append({
                "Type": "Fixed",
                "Main Path": "—",
                "Sub Path": "—",
                "Slot": "—",
                "Course": c["name"],
                "Code": c["code"],
                "CFU": c["cfu"],
                "Dept": c["dept"],
                "Year": c["year"],
                "Semester": c["semester"],
            })
        df = pd.DataFrame(rows)
        st.dataframe(df, use_container_width=True)

    # -------------------- Teacher tools --------------------
    if teacher_logged_in:
        with st.expander("👨‍🏫 Teacher: Add Main/Sub Path & Courses"):
            all_main_paths = list(st.session_state.catalog.keys()) + ["➕ Create new main path…"]
            choice = st.selectbox("Select Main Path or create new:", all_main_paths, index=0, placeholder="Type to search…")
            new_main = None
            if choice == "➕ Create new main path…":
                new_main = st.text_input("New Main Path Name")
            main_selected = new_main if new_main else choice

            sub_path = st.text_input("Sub Path Name")
            st.markdown("Defaults reflect program rules: Curricular I = 12 CFU, Curricular II = 6 CFU; Dept/Year/Sem default to DIETI/Second/Second")
            with st.form("add_spec_form"):
                col1, col2 = st.columns(2)
                with col1:
                    c1_name = st.text_input("Curricular Course I Name", key="c1n")
                    c1_code = st.text_input("Course I Code", value="U7XXX", key="c1c")
                    c1_cfu = st.number_input("Course I CFU", min_value=1, max_value=30, value=12, key="c1f")
                    c1_dept = st.text_input("Course I Department", value="DIETI", key="c1d")
                    c1_year = st.selectbox("Course I Year", ["First", "Second"], index=1, key="c1y")
                    c1_sem = st.selectbox("Course I Semester", ["First", "Second"], index=1, key="c1s")
                with col2:
                    c2_name = st.text_input("Curricular Course II Name", key="c2n")
                    c2_code = st.text_input("Course II Code", value="U7YYY", key="c2c")
                    c2_cfu = st.number_input("Course II CFU", min_value=1, max_value=30, value=6, key="c2f")
                    c2_dept = st.text_input("Course II Department", value="DIETI", key="c2d")
                    c2_year = st.selectbox("Course II Year", ["First", "Second"], index=1, key="c2y")
                    c2_sem = st.selectbox("Course II Semester", ["First", "Second"], index=1, key="c2s")
                submitted = st.form_submit_button("➕ Add / Update Sub Path")
            if submitted:
                if main_selected and sub_path and c1_name and c2_name and c1_code and c2_code:
                    if main_selected not in st.session_state.catalog:
                        st.session_state.catalog[main_selected] = {}
                    st.session_state.catalog[main_selected][sub_path] = [
                        make_course(c1_name, c1_code, c1_cfu, c1_dept, c1_year, c1_sem),
                        make_course(c2_name, c2_code, c2_cfu, c2_dept, c2_year, c2_sem),
                    ]
                    st.success(f"✅ Saved sub path '{sub_path}' under main path '{main_selected}'.")
                else:
                    st.error("⚠ Please fill all required fields (names & codes).")

            st.markdown("Add a free choice course (defaults: DIETI / Second / Second; recommended CFU = 6):")
            with st.form("add_free_form"):
                f_name = st.text_input("Free Choice Course Name")
                f_code = st.text_input("Course Code", value="U8ZZZ")
                f_cfu = st.number_input("CFU", min_value=1, max_value=30, value=6)
                f_dept = st.text_input("Department", value="DIETI")
                f_year = st.selectbox("Year", ["First", "Second"], index=1, key="fy")
                f_sem = st.selectbox("Semester", ["First", "Second"], index=1, key="fs")
                submitted_free = st.form_submit_button("➕ Add Free Choice Course")
            if submitted_free:
                if f_name and f_code:
                    if all(fc["name"] != f_name for fc in st.session_state.free_choice_courses):
                        st.session_state.free_choice_courses.append(make_course(f_name, f_code, f_cfu, f_dept, f_year, f_sem))
                        st.success(f"✅ Course '{f_name}' added!")
                    else:
                        st.warning("A free choice course with this name already exists.")
                else:
                    st.error("⚠ Please enter a course name and code.")

    # -------------------- Student workflow --------------------
    with st.expander("🎓 Student: Select Your Study Plan", expanded=True):
        # --- Student personal details ---
        st.markdown("#### 🧑‍🎓 Student Details")
        ca, cb, cc = st.columns(3)
        with ca:
            name = st.text_input("Name")
            pob = st.text_input("Place of Birth")
            phone = st.text_input("Phone Number")
        with cb:
            matricula = st.text_input("Matricula")
            dob = st.date_input("Date of Birth")
            email = st.text_input("Institutional Email")
        with cc:
            # Academic year helper options
            today = date.today()
            start_year = today.year if today.month >= 7 else today.year - 1
            acad_options = [f"{start_year-1}-{start_year}", f"{start_year}-{start_year+1}", f"{start_year+1}-{start_year+2}"]
            academic_year = st.selectbox("Academic Year", acad_options, index=1)
            year_of_degree = st.selectbox("Year of Degree", ["First", "Second"], index=1)
            degree_type = st.text_input("Degree Type", value="LAUREA MAGISTRALE")
            degree_name = st.text_input("Degree Name", value="DATA SCIENCE")

        st.markdown("---")

        main_paths = ["Select Main Path"] + list(st.session_state.catalog.keys())
        main_choice = st.selectbox(
            "🧭 Choose Main Path:",
            main_paths,
            index=0,
            placeholder="Type to search main paths…",
            help="Start typing to quickly search.",
        )

        if main_choice != "Select Main Path":
            sub_paths = ["Select Sub Path"] + list(st.session_state.catalog[main_choice].keys())
            sub_choice = st.selectbox(
                "📂 Choose Sub Path:",
                sub_paths,
                index=0,
                placeholder="Type to search sub paths…",
                help="Start typing to quickly search.",
            )
        else:
            sub_choice = "Select Sub Path"

        if main_choice != "Select Main Path" and sub_choice != "Select Sub Path":
            st.write("### 📚 Your Curricular Courses:")
            curr_courses = st.session_state.catalog[main_choice][sub_choice]
            for idx, c in enumerate(curr_courses, start=1):
                st.markdown(
                    f"- **Curricular {idx}: {c['name']}** — `{c['code']}` • **{c['cfu']} CFU** • {c['dept']} • Year: {c['year']} • Semester: {c['semester']}"
                )

            recs = recommended_by_path.get(main_choice, {}).get(sub_choice, [])
            if recs:
                st.info("**Recommended free choice exams for this sub path:**\n- " + "\n- ".join(recs))

            st.write("### 🎯 Select 2 Free Choice Courses:")
            free_labels = [course_label(c) for c in st.session_state.free_choice_courses]
            free_choice_selection_labels = st.multiselect(
                "Choose Free Courses (each 6 CFU):",
                free_labels,
                max_selections=2,
                placeholder="Type to search free-choice courses…",
                help="Start typing to search; select exactly 2.",
            )
            selected_free = [
                c for c in st.session_state.free_choice_courses if course_label(c) in free_choice_selection_labels
            ]

            fixed_total = sum(x["cfu"] for x in FIXED_COMPONENTS)
            curricular_total = sum(c["cfu"] for c in curr_courses)
            free_total = sum(c["cfu"] for c in selected_free)
            current_total = fixed_total + curricular_total + free_total

            st.caption(
                f"Planned CFUs so far: Curricular **{curricular_total}**, Free-choice **{free_total}**, Fixed components **{fixed_total}** → **{current_total}/60 CFU**"
            )

            if any(c["cfu"] != 6 for c in selected_free):
                st.warning("One or more selected free-choice courses are not 6 CFU. Program rule expects 2×6 CFU.")

            if len(selected_free) == 2 and st.button("📄 Generate Word (DOCX)"):
                dob_str = dob.strftime("%d/%m/%Y") if hasattr(dob, 'strftime') else str(dob)
                ordered_courses = [
                    curr_courses[0],
                    curr_courses[1],
                    selected_free[0],
                    selected_free[1],
                    FIXED_COMPONENTS[0],
                    FIXED_COMPONENTS[1],
                    FIXED_COMPONENTS[2],
                ]
                buf = build_study_plan_docx(
                    name=name,
                    matricula=matricula,
                    pob=pob,
                    dob_str=dob_str,
                    phone=phone,
                    email=email,
                    academic_year=academic_year,
                    year_of_degree=year_of_degree,
                    degree_type=degree_type,
                    degree_name=degree_name,
                    main_path=main_choice,
                    sub_path=sub_choice,
                    courses=ordered_courses,
                )
                fname = f"Piano_di_Studi_{matricula or 'studente'}.docx"
                st.download_button("⬇ Download Word Document", data=buf, file_name=fname, mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
            elif len(free_choice_selection_labels) != 2:
                st.warning("⚠ Please select exactly 2 free choice courses (6 CFU each).")


if __name__ == "__main__":
    main()
