# -*- coding: utf-8 -*-
import io, os, json, time
from pathlib import Path
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

# === Secrets (NO las pongas en el repo; cargalas en Streamlit Secrets) ===
SUPABASE_URL    = st.secrets["SUPABASE_URL"]
SUPABASE_KEY    = st.secrets["SUPABASE_KEY"]          # service_role
SUPABASE_BUCKET = st.secrets.get("SUPABASE_BUCKET", "utn")
COURSE_ROOT     = st.secrets.get("COURSE_ROOT", "Quimica_Organica")
PASSCODE        = st.secrets.get("PASSCODE", "FFCC")

# ================== ESTILO ==================
st.markdown("""
<style>
.stApp { background: #f5f8ff; }
[data-testid="stSidebar"] { background: #eef3ff; }
.block-container { padding-top: 1rem; }
div[role="tablist"] button { border-radius: 10px !important; }
.stButton>button, .stDownloadButton>button { border-radius: 10px; }
.badge { display:inline-block; padding:3px 10px; border-radius:20px;
  background:#e6ecff; color:#1a2b69; font-size:0.85rem; margin-left:.5rem; }
</style>
""", unsafe_allow_html=True)

# ================== SUPABASE CLIENT ==================
from supabase import create_client, Client
supa: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ================== HELPERS ==================
def safe_folder(name: str) -> str:
    return "".join([c for c in name.lower().replace(" ", "_") if c.isalnum() or c in "-_"])

def topic_prefix(tema: str) -> str:
    # Ruta base por tema dentro del bucket
    return f"{COURSE_ROOT}/{safe_folder(tema)}"

def bucket_join(*parts) -> str:
    return "/".join(p.strip("/").replace("//","/") for p in parts)

def storage_list(folder_path: str):
    try:
        return supa.storage.from_(SUPABASE_BUCKET).list(folder_path) or []
    except Exception:
        return []

def storage_upload(dst_path: str, data_bytes: bytes, content_type: str):
    return supa.storage.from_(SUPABASE_BUCKET).upload(
        dst_path, io.BytesIO(data_bytes),
        file_options={"content-type": content_type, "cache-control": "3600", "upsert": "true"}
    )

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

# ---- meta.json por tema (títulos y enlaces) ----
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

# ================== CABECERA ==================
col_logo, col_title = st.columns([1, 3], vertical_alignment="center")
with col_logo:
    if Path("logoutn.png").exists():
        st.image("logoutn.png", use_container_width=True)
    else:
        st.info("Subí **logoutn.png** a la raíz del repo para ver el logo aquí.")
with col_title:
    st.title(TITULO)
    st.subheader(PROFESOR)
    st.write(ALUMNOS)
    st.markdown('<span class="badge">Repositorio académico – Supabase Storage</span>', unsafe_allow_html=True)
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

# ================== NAVEGACIÓN ==================
st.sidebar.header("Navegación")
tema = st.sidebar.selectbox("Elegí un tema", TEMAS, index=0)

tabs = st.tabs([
    "📄 PDF Resúmenes", "📘 PDF Apuntes del profesor",
    "🎥 Videos (MP4 o enlace)", "🎧 Audios (MP3)"
])

# -------- UI helper: listado (Abrir/Descargar + Eliminar/Renombrar) --------
def render_list(bucket_name: str, tema: str, exts: set[str]):
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
        with cols[1]:
            if url:
                st.markdown(f"[Abrir / Descargar]({url})")
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
            dst = bucket_join(topic_prefix(tema), "resumenes", f"{int(time.time())}_{up.name}")
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
            dst = bucket_join(topic_prefix(tema), "apuntes", f"{int(time.time())}_{up.name}")
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
            dst = bucket_join(topic_prefix(tema), "videos", f"{int(time.time())}_{up.name}")
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
                write_meta(ema:=tema, meta)  # noqa
                st.success("Enlace agregado.")
                st.rerun()
            else:
                st.error("Pegá una URL válida.")

    # Mostrar material
    render_list("videos", tema, exts={".mp4"})
    if links:
        st.markdown("##### Enlaces")
        for i, it in enumerate(links):
            cols = st.columns([5,1]) if st.session_state["can_edit"] else st.columns([6])
            with cols[0]:
                if it.get("titulo"):
                    st.write(f"**{it['titulo']}**")
                st.video(it.get("url",""))
            if st.session_state["can_edit"]:
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
            dst = bucket_join(topic_prefix(tema), "audios", f"{int(time.time())}_{up.name}")
            mime = {".mp3":"audio/mpeg",".wav":"audio/wav",".m4a":"audio/mp4",".ogg":"audio/ogg"}.get(
                Path(up.name).suffix.lower(), "application/octet-stream"
            )
            storage_upload(dst, up.read(), content_type=mime)
            if titulo_aud.strip():
                meta = read_meta(tema)
                set_title(meta, "audios", dst.split("/")[-1], titulo_aud.strip())
                write_meta(tema, meta)
            st.success(f"Subido: {up.name}")
    render_list("audios", tema, exts={".mp3",".wav",".m4a",".ogg"})

# ================== PIE ==================
st.markdown("---")
st.caption(f"Archivos en Supabase Storage (bucket: {SUPABASE_BUCKET}). "
           "Para Años/Materias, se puede anteponer 'Año/Materia' a la ruta y agregar dos selectores.")
