# -*- coding: utf-8 -*-
import os, json, time
from pathlib import Path
import streamlit as st

# ============ CONFIG BÁSICA ============
st.set_page_config(page_title="Química Orgánica", page_icon="🧪", layout="wide")

# Títulos y personas
TITULO = "QUÍMICA ORGÁNICA"
PROFESOR = "Profesor: Israel Funes"
ALUMNOS = "Alumnos: Carrasco Federico & Catereniuc Federico"

# Temas fijos
TEMAS = [
    "Conceptos básicos",
    "Nomenclatura",
    "Isomería",
    "Alcanos",
    "Halogenuros de alquilo",
    "Alquenos",
    "Alquinos",
    "Aromáticos",
    "Alcoholes",
    "Éteres",
    "Fenoles",
    "Aldehídos",
    "Cetonas",
    "Ácidos carboxílicos",
    "Heteroátomos",
    "PAHs",
    "Carbohidratos",
    "Aminoácidos",
    "Lípidos y proteínas",
]

# Carpeta base de almacenamiento (se crea sola)
BASE = Path("storage")
BASE.mkdir(exist_ok=True)

# Donde guardo los enlaces de video externos
LINKS_JSON = BASE / "links.json"
if not LINKS_JSON.exists():
    LINKS_JSON.write_text(json.dumps({}, ensure_ascii=False, indent=2), encoding="utf-8")


# ============ UTILIDADES ============
def safe_folder(name: str) -> str:
    """Carpeta 'segura' para cada tema (sin espacios y minúsculas)."""
    return "".join([c for c in name.lower().replace(" ", "_") if c.isalnum() or c in "-_"])

def ensure_topic_dirs(topic: str):
    root = BASE / safe_folder(topic)
    (root / "resumenes").mkdir(parents=True, exist_ok=True)
    (root / "apuntes").mkdir(parents=True, exist_ok=True)
    (root / "videos").mkdir(parents=True, exist_ok=True)   # para MP4 locales
    (root / "audios").mkdir(parents=True, exist_ok=True)
    return root

def list_files(folder: Path, exts):
    files = []
    if folder.exists():
        for f in sorted(folder.iterdir(), key=lambda p: p.name.lower()):
            if f.is_file() and (f.suffix.lower() in exts):
                files.append(f)
    return files

def load_links():
    try:
        return json.loads(LINKS_JSON.read_text(encoding="utf-8"))
    except Exception:
        return {}

def save_links(d):
    LINKS_JSON.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")


# ============ CABECERA ============
col_logo, col_title = st.columns([1, 3], vertical_alignment="center")
with col_logo:
    # Colocá 'logoutn.png' en la raíz del repo
    if Path("logoutn.png").exists():
        st.image("logoutn.png", use_container_width=True)
    else:
        st.info("Subí un archivo llamado **logoutn.png** al repositorio (raíz) para ver el logo aquí.")

with col_title:
    st.title(TITULO)
    st.subheader(PROFESOR)
    st.write(ALUMNOS)

st.markdown("""---""")

# ============ NAVEGACIÓN ============
st.sidebar.header("Navegación")
tema = st.sidebar.selectbox("Elegí un tema", TEMAS, index=0)

root = ensure_topic_dirs(tema)
tabs = st.tabs(["📄 PDF Resúmenes", "📘 PDF Apuntes del profesor", "🎥 Videos (MP4 o enlace)", "🎧 Audios (MP3)"])


# ============ TAB 1: RESÚMENES ============
with tabs[0]:
    st.subheader(f"Resúmenes — {tema}")
    up = st.file_uploader("Subir PDF de resumen", type=["pdf"], key=f"res_{tema}")
    if up is not None:
        savepath = root / "resumenes" / f"{int(time.time())}_{up.name}"
        with open(savepath, "wb") as f:
            f.write(up.read())
        st.success(f"Guardado: {savepath.name}")

    pdfs = list_files(root / "resumenes", exts={".pdf"})
    if pdfs:
        st.markdown("#### Archivos cargados")
        for p in pdfs:
            with open(p, "rb") as f:
                st.download_button(f"📥 Descargar {p.name}", f, file_name=p.name, mime="application/pdf", key=f"dl_res_{p.name}")
    else:
        st.info("Todavía no hay resúmenes cargados.")


# ============ TAB 2: APUNTES DEL PROFESOR ============
with tabs[1]:
    st.subheader(f"Apuntes del profesor — {tema}")
    up = st.file_uploader("Subir PDF de apuntes del profesor", type=["pdf"], key=f"apu_{tema}")
    if up is not None:
        savepath = root / "apuntes" / f"{int(time.time())}_{up.name}"
        with open(savepath, "wb") as f:
            f.write(up.read())
        st.success(f"Guardado: {savepath.name}")

    pdfs = list_files(root / "apuntes", exts={".pdf"})
    if pdfs:
        st.markdown("#### Archivos cargados")
        for p in pdfs:
            with open(p, "rb") as f:
                st.download_button(f"📥 Descargar {p.name}", f, file_name=p.name, mime="application/pdf", key=f"dl_apu_{p.name}")
    else:
        st.info("Todavía no hay apuntes cargados.")


# ============ TAB 3: VIDEOS ============
with tabs[2]:
    st.subheader(f"Videos — {tema}")

    # a) Subida de MP4 directamente
    up = st.file_uploader("Subir video MP4", type=["mp4"], key=f"vid_{tema}")
    if up is not None:
        savepath = root / "videos" / f"{int(time.time())}_{up.name}"
        with open(savepath, "wb") as f:
            f.write(up.read())
        st.success(f"Guardado: {savepath.name}")

    # b) Enlaces (YouTube/Drive/Zoom)
    st.markdown("##### Agregar enlace (YouTube/Drive/Zoom)")
    url = st.text_input("Pega el enlace del video", key=f"url_{tema}")
    titulo = st.text_input("Título del enlace (opcional)", key=f"ttl_{tema}")
    if st.button("Agregar enlace", key=f"addlink_{tema}"):
        links = load_links()
        tkey = safe_folder(tema)
        links.setdefault(tkey, {}).setdefault("video_links", [])
        links[tkey]["video_links"].append({"titulo": titulo.strip() or "Video", "url": url.strip()})
        save_links(links)
        st.success("Enlace agregado.")

    # Mostrar material
    mp4s = list_files(root / "videos", exts={".mp4"})
    links = load_links().get(safe_folder(tema), {}).get("video_links", [])

    if mp4s or links:
        st.markdown("#### Material cargado")
        for p in mp4s:
            st.video(str(p))
        for it in links:
            if it.get("titulo"):
                st.write(f"**{it['titulo']}**")
            st.video(it.get("url", ""))
    else:
        st.info("Todavía no hay videos cargados.")


# ============ TAB 4: AUDIOS ============
with tabs[3]:
    st.subheader(f"Audios — {tema}")
    up = st.file_uploader("Subir audio (MP3 u otros)", type=["mp3", "wav", "m4a", "ogg"], key=f"aud_{tema}")
    if up is not None:
        savepath = root / "audios" / f"{int(time.time())}_{up.name}"
        with open(savepath, "wb") as f:
            f.write(up.read())
        st.success(f"Guardado: {savepath.name}")

    auds = list_files(root / "audios", exts={".mp3", ".wav", ".m4a", ".ogg"})
    if auds:
        st.markdown("#### Archivos cargados")
        for p in auds:
            st.audio(str(p))
            with open(p, "rb") as f:
                st.download_button(f"📥 Descargar {p.name}", f, file_name=p.name, key=f"dl_aud_{p.name}")
    else:
        st.info("Todavía no hay audios cargados.")


# ============ PIE ============
st.markdown("---")
st.caption(
    "Repositorio académico minimal – Se guardan archivos localmente en 'storage/'. "
    "Para persistencia permanente, luego podemos conectar un backend (Supabase/Drive)."
)
