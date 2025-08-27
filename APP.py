# -*- coding: utf-8 -*-
import os, json, time
from pathlib import Path
import streamlit as st

# ================== CONFIG ==================
st.set_page_config(page_title="Química Orgánica", page_icon="🧪", layout="wide")

TITULO = "QUÍMICA ORGÁNICA"
PROFESOR = "Profesor: Israel Funes"
ALUMNOS = "Alumnos: Carrasco Federico & Catereniuc Federico"
PASSCODE = "FFCC"   # Código de edición

TEMAS = [
    "Conceptos básicos", "Nomenclatura", "Isomería", "Alcanos",
    "Halogenuros de alquilo", "Alquenos", "Alquinos", "Aromáticos",
    "Alcoholes", "Éteres", "Fenoles", "Aldehídos", "Cetonas",
    "Ácidos carboxílicos", "Heteroátomos", "PAHs", "Carbohidratos",
    "Aminoácidos", "Lípidos y proteínas",
]

# Estilo simple (fondo suave y detalles redondeados)
st.markdown("""
<style>
.stApp { background: #f5f8ff; }
[data-testid="stSidebar"] { background: #eef3ff; }
.block-container { padding-top: 1rem; }
div[role="tablist"] button { border-radius: 10px !important; }
.stButton>button { border-radius: 10px; }
.stDownloadButton>button { border-radius: 10px; }
.badge {
  display:inline-block; padding:3px 10px; border-radius:20px;
  background:#e6ecff; color:#1a2b69; font-size:0.85rem; margin-left:.5rem;
}
</style>
""", unsafe_allow_html=True)

# ================== PERSISTENCIA LOCAL ==================
BASE = Path("storage")
BASE.mkdir(exist_ok=True)
META_JSON = BASE / "meta.json"

def _empty_meta():
    return {}  # {topic_key: {"titles": {"resumenes":{file:title}, ...}, "video_links":[{"titulo","url"}]}}

def load_meta():
    if META_JSON.exists():
        try:
            return json.loads(META_JSON.read_text(encoding="utf-8"))
        except Exception:
            return _empty_meta()
    return _empty_meta()

def save_meta(meta: dict):
    META_JSON.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

def safe_folder(name: str) -> str:
    return "".join([c for c in name.lower().replace(" ", "_") if c.isalnum() or c in "-_"])

def ensure_topic_dirs(topic: str):
    root = BASE / safe_folder(topic)
    (root / "resumenes").mkdir(parents=True, exist_ok=True)
    (root / "apuntes").mkdir(parents=True, exist_ok=True)
    (root / "videos").mkdir(parents=True, exist_ok=True)   # MP4 locales
    (root / "audios").mkdir(parents=True, exist_ok=True)
    return root

def list_files(folder: Path, exts):
    files = []
    if folder.exists():
        for f in sorted(folder.iterdir(), key=lambda p: p.name.lower()):
            if f.is_file() and (f.suffix.lower() in exts):
                files.append(f)
    return files

def get_title(meta, topic_key, bucket, filename):
    return (meta.get(topic_key, {})
               .get("titles", {})
               .get(bucket, {})
               .get(filename, ""))

def set_title(meta, topic_key, bucket, filename, title):
    meta.setdefault(topic_key, {}).setdefault("titles", {}).setdefault(bucket, {})
    if title.strip():
        meta[topic_key]["titles"][bucket][filename] = title.strip()
    else:
        # si está vacío, removemos el título para no ensuciar
        meta[topic_key]["titles"][bucket].pop(filename, None)

def add_link(meta, topic_key, titulo, url):
    meta.setdefault(topic_key, {}).setdefault("video_links", [])
    meta[topic_key]["video_links"].append({"titulo": titulo.strip() or "Video", "url": url.strip()})

def delete_link(meta, topic_key, idx):
    try:
        meta.setdefault(topic_key, {}).setdefault("video_links", [])
        meta[topic_key]["video_links"].pop(idx)
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
    st.markdown('<span class="badge">Repositorio académico</span>', unsafe_allow_html=True)

st.markdown("---")

# ================== MODO EDICIÓN ==================
if "can_edit" not in st.session_state:
    st.session_state["can_edit"] = False

with st.expander("🔐 Modo edición (solo para subir/borrar/renombrar)", expanded=False):
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
topic_key = safe_folder(tema)
root = ensure_topic_dirs(tema)
meta = load_meta()

tabs = st.tabs([
    "📄 PDF Resúmenes",
    "📘 PDF Apuntes del profesor",
    "🎥 Videos (MP4 o enlace)",
    "🎧 Audios (MP3)"
])

# -------- Helper UI: listado con descargar + borrar/renombrar --------
def render_file_list(bucket_name, folder: Path, exts):
    can_edit = st.session_state["can_edit"]
    files = list_files(folder, exts=exts)
    if not files:
        st.info("No hay archivos cargados aún.")
        return

    st.markdown("#### Archivos cargados")
    for p in files:
        fname = p.name
        title = get_title(meta, topic_key, bucket_name, fname) or fname
        cols = st.columns([4, 2, 1, 1]) if can_edit else st.columns([6, 2])
        with cols[0]:
            st.write(f"**{title}**")
            st.caption(fname)
        with cols[1]:
            with open(p, "rb") as f:
                st.download_button("📥 Descargar", f, file_name=fname, key=f"dl_{bucket_name}_{fname}")
        if can_edit:
            with cols[2]:
                # Renombrar título (no archivo)
                new_title = st.text_input("Título", value=title if title != fname else "", key=f"ttl_{bucket_name}_{fname}")
            with cols[3]:
                if st.button("🗑️ Eliminar", key=f"del_{bucket_name}_{fname}"):
                    try:
                        os.remove(p)
                        # limpiar título si existía
                        set_title(meta, topic_key, bucket_name, fname, "")
                        save_meta(meta)
                        st.success(f"Eliminado: {fname}")
                        st.rerun()
                    except Exception as e:
                        st.error(f"No se pudo eliminar: {e}")
            # Guardar cambio de título si lo modificó
            if new_title != (title if title != fname else ""):
                set_title(meta, topic_key, bucket_name, fname, new_title)
                save_meta(meta)

# ================== TAB 1: RESÚMENES ==================
with tabs[0]:
    st.subheader(f"Resúmenes — {tema}")
    if st.session_state["can_edit"]:
        c1, c2 = st.columns([2,3])
        with c1:
            up = st.file_uploader("Subir PDF de resumen", type=["pdf"], key=f"res_{tema}")
        with c2:
            titulo_pdf = st.text_input("Título (opcional) para el PDF recién subido", key=f"res_title_{tema}")
        if up is not None:
            savepath = root / "resumenes" / f"{int(time.time())}_{up.name}"
            with open(savepath, "wb") as f:
                f.write(up.read())
            if titulo_pdf.strip():
                set_title(meta, topic_key, "resumenes", savepath.name, titulo_pdf.strip())
                save_meta(meta)
            st.success(f"Guardado: {savepath.name}")
    render_file_list("resumenes", root / "resumenes", exts={".pdf"})

# ================== TAB 2: APUNTES DEL PROFESOR ==================
with tabs[1]:
    st.subheader(f"Apuntes del profesor — {tema}")
    if st.session_state["can_edit"]:
        c1, c2 = st.columns([2,3])
        with c1:
            up = st.file_uploader("Subir PDF de apuntes", type=["pdf"], key=f"apu_{tema}")
        with c2:
            titulo_pdf = st.text_input("Título (opcional) para el PDF recién subido", key=f"apu_title_{tema}")
        if up is not None:
            savepath = root / "apuntes" / f"{int(time.time())}_{up.name}"
            with open(savepath, "wb") as f:
                f.write(up.read())
            if titulo_pdf.strip():
                set_title(meta, topic_key, "apuntes", savepath.name, titulo_pdf.strip())
                save_meta(meta)
            st.success(f"Guardado: {savepath.name}")
    render_file_list("apuntes", root / "apuntes", exts={".pdf"})

# ================== TAB 3: VIDEOS ==================
with tabs[2]:
    st.subheader(f"Videos — {tema}")

    # a) MP4 local
    if st.session_state["can_edit"]:
        c1, c2 = st.columns([2,3])
        with c1:
            up = st.file_uploader("Subir video MP4", type=["mp4"], key=f"vid_{tema}")
        with c2:
            titulo_mp4 = st.text_input("Título (opcional) para el video recién subido", key=f"vid_title_{tema}")
        if up is not None:
            savepath = root / "videos" / f"{int(time.time())}_{up.name}"
            with open(savepath, "wb") as f:
                f.write(up.read())
            if titulo_mp4.strip():
                set_title(meta, topic_key, "videos", savepath.name, titulo_mp4.strip())
                save_meta(meta)
            st.success(f"Guardado: {savepath.name}")

    # b) Enlaces externos
    links = load_meta().get(topic_key, {}).get("video_links", [])
    if st.session_state["can_edit"]:
        st.markdown("##### Agregar enlace (YouTube/Drive/Zoom)")
        url = st.text_input("URL del video", key=f"url_{tema}")
        titulo = st.text_input("Título del video (opcional)", key=f"ttl_{tema}")
        if st.button("Agregar enlace", key=f"addlink_{tema}"):
            if url.strip():
                meta = load_meta()
                add_link(meta, topic_key, titulo, url)
                save_meta(meta)
                st.success("Enlace agregado.")
                st.rerun()
            else:
                st.error("Pegá una URL.")

    # Mostrar material
    mp4s = list_files(root / "videos", exts={".mp4"})
    titles_map = load_meta().get(topic_key, {}).get("titles", {}).get("videos", {})
    if mp4s or links:
        st.markdown("#### Material cargado")
        # MP4
        for p in mp4s:
            title = titles_map.get(p.name, p.name)
            st.write(f"**{title}**")
            st.video(str(p))
            cols = st.columns([2,1,1]) if st.session_state["can_edit"] else st.columns([2,1])
            with cols[0]:
                with open(p, "rb") as f:
                    st.download_button("📥 Descargar", f, file_name=p.name, key=f"dl_vid_{p.name}")
            if st.session_state["can_edit"]:
                with cols[1]:
                    new_title = st.text_input("Título", value=title if title != p.name else "", key=f"ttl_vid_{p.name}")
                with cols[2]:
                    if st.button("🗑️ Eliminar", key=f"del_vid_{p.name}"):
                        try:
                            os.remove(p)
                            set_title(meta, topic_key, "videos", p.name, "")
                            save_meta(meta)
                            st.success(f"Eliminado: {p.name}")
                            st.rerun()
                        except Exception as e:
                            st.error(f"No se pudo eliminar: {e}")
                if new_title != (title if title != p.name else ""):
                    set_title(meta, topic_key, "videos", p.name, new_title)
                    save_meta(meta)

        # Links
        if links:
            st.markdown("##### Enlaces")
            for i, it in enumerate(links):
                cols = st.columns([5,1]) if st.session_state["can_edit"] else st.columns([6])
                with cols[0]:
                    if it.get("titulo"):
                        st.write(f"**{it['titulo']}**")
                    st.video(it.get("url", ""))
                if st.session_state["can_edit"]:
                    if st.button("🗑️ Eliminar enlace", key=f"del_link_{i}"):
                        meta = load_meta()
                        delete_link(meta, topic_key, i)
                        save_meta(meta)
                        st.success("Enlace eliminado.")
                        st.rerun()
    else:
        st.info("Todavía no hay videos cargados.")

# ================== TAB 4: AUDIOS ==================
with tabs[3]:
    st.subheader(f"Audios — {tema}")
    if st.session_state["can_edit"]:
        c1, c2 = st.columns([2,3])
        with c1:
            up = st.file_uploader("Subir audio (MP3/WAV/M4A/OGG)", type=["mp3", "wav", "m4a", "ogg"], key=f"aud_{tema}")
        with c2:
            titulo_aud = st.text_input("Título (opcional) para el audio recién subido", key=f"aud_title_{tema}")
        if up is not None:
            savepath = root / "audios" / f"{int(time.time())}_{up.name}"
            with open(savepath, "wb") as f:
                f.write(up.read())
            if titulo_aud.strip():
                set_title(meta, topic_key, "audios", savepath.name, titulo_aud.strip())
                save_meta(meta)
            st.success(f"Guardado: {savepath.name}")

    render_file_list("audios", root / "audios", exts={".mp3", ".wav", ".m4a", ".ogg"})

# ================== PIE ==================
st.markdown("---")
st.caption(
    "Se guardan archivos en 'storage/'. En Streamlit Cloud el almacenamiento local puede "
    "reiniciarse en redeploys. Para persistencia permanente luego podemos conectar Supabase/Drive."
)
