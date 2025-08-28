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

TEMAS = [
    "Conceptos básicos","Nomenclatura","Isomería","Alcanos",
    "Halogenuros de alquilo","Alquenos","Alquinos","Aromáticos",
    "Alcoholes","Éteres","Fenoles","Aldehídos","Cetonas",
    "Ácidos carboxílicos","Heteroátomos","PAHs","Carbohidratos",
    "Aminoácidos","Lípidos y proteínas",
]

# ===== Límites de carga (ajusta si lo necesitás) =====
MAX_UPLOAD_MB = 50  # tope “seguro”; para videos grandes usa enlaces externos
def too_big(uploaded_file) -> bool:
    return getattr(uploaded_file, "size", 0) > MAX_UPLOAD_MB * 1024 * 1024

def human_mb(nbytes: int) -> str:
    return f"{nbytes/1024/1024:.1f} MB"

# === Secrets (NO van en el repo; cargalas en Streamlit Secrets) ===
SUPABASE_URL    = st.secrets["SUPABASE_URL"]
SUPABASE_KEY    = st.secrets["SUPABASE_KEY"]          # service_role
SUPABASE_BUCKET = st.secrets.get("SUPABASE_BUCKET", "utn")
COURSE_ROOT     = st.secrets.get("COURSE_ROOT", "Quimica_Organica")
PASSCODE        = st.secrets.get("PASSCODE", "FFCC")

# ================== ESTILO (tema oscuro + neón) ==================
st.markdown("""
<style>
:root{
  --bg:#0b1220;
  --panel:#0f1a2b;
  --soft:#101a30;
  --text:#e6eeff;
  --muted:#9fb0d8;
  --accent:#5ee7ff; /* cian neón */
  --accent-2:#8a5eff; /* violeta neón */
  --ring: 0 0 12px var(--accent);
  --ring2: 0 0 18px var(--accent-2);
}
.stApp { background: radial-gradient(1200px 600px at 10% -10%, #13223b 0%, var(--bg) 45%) fixed; color:var(--text); }
[data-testid="stSidebar"] { background: linear-gradient(180deg, #0c1628 0%, #0a1322 100%); border-right: 1px solid #162743; }
.block-container { padding-top: .8rem; }
h1, h2, h3, h4 { color: var(--text) !important; }
p, span, label, .stMarkdown, .stTextInput label { color: var(--text) !important; }
.small, .caption, .st-emotion-cache-16idsys { color: var(--muted) !important; }
div[role="tablist"] button {
  background: linear-gradient(180deg, #0f1d33 0%, #0b1527 100%) !important;
  color: var(--muted) !important;
  border: 1px solid #1c3258 !important;
  border-radius: 12px !important;
  box-shadow: inset 0 -1px 0 #091221;
}
div[role="tablist"] button[aria-selected="true"]{
  color: #dff7ff !important;
  border-color: var(--accent) !important;
  box-shadow: 0 0 0 1px var(--accent), var(--ring);
}
.stButton>button, .stDownloadButton>button {
  background: linear-gradient(90deg, rgba(94,231,255,.12), rgba(138,94,255,.12));
  border: 1px solid #1c3258;
  color: #dff7ff;
  border-radius: 12px;
  padding: .55rem 1rem;
  transition: all .18s ease;
}
.stButton>button:hover, .stDownloadButton>button:hover {
  border-color: var(--accent);
  box-shadow: 0 0 0 1px var(--accent), var(--ring);
  transform: translateY(-1px);
}
.stButton>button:active { transform: translateY(0px) scale(.99); }
.stTextInput>div>div>input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] {
  background: #0d182b !important;
  color: var(--text) !important;
  border: 1px solid #1b2f52 !important;
  border-radius: 10px !important;
}
.stTextInput>div>div>input:focus, .stTextArea textarea:focus {
  border-color: var(--accent) !important;
  box-shadow: 0 0 0 1px var(--accent), var(--ring);
}
.badge { display:inline-block; padding:4px 12px; border-radius:20px;
  background: rgba(94,231,255,.12); color:#cdecff; font-size:.85rem; margin-left:.5rem;
  border:1px solid rgba(94,231,255,.35); box-shadow: var(--ring);
}
[data-testid="stAlert"]{
  background: linear-gradient(180deg,#0f1e36,#0b1527) !important;
  border:1px solid #193158 !important;
  color:#cfe6ff !important;
  border-radius:12px !important;
}
.st-emotion-cache-1n76uvr, .st-emotion-cache-1v0mbdj { background: transparent !important; }
hr, .stMarkdown hr { border: none; height:1px; background: linear-gradient(90deg, transparent, #2a4d83, transparent); }
a { color:#8ddfff; text-decoration: none; }
a:hover { text-shadow: 0 0 8px #5ee7ff; }
.block:hover { box-shadow: 0 0 0 1px #193158, 0 0 12px rgba(94,231,255,.12); transition: box-shadow .2s; }
</style>
""", unsafe_allow_html=True)

# ================== SUPABASE CLIENT ==================
from supabase import create_client, Client
try:
    from storage3.exceptions import StorageApiError
except Exception:
    class StorageApiError(Exception):
        pass
import storage3  # para capturar storage3.utils.StorageException

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
        tmp.write(data_bytes)
        tmp.flush()
        tmp_path = tmp.name
    try:
        try:
            return supa.storage.from_(SUPABASE_BUCKET).upload(
                dst_path,
                tmp_path,
                {"content-type": str(content_type), "cache-control": "3600", "x-upsert": "true"},
            )
        except (StorageApiError, storage3.utils.StorageException, Exception) as e:
            try:
                info = (e.args or [{}])[0]
                status = info.get("statusCode")
                msg = info.get("message") or info.get("error") or info
                st.warning(f"Upload falló (status={status}). Intento update(). Detalle: {msg}")
            except Exception:
                st.warning(f"Upload falló. Intento update(). Detalle: {repr(e)}")
            try:
                return supa.storage.from_(SUPABASE_BUCKET).update(
                    dst_path,
                    tmp_path,
                    {"content-type": str(content_type), "cache-control": "3600"},
                )
            except (StorageApiError, storage3.utils.StorageException, Exception) as e2:
                try:
                    info2 = (e2.args or [{}])[0]
                    status2 = info2.get("statusCode")
                    msg2 = info2.get("message") or info2.get("error") or info2
                    st.error(f"Update también falló (status={status2}).")
                    st.code(json.dumps(info2, ensure_ascii=False, indent=2))
                except Exception:
                    st.error("Update también falló.")
                    st.code(repr(e2))
                raise
    finally:
        try:
            os.remove(tmp_path)
        except Exception:
            pass

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

# ================== CABECERA (logo grande + UTN/FRN + intro) ==================
col_logo, col_title = st.columns([1.1, 3], vertical_alignment="center")

with col_logo:
    if Path("logoutn.png").exists():
        st.image("logoutn.png", use_container_width=True)
    else:
        st.info("Subí **logoutn.png** a la raíz del repo para ver el logo aquí.")
    st.markdown(
        """
        <div style="margin-top:.4rem; line-height:1.15">
          <div style="font-weight:700; letter-spacing:.5px;">UNIVERSIDAD TECNOLÓGICA NACIONAL</div>
          <div style="opacity:.85;">FACULTAD REGIONAL DEL NEUQUÉN</div>
        </div>
        """,
        unsafe_allow_html=True
    )

with col_title:
    st.title(TITULO)
    st.subheader(PROFESOR)
    st.write(ALUMNOS)
    st.markdown('<span class="badge">Repositorio académico – Supabase Storage</span>', unsafe_allow_html=True)

st.markdown("""
---
### 🧪 ¿Qué es esta aplicación?
Esta interfaz te permite **organizar y acceder** al material didáctico del curso de **Química Orgánica**:
- Subí y consultá **resúmenes** y **apuntes** en PDF.  
- Agregá **videos** (MP4 o enlaces YouTube/Drive/Zoom) y **audios** de estudio.  
- Renombrá, eliminá y gestioná el material por **tema** de forma segura.

> **Tip:** activá el *modo edición* para cargar/gestionar archivos. Debajo vas a encontrar **pestañas rápidas por tema** para navegar más ágil.
""")
st.markdown("---")

# ================== MODO EDICIÓN ==================
if "can_edit" not in st.session_state:
    st.session_state["can_edit"] = False
with st.expander("🔐 Modo edición (subir/borrar/renombrar)", expanded=False):
    if st.session_state["can_edit"]:
        st.success("Modo edición ACTIVO.")
        if st.button("Cerrar modo edición"):
            st.session_state["can_edit"] = False
            st.rerun()
    else:
        code = st.text_input("Ingresá el código de edición", type="password")
        if st.button("Ingresar"):
            if code.strip() == PASSCODE:
                st.session_state["can_edit"] = True
                st.success("Modo edición activado.")
                st.rerun()
            else:
                st.error("Código incorrecto.")

# ====== PESTAÑAS RÁPIDAS DE TEMAS (debajo del bloque de contraseña) ======
if "tema_idx" not in st.session_state:
    st.session_state["tema_idx"] = 0
st.markdown("#### 🚀 Acceso rápido por tema")
tema_tabs = st.tabs(TEMAS)
for i, t in enumerate(TEMAS):
    with tema_tabs[i]:
        st.caption(f"Seleccionar **{t}**")
        if st.button("Abrir este tema", key=f"pick_{i}"):
            st.session_state["tema_idx"] = i
            st.rerun()

# ================== NAVEGACIÓN (sidebar sincronizada) ==================
st.sidebar.header("Navegación")
tema = st.sidebar.selectbox(
    "Elegí un tema",
    TEMAS,
    index=st.session_state["tema_idx"],
    key="tema_select"
)
st.session_state["tema_idx"] = TEMAS.index(tema)
tema = TEMAS[st.session_state["tema_idx"]]

tabs = st.tabs([
    "📄 PDF Resúmenes", "📘 PDF Apuntes del profesor",
    "🎥 Videos (MP4 o enlace)", "🎧 Audios (MP3)"
])

# -------- UI helper: listado (link + eliminar/renombrar + embed opcional) --------
def render_list(bucket_name: str, tema: str, exts: set[str], media: str | None = None):
    can_edit = st.session_state["can_edit"]
    folder = bucket_join(topic_prefix(tema), bucket_name)
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
        full_path = bucket_join(folder, name)
        url = public_url(full_path)
        title = get_title(meta, bucket_name, name) or name

        cols = st.columns([4, 2, 1, 1]) if can_edit else st.columns([6, 2])
        with cols[0]:
            st.write(f"**{title}**")
            st.caption(name)
            if url and media == "video":
                st.video(_encode_url(url))
            elif url and media == "audio":
                st.audio(_encode_url(url))
        with cols[1]:
            if url:
                st.markdown(f"[Abrir / Descargar]({_encode_url(url)})")
        if can_edit:
            with cols[2]:
                new_title = st.text_input("Título", value=title if title != name else "",
                                          key=f"ttl_{bucket_name}_{name}")
            with cols[3]:
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
                dst = bucket_join(topic_prefix(tema), "resumenes", f"{int(time.time())}_{safe_filename(up.name)}")
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
                dst = bucket_join(topic_prefix(tema), "apuntes", f"{int(time.time())}_{safe_filename(up.name)}")
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

    # a) MP4 a Storage
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
                dst = bucket_join(topic_prefix(tema), "videos", f"{int(time.time())}_{safe_filename(up.name)}")
                storage_upload(dst, up.read(), content_type="video/mp4")
                if titulo_mp4.strip():
                    set_title(meta, "videos", dst.split("/")[-1], titulo_mp4.strip())
                    write_meta(tema, meta)
                st.success(f"Subido: {up.name}")

    # b) Enlaces externos (YouTube/Drive/Zoom)
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

    # Mostrar material
    render_list("videos", tema, exts={".mp4"}, media="video")
    if links:
        st.markdown("##### Enlaces")
        for i, it in enumerate(links):
            cols = st.columns([5,1]) if st.session_state["can_edit"] else st.columns([6])
            with cols[0]:
                titulo = (it.get("titulo") or "Video")
                url_raw = (it.get("url") or "").strip()
                url_norm = drive_preview_url(url_raw)
                if should_embed(url_norm):
                    st.write(f"**{titulo}**")
                    st.video(url_norm)
                    st.markdown(f"[Abrir en pestaña]({_encode_url(url_norm)})")
                else:
                    st.write(f"**{titulo}**")
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
        if not storage_list(bucket_join(topic_prefix(tema), "videos")):
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
                dst = bucket_join(topic_prefix(tema), "audios", f"{int(time.time())}_{safe_filename(up.name)}")
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

# ================== PIE ==================
st.markdown("---")
# Pie discreto (sin el texto anterior)
st.caption(" ")
