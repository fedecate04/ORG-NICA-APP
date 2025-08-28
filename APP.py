 # APP.py
# -*- coding: utf-8 -*-
import io, os, json, time, tempfile, unicodedata, re
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit, quote, urlparse, parse_qs
import streamlit as st

# ================== CONFIG BÁSICA ==================
st.set_page_config(page_title="Química Orgánica", page_icon="🧪", layout="wide")

TITULO   = "QUÍMICA ORGÁNICA"
PROFESOR = "Profesor: Israel Funes"
ALUMNOS  = "Alumnos: Carrasco Federico & Catereniuc Federico"

# Temas (lista completa para el sidebar y la app)
TEMAS = [
    "Conceptos básicos","Nomenclatura","Isomería","Alcanos",
    "Halogenuros de alquilo","Alquenos","Alquinos","Aromáticos",
    "Alcoholes","Éteres","Fenoles","Aldehídos","Cetonas",
    "Ácidos carboxílicos","Heteroátomos","PAHs","Carbohidratos",
    "Aminoácidos","Lípidos y proteínas",
]
# División para acceso rápido en 2 filas
TEMAS_BASE = [
    "Conceptos básicos","Nomenclatura","Isomería","Alcanos",
    "Halogenuros de alquilo","Alquenos","Alquinos","Aromáticos",
    "Alcoholes","Éteres","Fenoles","Aldehídos","Cetonas",
    "Ácidos carboxílicos",
]
TEMAS_ESPECIALES = [
    "Heteroátomos","PAHs","Carbohidratos","Aminoácidos","Lípidos y proteínas",
]

# ===== Límites de carga (ajusta si lo necesitás) =====
MAX_UPLOAD_MB = 50
def too_big(uploaded_file) -> bool:
    return getattr(uploaded_file, "size", 0) > MAX_UPLOAD_MB * 1024 * 1024
def human_mb(nbytes: int) -> str:
    return f"{nbytes/1024/1024:.1f} MB"

# === Secrets (cargalas en Streamlit Secrets) ===
SUPABASE_URL    = st.secrets["SUPABASE_URL"]
SUPABASE_KEY    = st.secrets["SUPABASE_KEY"]          # service_role
SUPABASE_BUCKET = st.secrets.get("SUPABASE_BUCKET", "utn")
COURSE_ROOT     = st.secrets.get("COURSE_ROOT", "Quimica_Organica")
PASSCODE        = st.secrets.get("PASSCODE", "FFCC")

# ================== ESTILO (UTN compacto y claro) ==================
st.markdown(f"""
<style>
:root{{
  --bg:#f7f7fb;
  --panel:#ffffff;
  --soft:#f1f3f9;
  --text:#0b1221;
  --muted:#5b6579;
  --accent:#1f2a44;
  --accent-2:#2e5aac;
  --border:#e6e8f0;
  --radius:10px;
  --radius-lg:12px;
}}

html, body, .stApp {{ background: var(--bg); color: var(--text); }}
.block-container {{ padding-top:.6rem; padding-bottom:.8rem; max-width:1180px; }}

[data-testid="stSidebar"] {{
  background: var(--panel);
  border-right: 1px solid var(--border);
}}

h1,h2,h3,h4 {{ color: var(--text) !important; letter-spacing:.1px; }}
p, span, label, .stMarkdown, .stTextInput label {{ color: var(--text) !important; }}
.small, .caption {{ color: var(--muted) !important; }}

hr, .stMarkdown hr {{ border: none; height:1px; background: linear-gradient(90deg, transparent, var(--border), transparent); }}

/* ====== Encabezado nuevo ====== */
.header-wrap {{
  display:grid; grid-template-columns: 1fr 320px; gap:16px; align-items:center;
  margin: 6px 0 8px 0;
}}
.header-left {{ text-align:center; }}
.header-logo img {{ max-width: 520px; width: 100%; height:auto; margin:0 auto; display:block; }}
.header-uni   {{ margin-top:.6rem; font-weight:800; font-size:1.6rem; letter-spacing:.3px; }}
.header-fac   {{ margin-top:.15rem; font-weight:700; font-size:1.15rem; color:#24324d; }}
.header-cat   {{ margin-top:.8rem; font-weight:800; font-size:1.9rem; color: var(--accent-2); }}
.header-meta  {{
  background:#fff; border:1px solid var(--border); border-radius:var(--radius-lg);
  padding:.7rem .9rem; font-size:.95rem;
}}
.header-meta strong {{ font-weight:700; }}
@media (max-width: 900px) {{
  .header-wrap {{ grid-template-columns: 1fr; }}
  .header-meta {{ justify-self:center; width: min(360px, 100%); }}
  .header-logo img {{ max-width: 420px; }}
}}

/* Línea fina separadora */
.thin-sep {{ height:1px; background:var(--border); margin:10px 0 6px 0; }}

/* ---- Botón editar sutil ---- */
.edit-inline button {{
  background:#ffffff; color:#1f2a44; border:1px solid var(--border);
  border-radius:8px; padding:.28rem .6rem; font-weight:600;
}}
.edit-inline button:hover {{ background:#f4f6fb; border-color:#cfd7ea; }}

/* ---- Card compacta ---- */
.card {{
  background: var(--panel);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  padding: 12px 14px;
  box-shadow: 0 1px 2px rgba(15,23,42,.05);
}}

/* Tabs sobrios */
div[role="tablist"] {{ gap:.35rem; border-top:1px solid var(--border); padding-top:.35rem; }}
div[role="tablist"] button {{
  background: #fafbff !important;
  color: var(--muted) !important;
  border: 1px solid var(--border) !important;
  border-radius: var(--radius) !important;
  padding: .35rem .7rem !important;
  font-size: .95rem !important;
}}
div[role="tablist"] button[aria-selected="true"]{{
  color: var(--text) !important;
  background: #ffffff !important;
  border-color: var(--accent-2) !important;
  box-shadow: 0 0 0 2px rgba(46,90,172,.10);
}}

/* Botones */
.stButton>button, .stDownloadButton>button {{
  background: var(--accent);
  color: #ffffff;
  border: 1px solid #182238;
  border-radius: var(--radius);
  padding: .42rem .8rem;
  transition: background .12s ease, transform .04s ease;
  font-weight: 600;
}}
.stButton>button:hover, .stDownloadButton>button:hover {{ background: var(--accent-2); }}
.stButton>button:active {{ transform: translateY(1px); }}

/* Inputs compactos */
.stTextInput>div>div>input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] {{
  background: #ffffff !important; color: var(--text) !important;
  border: 1px solid var(--border) !important; border-radius: var(--radius) !important;
  padding:.45rem .6rem !important;
}}
.stTextInput>div>div>input:focus, .stTextArea textarea:focus {{
  border-color: var(--accent-2) !important; box-shadow: 0 0 0 2px rgba(46,90,172,.12);
}}

/* Chips / Temas: BLANCOS + hover claro */
.chipbar {{ margin-top:.2rem; }}
.chipbar .title {{ font-weight:800; margin:.1rem 0 .35rem 0; color:#1f2a44; }}
.chipgrid {{
  display:grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 10px;
}}
.chipgrid .chipbtn {{
  width: 100%; background:#ffffff; color:#111827;
  border: 1px solid var(--border); padding: .48rem .66rem;
  font-size: .96rem; border-radius: 16px; text-align:center;
}}
.chipgrid .chipbtn:hover {{ background:#f5f7ff; border-color:#cfd7ea; }}

/* Filas de recursos compactas */
.res-row {{
  display:flex; align-items:center; gap:10px;
  padding:.45rem .55rem; border:1px solid var(--border);
  border-radius: var(--radius); background:#fff; margin-bottom:6px;
}}
.res-row:hover {{ background:#fafbff; }}
.res-title {{ font-weight:600; }}
.res-meta {{ color:var(--muted); font-size:.9rem; }}
.res-actions a {{ margin-left:10px; }}
</style>
""", unsafe_allow_html=True)

# ================== SUPABASE CLIENT ==================
from supabase import create_client, Client
try:
    from storage3.exceptions import StorageApiError
except Exception:
    class StorageApiError(Exception):
        pass
import storage3

supa: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ---------- Diagnóstico rápido ----------
with st.expander("🛠️ Diagnóstico Supabase", expanded=False):
    st.write("Bucket configurado:", SUPABASE_BUCKET)
    st.write("URL:", SUPABASE_URL)
    try:
        buckets = supa.storage.list_buckets()
        st.success(f"Buckets visibles: {[b['name'] for b in buckets]}")
    except Exception as e:
        st.error("No pude listar buckets (¿SUPABASE_KEY no es service_role?).")
        st.code(repr(e))
    try:
        root_list = supa.storage.from_(SUPABASE_BUCKET).list("")
        st.write(f"Objetos en raíz del bucket '{SUPABASE_BUCKET}': {len(root_list)}")
    except Exception as e:
        st.error("Error listando raíz del bucket (¿nombre mal escrito o bucket inexistente?).")
        st.code(repr(e))
    import storage3 as _s3, supabase as _sb
    st.caption(f"supabase-py: {getattr(_sb, '__version__', 'unknown')} | storage3: {getattr(_s3, '__version__', 'unknown')}")

# ================== HELPERS ==================
def safe_folder(name: str) -> str:
    s = unicodedata.normalize("NFKD", name).encode("ascii","ignore").decode("ascii")
    s = s.lower().replace(" ", "_")
    s = re.sub(r"[^a-z0-9\-_]", "", s)
    return s

def safe_filename(name: str) -> str:
    s = unicodedata.normalize("NFKD", name).encode("ascii","ignore").decode("ascii")
    s = s.strip().replace(" ", "_")
    return re.sub(r"[^\w\.\-]", "_", s)

def topic_prefix(tema: str) -> str:
    return f"{COURSE_ROOT}/{safe_folder(tema)}"

def bucket_join(*parts) -> str:
    return "/".join(p.strip("/").replace("//","/") for p in parts)

def _encode_url(u: str) -> str:
    parts = urlsplit(u)
    path = quote(parts.path)
    return urlunsplit((parts.scheme, parts.netloc, path, parts.query, parts.fragment))

def storage_list(folder_path: str):
    try:
        return supa.storage.from_(SUPABASE_BUCKET).list(folder_path) or []
    except Exception:
        return []

def should_embed(url: str) -> bool:
    host = urlparse(url).netloc.lower()
    if "youtube.com" in host or "youtu.be" in host or "vimeo.com" in host:
        return True
    return "drive.google.com" in host and "/preview" in url

def drive_preview_url(url: str) -> str:
    u = urlparse(url)
    if "drive.google.com" not in u.netloc.lower():
        return url
    if "/file/d/" in u.path:
        try:
            file_id = u.path.split("/file/d/")[1].split("/")[0]
            return f"https://drive.google.com/file/d/{file_id}/preview"
        except Exception:
            return url
    qs = parse_qs(u.query)
    if "id" in qs and qs["id"]:
        file_id = qs["id"][0]
        return f"https://drive.google.com/file/d/{file_id}/preview"
    return url

def storage_upload(dst_path: str, data_bytes: bytes, content_type: str):
    dst_path = re.sub(r"[^\w\-/\.]", "_", dst_path)
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(data_bytes); tmp.flush()
        tmp_path = tmp.name
    try:
        try:
            return supa.storage.from_(SUPABASE_BUCKET).upload(
                dst_path, tmp_path,
                {"content-type": str(content_type), "cache-control": "3600", "x-upsert": "true"},
            )
        except (StorageApiError, storage3.utils.StorageException, Exception) as e:
            try:
                info = (e.args or [{}])[0]
                status = info.get("statusCode"); msg = info.get("message") or info.get("error") or info
                st.warning(f"Upload falló (status={{status}}). Intento update(). Detalle: {{msg}}")
            except Exception:
                st.warning(f"Upload falló. Intento update(). Detalle: {{repr(e)}}")
            try:
                return supa.storage.from_(SUPABASE_BUCKET).update(
                    dst_path, tmp_path,
                    {"content-type": str(content_type), "cache-control": "3600"},
                )
            except (StorageApiError, storage3.utils.StorageException, Exception) as e2:
                try:
                    info2 = (e2.args or [{}])[0]
                    status2 = info2.get("statusCode")
                    msg2 = info2.get("message") or info2.get("error") or info2
                    st.error(f"Update también falló (status={{status2}}).")
                    st.code(json.dumps(info2, ensure_ascii=False, indent=2))
                except Exception:
                    st.error("Update también falló."); st.code(repr(e2))
                raise
    finally:
        try: os.remove(tmp_path)
        except Exception: pass

def storage_download(src_path: str) -> bytes | None:
    try:
        return supa.storage.from_(SUPABASE_BUCKET).download(src_path)
    except Exception:
        return None

def storage_remove(paths: list[str]):
    try:
        return supa.storage.from_(SUPABASE_BUCKET).remove(paths)
    except Exception as e:
        return {"error": str(e)}

def public_url(path: str) -> str | None:
    try:
        res = supa.storage.from_(SUPABASE_BUCKET).get_public_url(path)
        if isinstance(res, dict):
            return res.get("publicURL") or res.get("publicUrl") or res.get("data", {}).get("publicUrl")
        return str(res)
    except Exception:
        return None

def read_meta(tema: str) -> dict:
    p = bucket_join(topic_prefix(tema), "meta.json")
    raw = storage_download(p)
    if not raw:
        return {}
    try:
        return json.loads(raw.decode("utf-8"))
    except Exception:
        return {}

def write_meta(tema: str, meta: dict):
    p = bucket_join(topic_prefix(tema), "meta.json")
    storage_upload(p, json.dumps(meta, ensure_ascii=False, indent=2).encode("utf-8"),
                   content_type="application/json")

def get_title(meta, bucket, filename):
    return meta.get("titles", {}).get(bucket, {}).get(filename, "")

def set_title(meta, bucket, filename, title):
    meta.setdefault("titles", {}).setdefault(bucket, {})
    if title.strip():
        meta["titles"][bucket][filename] = title.strip()
    else:
        meta["titles"][bucket].pop(filename, None)

def add_link(meta, titulo, url):
    meta.setdefault("video_links", []).append({"titulo": titulo.strip() or "Video", "url": url.strip()})

def delete_link(meta, idx):
    try:
        meta.setdefault("video_links", []).pop(idx)
    except Exception:
        pass

# ================== ENCABEZADO NUEVO ==================
col = st.container()
with col:
    st.markdown('<div class="header-wrap">', unsafe_allow_html=True)

    # Columna principal (logo + textos centrales)
    left = st.container()
    with left:
        st.markdown('<div class="header-left">', unsafe_allow_html=True)
        # Logo grande centrado
        if Path("logoutn.png").exists():
            st.markdown('<div class="header-logo">', unsafe_allow_html=True)
            st.image("logoutn.png", use_container_width=False)
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.info("Subí **logoutn.png** a la raíz del repo para ver el logo aquí.")

        # Textos institucionales centrados y separados
        st.markdown(f"""
        <div class="header-uni">UNIVERSIDAD TECNOLÓGICA NACIONAL</div>
        <div class="header-fac">FACULTAD REGIONAL DEL NEUQUÉN</div>
        <div class="header-cat">{TITULO}</div>
        """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # Columna lateral (profesor y alumnos)
    right = st.container()
    with right:
        st.markdown(f"""
        <div class="header-meta">
          <div><strong>Profesor:</strong> Israel Funes</div>
          <div><strong>Alumnos:</strong> Carrasco Federico & Catereniuc Federico</div>
          <div class="small" style="margin-top:.3rem;">(Bloque lateral, menor jerarquía)</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)  # cierra header-wrap

# Línea fina separadora
st.markdown('<div class="thin-sep"></div>', unsafe_allow_html=True)

# ================== MODO EDICIÓN (botón sutil) ==================
if "can_edit" not in st.session_state:
    st.session_state["can_edit"] = False
if "ask_pass" not in st.session_state:
    st.session_state["ask_pass"] = False

c1, c2 = st.columns([1,5])
with c1:
    if not st.session_state["can_edit"]:
        with st.container():
            if st.button("🔒 Editar", key="btn_edit", help="Entrar a modo edición", type="secondary"):
                st.session_state["ask_pass"] = True
    else:
        if st.button("✅ Cerrar edición", key="btn_close_edit"):
            st.session_state["can_edit"] = False
            st.session_state["ask_pass"] = False
            st.rerun()

with c2:
    if st.session_state["ask_pass"] and not st.session_state["can_edit"]:
        code = st.text_input("Ingresá el código de edición", type="password", key="pass_input")
        go = st.button("Ingresar")
        if go:
            if (code or "").strip() == PASSCODE:
                st.session_state["can_edit"] = True
                st.success("Modo edición activado.")
                st.session_state["ask_pass"] = False
                st.rerun()
            else:
                st.error("Código incorrecto.")

# (Se eliminaron los expanders informativos, como pediste)

# ====== FAMILIA ORGÁNICA (antes “Acceso rápido…”) ======
if "tema_idx" not in st.session_state:
    st.session_state["tema_idx"] = 0

def chip_row(titulo: str, lista_temas: list, prefix_key: str):
    st.markdown('<div class="chipbar">', unsafe_allow_html=True)
    st.markdown(f'<div class="title">{titulo}</div>', unsafe_allow_html=True)
    st.markdown('<div class="chipgrid">', unsafe_allow_html=True)
    cols = st.columns(6)
    for i, t in enumerate(lista_temas):
        with cols[i % 6]:
            if st.button(t, key=f"{prefix_key}_{t}", use_container_width=True):
                st.session_state["tema_idx"] = TEMAS.index(t)
                st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown("### 🧬 Familia Orgánica")
chip_row("Temas base", TEMAS_BASE, "chip_base")
chip_row("Grupos especiales", TEMAS_ESPECIALES, "chip_esp")

# ================== NAVEGACIÓN (sidebar sincronizada) ==================
st.sidebar.header("Navegación")
tema = st.sidebar.selectbox(
    "Elegí un tema",
    TEMAS,
    index=st.session_state["tema_idx"],
    key="tema_select"
)
st.session_state["tema_idx"] = TEMAS.index(tema)
tema = TEMAS[st.session_state]["tema_idx"] if isinstance(st.session_state.get("tema_idx"), int) else tema

# ================== CONTENIDO DEL TEMA ==================
st.markdown(f"## CONTENIDO DEL TEMA — {tema}")
st.markdown('<div class="card">', unsafe_allow_html=True)

tabs = st.tabs(["📄 PDF Resúmenes", "📘 PDF Apuntes del profesor", "🎥 Videos (MP4 o enlace)", "🎧 Audios (MP3)"])

# -------- UI helper: listado (link + eliminar/renombrar + embed opcional) --------
def bucket_join_safe(*parts) -> str:
    return "/".join(p.strip("/").replace("//","/") for p in parts)

def render_list(bucket_name: str, tema: str, exts: set[str], media: str | None = None):
    can_edit = st.session_state["can_edit"]
    folder = bucket_join_safe(f"{COURSE_ROOT}/{safe_folder(tema)}", bucket_name)
    objs = storage_list(folder)
    if not objs:
        st.info("No hay archivos cargados aún.")
        return

    meta = read_meta(tema)
    st.markdown("#### Archivos cargados")
    for obj in sorted(objs, key=lambda o: o.get("name","").lower()):
        name = obj.get("name","")
        if not any(name.lower().endswith(e) for e in exts):
            continue
        full_path = bucket_join_safe(folder, name)
        url = public_url(full_path)
        title = get_title(meta, bucket_name, name) or name

        with st.container():
            st.markdown(
                f'''
                <div class="res-row">
                  <div style="flex:1 1 auto; min-width:240px;">
                    <div class="res-title">{title}</div>
                    <div class="res-meta">{name}</div>
                  </div>
                  <div class="res-actions">
                    {('<a href="'+_encode_url(url)+'">Abrir / Descargar</a>') if url else ''}
                  </div>
                </div>
                ''', unsafe_allow_html=True
            )
            if url and media == "video":
                st.video(_encode_url(url))
            elif url and media == "audio":
                st.audio(_encode_url(url))

            if can_edit:
                c1, c2 = st.columns([5,1])
                with c1:
                    new_title = st.text_input("Título", value=title if title != name else "",
                                              key=f"ttl_{bucket_name}_{name}")
                with c2:
                    if st.button("🗑️ Eliminar", key=f"del_{bucket_name}_{name}"):
                        storage_remove([full_path])
                        set_title(meta, bucket_name, name, "")
                        write_meta(tema, meta)
                        st.success(f"Eliminado: {name}")
                        st.rerun()
                if new_title != (title if title != name else ""):
                    set_title(meta, bucket_name, name, new_title)
                    write_meta(tema, meta)

# ================== TAB 1: RESÚMENES ==================
with tabs[0]:
    st.subheader(f"Resúmenes — {tema}")
    if st.session_state["can_edit"]:
        c1, c2 = st.columns([2,3])
        with c1:
            up = st.file_uploader("Subir PDF de resumen", type=["pdf"], key=f"res_{tema}")
        with c2:
            titulo_pdf = st.text_input("Título (opcional) para el PDF", key=f"res_title_{tema}")
        if up is not None:
            if too_big(up):
                st.error(f"El archivo ({human_mb(up.size)}) supera {MAX_UPLOAD_MB} MB. Comprimilo o subilo como enlace.")
            else:
                dst = bucket_join_safe(f"{COURSE_ROOT}/{safe_folder(tema)}", "resumenes", f"{int(time.time())}_{safe_filename(up.name)}")
                storage_upload(dst, up.read(), content_type="application/pdf")
                if titulo_pdf.strip():
                    meta = read_meta(tema)
                    set_title(meta, "resumenes", dst.split("/")[-1], titulo_pdf.strip())
                    write_meta(tema, meta)
                st.success(f"Subido: {up.name}")
    render_list("resumenes", tema, exts={".pdf"})

# ================== TAB 2: APUNTES ==================
with tabs[1]:
    st.subheader(f"Apuntes del profesor — {tema}")
    if st.session_state["can_edit"]:
        c1, c2 = st.columns([2,3])
        with c1:
            up = st.file_uploader("Subir PDF de apuntes", type=["pdf"], key=f"apu_{tema}")
        with c2:
            titulo_pdf = st.text_input("Título (opcional) para el PDF", key=f"apu_title_{tema}")
        if up is not None:
            if too_big(up):
                st.error(f"El archivo ({human_mb(up.size)}) supera {MAX_UPLOAD_MB} MB. Comprimilo o subilo como enlace.")
            else:
                dst = bucket_join_safe(f"{COURSE_ROOT}/{safe_folder(tema)}", "apuntes", f"{int(time.time())}_{safe_filename(up.name)}")
                storage_upload(dst, up.read(), content_type="application/pdf")
                if titulo_pdf.strip():
                    meta = read_meta(tema)
                    set_title(meta, "apuntes", dst.split("/")[-1], titulo_pdf.strip())
                    write_meta(tema, meta)
                st.success(f"Subido: {up.name}")
    render_list("apuntes", tema, exts={".pdf"})

# ================== TAB 3: VIDEOS ==================
with tabs[2]:
    st.subheader(f"Videos — {tema}")
    meta = read_meta(tema)

    if st.session_state["can_edit"]:
        c1, c2 = st.columns([2,3])
        with c1:
            up = st.file_uploader("Subir video MP4", type=["mp4"], key=f"vid_{tema}")
        with c2:
            titulo_mp4 = st.text_input("Título (opcional) del video", key=f"vid_title_{tema}")
        if up is not None:
            if too_big(up):
                st.error(f"El video ({human_mb(up.size)}) supera {MAX_UPLOAD_MB} MB. Subilo como enlace (YouTube/Drive/Zoom) o recomprimilo (720p).")
            else:
                dst = bucket_join_safe(f"{COURSE_ROOT}/{safe_folder(tema)}", "videos", f"{int(time.time())}_{safe_filename(up.name)}")
                storage_upload(dst, up.read(), content_type="video/mp4")
                if titulo_mp4.strip():
                    set_title(meta, "videos", dst.split("/")[-1], titulo_mp4.strip())
                    write_meta(tema, meta)
                st.success(f"Subido: {up.name}")

    links = meta.get("video_links", [])
    if st.session_state["can_edit"]:
        st.markdown("##### Agregar enlace (YouTube/Drive/Zoom)")
        url = st.text_input("URL del video", key=f"url_{tema}")
        titulo = st.text_input("Título del video (opcional)", key=f"ttl_{tema}")
        if st.button("Agregar enlace", key=f"addlink_{tema}"):
            if url.strip():
                meta = read_meta(tema)
                add_link(meta, titulo, url)
                write_meta(tema, meta)
                st.success("Enlace agregado.")
                st.rerun()
            else:
                st.error("Pegá una URL válida.")

    render_list("videos", tema, exts={".mp4"}, media="video")
    if links:
        st.markdown("##### Enlaces")
        for i, it in enumerate(links):
            cols = st.columns([6,1]) if st.session_state["can_edit"] else st.columns([6])
            with cols[0]:
                titulo = (it.get("titulo") or "Video")
                url_raw = (it.get("url") or "").strip()
                url_norm = drive_preview_url(url_raw)
                st.write(f"**{titulo}**")
                if should_embed(url_norm):
                    st.video(url_norm)
                    st.markdown(f"[Abrir en pestaña]({_encode_url(url_norm)})")
                else:
                    st.markdown(f"[Abrir enlace]({_encode_url(url_norm)})")
            if st.session_state["can_edit"]:
                with cols[1]:
                    if st.button("🗑️ Eliminar enlace", key=f"del_link_{i}"):
                        meta = read_meta(tema)
                        delete_link(meta, i)
                        write_meta(tema, meta)
                        st.success("Enlace eliminado.")
                        st.rerun()
    else:
        if not storage_list(bucket_join_safe(f"{COURSE_ROOT}/{safe_folder(tema)}", "videos")):
            st.info("Todavía no hay videos cargados.")

# ================== TAB 4: AUDIOS ==================
with tabs[3]:
    st.subheader(f"Audios — {tema}")
    if st.session_state["can_edit"]:
        c1, c2 = st.columns([2,3])
        with c1:
            up = st.file_uploader("Subir audio (MP3/WAV/M4A/OGG)", type=["mp3","wav","m4a","ogg"], key=f"aud_{tema}")
        with c2:
            titulo_aud = st.text_input("Título (opcional) del audio", key=f"aud_title_{tema}")
        if up is not None:
            if too_big(up):
                st.error(f"El audio ({human_mb(up.size)}) supera {MAX_UPLOAD_MB} MB. Comprimilo (mp3 ~128 kbps) o subilo como enlace.")
            else:
                dst = bucket_join_safe(f"{COURSE_ROOT}/{safe_folder(tema)}", "audios", f"{int(time.time())}_{safe_filename(up.name)}")
                mime = {
                    ".mp3":"audio/mpeg", ".wav":"audio/wav", ".m4a":"audio/mp4", ".ogg":"audio/ogg"
                }.get(Path(up.name).suffix.lower(), "application/octet-stream")
                storage_upload(dst, up.read(), content_type=mime)
                if titulo_aud.strip():
                    meta = read_meta(tema)
                    set_title(meta, "audios", dst.split("/")[-1], titulo_aud.strip())
                    write_meta(tema, meta)
                st.success(f"Subido: {up.name}")
    render_list("audios", tema, exts={".mp3",".wav",".m4a",".ogg"}, media="audio")

st.markdown('</div>', unsafe_allow_html=True)  # cierra .card

# ================== PIE ==================
st.markdown('<div class="thin-sep"></div>', unsafe_allow_html=True)
st.caption(" ")
