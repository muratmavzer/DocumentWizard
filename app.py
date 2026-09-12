from __future__ import annotations

import os
import time

import streamlit as st
from dotenv import load_dotenv

from belgeiz.config import Settings
from belgeiz.qa import ollama_status
from belgeiz.service import BelgeIzService


load_dotenv()
st.set_page_config(
    page_title="Belgeİz · Kaynaklı Belge Asistanı",
    page_icon="🔎",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items=None,
)

st.markdown(
    """
<style>
:root{--ink:#14292d;--muted:#607477;--teal:#176b68;--teal-2:#23827d;
--accent:#e88950;--accent-hover:#f3a06c;--accent-active:#c96b37;--ring:#89d5cc}
.stApp{background:radial-gradient(circle at 80% 0%,#e1f1ed 0,transparent 34%),#f7f8f6}
.main .block-container{max-width:1120px;padding-top:1.5rem;padding-bottom:3rem}
[data-testid="stSidebar"]{background:linear-gradient(180deg,#102f34,#0d2529)}
[data-testid="stSidebar"] h1,[data-testid="stSidebar"] h2,[data-testid="stSidebar"] h3,
[data-testid="stSidebar"] p,[data-testid="stSidebar"] label{color:#f4fbf9}
[data-testid="stSidebar"] [data-baseweb="input"] input{color:#14292d}
[data-testid="stToolbar"],[data-testid="stDecoration"],#MainMenu,footer,
[data-testid="manage-app-button"]{display:none!important}
[data-testid="stHeader"]{background:transparent}
button[data-testid="stBaseButton-primary"],button[kind="primary"]{
background:var(--accent)!important;border:1px solid var(--accent)!important;color:#14292d!important;
font-weight:750!important;box-shadow:0 5px 14px #071f2229!important;
transition:background-color .16s ease,border-color .16s ease,box-shadow .16s ease,transform .16s ease!important}
button[data-testid="stBaseButton-primary"]:hover:not(:disabled),button[kind="primary"]:hover:not(:disabled){
background:var(--accent-hover)!important;border-color:#ffd0b1!important;color:#102a2e!important;
box-shadow:0 8px 20px #071f2240!important;transform:translateY(-1px)}
button[data-testid="stBaseButton-primary"]:active:not(:disabled),button[kind="primary"]:active:not(:disabled){
background:var(--accent-active)!important;border-color:var(--accent-active)!important;color:white!important;
box-shadow:0 2px 7px #071f2238!important;transform:translateY(0)}
button[data-testid="stBaseButton-secondary"],button[kind="secondary"]{
background:#f7fbfa!important;border:1px solid #9abdb8!important;color:#164c4b!important;
font-weight:680!important;box-shadow:none!important;
transition:background-color .16s ease,border-color .16s ease,box-shadow .16s ease,transform .16s ease!important}
button[data-testid="stBaseButton-secondary"]:hover:not(:disabled),button[kind="secondary"]:hover:not(:disabled){
background:#e0f1ee!important;border-color:var(--teal-2)!important;color:#0d3b3b!important;
box-shadow:0 5px 13px #0d44451f!important;transform:translateY(-1px)}
button[data-testid="stBaseButton-secondary"]:active:not(:disabled),button[kind="secondary"]:active:not(:disabled){
background:#cbe6e1!important;border-color:var(--teal)!important;transform:translateY(0)}
[data-testid="stSidebar"] button[data-testid="stBaseButton-secondary"],
[data-testid="stSidebar"] button[kind="secondary"]{
background:#163c41!important;border-color:#527b7e!important;color:#f4fbf9!important}
[data-testid="stSidebar"] button[data-testid="stBaseButton-secondary"]:hover:not(:disabled),
[data-testid="stSidebar"] button[kind="secondary"]:hover:not(:disabled){
background:#24565a!important;border-color:#85c9c1!important;color:white!important;
box-shadow:0 6px 16px #06191c59!important}
button[data-testid="stBaseButton-primary"]:focus-visible,button[kind="primary"]:focus-visible,
button[data-testid="stBaseButton-secondary"]:focus-visible,button[kind="secondary"]:focus-visible{
outline:3px solid var(--ring)!important;outline-offset:2px!important}
button[data-testid="stBaseButton-primary"]:disabled,button[kind="primary"]:disabled{
background:#496468!important;border-color:#5f797c!important;color:#b9cdcc!important;
box-shadow:none!important;cursor:not-allowed!important;transform:none!important;opacity:1!important}
button[data-testid="stBaseButton-secondary"]:disabled,button[kind="secondary"]:disabled{
background:#e6ecea!important;border-color:#c3d0ce!important;color:#879a98!important;
box-shadow:none!important;cursor:not-allowed!important;transform:none!important;opacity:1!important}
[data-testid="stSidebar"] [data-baseweb="input"]>div,
[data-testid="stSidebar"] [data-baseweb="select"]>div{
background:#f6faf9!important;border-color:#66898a!important;transition:border-color .16s ease,box-shadow .16s ease}
[data-testid="stSidebar"] [data-baseweb="input"]>div:hover,
[data-testid="stSidebar"] [data-baseweb="select"]>div:hover{border-color:#8acbc3!important}
[data-testid="stSidebar"] [data-baseweb="input"]>div:focus-within,
[data-testid="stSidebar"] [data-baseweb="select"]>div:focus-within{
border-color:var(--ring)!important;box-shadow:0 0 0 3px #6fc9bf33!important}
[data-testid="stSidebar"] [role="radiogroup"] label{border-radius:10px;padding:.18rem .3rem}
[data-testid="stSidebar"] [role="radiogroup"] label:hover{background:#ffffff0d}
.brand{display:flex;align-items:center;gap:.75rem;margin:.2rem 0 1.25rem}
.brand-mark{width:42px;height:42px;border-radius:13px;display:grid;place-items:center;
background:linear-gradient(135deg,#44a99f,#f0a06e);font-size:1.25rem;box-shadow:0 8px 20px #0003}
.brand-name{font-weight:800;font-size:1.2rem;color:#fff}.brand-sub{font-size:.77rem;color:#a9c8c6}
.hero{padding:1.7rem 1.9rem;border-radius:24px;color:white;overflow:hidden;position:relative;
background:linear-gradient(120deg,#123b42,#176b68 67%,#d77d4d 130%);box-shadow:0 18px 45px #10373c2e}
.hero:after{content:"";position:absolute;width:260px;height:260px;border-radius:50%;right:-85px;
top:-135px;border:42px solid #ffffff17}.hero-badge{display:inline-block;padding:.3rem .65rem;
border-radius:999px;background:#ffffff21;font-size:.78rem;font-weight:650}
.hero h1{margin:.55rem 0 0;font-size:2.45rem;letter-spacing:-.05em;color:white}
.hero p{margin:.5rem 0 0;max-width:720px;color:#def1ed;font-size:1rem;line-height:1.55}
.step-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:.8rem;margin:.8rem 0 1.25rem}
.step{background:#ffffffd1;border:1px solid #dce7e4;border-radius:17px;padding:1rem}
.step b{display:block;color:var(--ink);margin-bottom:.18rem}.step span{font-size:.86rem;color:var(--muted)}
.step-no{font-size:.72rem!important;color:#fff!important;background:var(--teal);padding:.2rem .45rem;
border-radius:7px;margin-right:.3rem}.empty{text-align:center;background:#ffffffb8;border:1px dashed #b9cfcb;
border-radius:20px;padding:2.2rem 1rem;color:var(--muted)}
div[data-testid="stChatMessage"]{background:#ffffffd1;border:1px solid #dce6e4;border-radius:18px}
div[data-testid="stMetric"]{background:#fff;border:1px solid #dce6e4;border-radius:16px;padding:.8rem 1rem}
.privacy{font-size:.8rem;color:#607477;background:#edf3f1;border-radius:12px;padding:.7rem .85rem}
[data-testid="stFileUploaderDropzoneInstructions"] span{display:none}
[data-testid="stFileUploaderDropzoneInstructions"] span:before{content:"Belgeleri buraya sürükleyin";display:block}
[data-testid="stFileUploaderDropzoneInstructions"] small{display:none}
[data-testid="stFileUploaderDropzone"] button{font-size:0!important}
[data-testid="stFileUploaderDropzone"] button>*{display:none!important}
[data-testid="stFileUploaderDropzone"] button:after{content:"Dosya seç";font-size:.875rem;color:inherit}
@media(max-width:760px){.step-grid{grid-template-columns:1fr}.hero h1{font-size:2rem}}
</style>
""",
    unsafe_allow_html=True,
)

PROVIDERS = {"OpenAI API": "openai", "Yerel Ollama · ücretsiz": "ollama"}
OLLAMA_MODELS = ["qwen3:1.7b", "qwen3:4b-instruct", "qwen3:8b"]


def reset_chat() -> None:
    st.session_state.messages = []


def render_citations(citations: list[dict]) -> None:
    if citations:
        st.caption("Yanıtı destekleyen kaynaklar")
    for index, citation in enumerate(citations, start=1):
        with st.expander(
            f"{index}. {citation['document_name']} · sayfa {citation['page']}"
        ):
            st.write(citation["text"])


def render_evidence_status(score: float | None, evidence_mode: str) -> None:
    if score is None:
        return
    if evidence_mode == "full_context":
        st.caption("Kanıt yöntemi: tam belge bağlamı · çok-adımlı analiz")
    else:
        st.caption(f"En yüksek kanıt skoru: {score:.2f}")


if "service" not in st.session_state:
    st.session_state.service = None
if "messages" not in st.session_state:
    st.session_state.messages = []
if "ollama_check" not in st.session_state:
    st.session_state.ollama_check = None
if "uploader_version" not in st.session_state:
    st.session_state.uploader_version = 0

notice = st.session_state.pop("notice", None)
if notice:
    st.toast(notice, icon="🗑️")

base_settings = Settings.from_env()

with st.sidebar:
    st.markdown(
        '<div class="brand"><div class="brand-mark">⌕</div><div>'
        '<div class="brand-name">Belgeİz</div>'
        '<div class="brand-sub">Kaynağını gösteren belge asistanı</div></div></div>',
        unsafe_allow_html=True,
    )
    st.markdown("### 1 · Yanıt motoru")
    provider_label = st.radio(
        "Model sağlayıcısı", list(PROVIDERS), label_visibility="collapsed"
    )
    provider = PROVIDERS[provider_label]

    if provider == "openai":
        api_key = st.text_input(
            "OpenAI API anahtarı",
            value=os.getenv("OPENAI_API_KEY", ""),
            type="password",
            help="Anahtar yalnızca bu oturumdaki yanıt isteğinde kullanılır.",
        )
        model = st.text_input("OpenAI model adı", value=base_settings.model)
        ollama_url = base_settings.ollama_url
    else:
        api_key = ""
        model = st.selectbox(
            "Yerel model",
            OLLAMA_MODELS,
            index=1,
            help="1.7B daha hızlı; 8B daha kaliteli fakat daha çok bellek kullanır.",
        )
        ollama_url = st.text_input("Ollama adresi", value=base_settings.ollama_url)
        if st.button("Yerel bağlantıyı denetle", use_container_width=True):
            with st.spinner("Ollama denetleniyor…"):
                st.session_state.ollama_check = ollama_status(ollama_url)
        if st.session_state.ollama_check:
            available, installed = st.session_state.ollama_check
            if available and model in installed:
                st.success("Ollama ve seçilen model hazır.")
            elif available:
                st.warning(f"Ollama açık; {model} henüz indirilmemiş.")
            else:
                st.error("Ollama'ya ulaşılamadı. YerelModelKur.cmd dosyasını çalıştırın.")

    st.markdown("### 2 · Belgeler")
    uploaded_files = st.file_uploader(
        "Belgeleri seçin",
        type=["pdf", "jpg", "jpeg", "png"],
        accept_multiple_files=True,
        key=f"documents_{st.session_state.uploader_version}",
        help=f"PDF, JPG veya PNG · dosya başına en fazla {base_settings.max_file_mb} MB",
        label_visibility="collapsed",
    )
    with st.expander("Gelişmiş işleme ayarları"):
        ocr_enabled = st.toggle(
            "Taranmış PDF sayfalarında OCR",
            value=base_settings.ocr_enabled,
            help=(
                "Metin içeren PDF sayfaları OCR yapılmadan hızla okunur. "
                "Taranmış her sayfa CPU'da yaklaşık 15–30 saniye sürebilir."
            ),
        )
        threshold = st.slider(
            "Kanıt eşiği",
            0.05,
            0.60,
            float(base_settings.retrieval_threshold),
            0.01,
            help=(
                "Büyük belge kümelerinde yükseldikçe zayıf kanıtlar daha sık elenir. "
                "Bağlama sığan küçük belgelerde model bütün kaynakları denetler."
            ),
        )
    process = st.button(
        "Belgeleri hazırla",
        type="primary",
        use_container_width=True,
        disabled=not uploaded_files,
    )
    if st.button("Oturumu temizle", use_container_width=True):
        st.session_state.service = None
        st.session_state.uploader_version += 1
        reset_chat()
        st.rerun()

if process:
    settings = Settings(
        model=model.strip() if provider == "openai" else base_settings.model,
        ollama_model=model.strip() if provider == "ollama" else base_settings.ollama_model,
        ollama_url=ollama_url.strip(),
        retrieval_threshold=threshold,
        max_file_mb=base_settings.max_file_mb,
        max_pdf_pages=base_settings.max_pdf_pages,
        max_context_chars=base_settings.max_context_chars,
        max_chunk_words=base_settings.max_chunk_words,
        chunk_overlap_words=base_settings.chunk_overlap_words,
        top_k=base_settings.top_k,
        ocr_enabled=ocr_enabled,
        ocr_render_scale=base_settings.ocr_render_scale,
        ocr_max_image_side=base_settings.ocr_max_image_side,
        ocr_min_text_chars=base_settings.ocr_min_text_chars,
    )
    service = BelgeIzService(settings)
    progress_bar = st.progress(0.0, text="Belgeler hazırlanıyor…")
    status_box = st.status("Belge işleme başladı", expanded=True)
    errors: list[str] = []
    started_at = time.perf_counter()

    for file_index, uploaded in enumerate(uploaded_files, start=1):
        status_box.write(f"**{uploaded.name}** açılıyor…")

        def on_progress(current: int, total: int, message: str) -> None:
            within_file = current / max(1, total)
            overall = ((file_index - 1) + within_file) / len(uploaded_files)
            progress_bar.progress(
                min(1.0, overall), text=f"{uploaded.name} · {message}"
            )
            status_box.update(label=f"{uploaded.name} · {message}")

        try:
            result = service.add_document(
                uploaded.name, uploaded.getvalue(), progress=on_progress
            )
            status_box.write(
                f"✓ {result.page_count} sayfa, {len(result.chunks)} kaynak parçası hazır"
            )
            for warning in result.warnings:
                status_box.warning(warning)
        except Exception as exc:
            errors.append(f"{uploaded.name}: {exc}")

    elapsed = time.perf_counter() - started_at
    progress_bar.progress(1.0, text=f"İşlem {elapsed:.1f} saniyede tamamlandı")
    status_box.update(
        label=f"Belge işleme tamamlandı · {elapsed:.1f} saniye",
        state="complete" if service.chunks else "error",
        expanded=False,
    )
    if service.chunks:
        st.session_state.service = service
        reset_chat()
        st.success(
            f"{len(service.documents)} belge ve {len(service.chunks)} kaynak parçası kullanıma hazır."
        )
    for error in errors:
        st.error(error)

st.markdown(
    """
<div class="hero">
  <span class="hero-badge">YEREL BELGE İŞLEME · DOĞRULANABİLİR YANIT</span>
  <h1>Belgenin söylediğini bulun.</h1>
  <p>PDF ve görsellerinizi Türkçe veya İngilizce sorgulayın. Belgeİz her yanıtı
  dosya ve sayfa kaynağıyla gösterir; yeterli kanıt yoksa yanıt üretmez.</p>
</div>
<div class="step-grid">
  <div class="step"><b><span class="step-no">1</span> Motoru seçin</b><span>OpenAI veya ücretsiz yerel Ollama</span></div>
  <div class="step"><b><span class="step-no">2</span> Belgeyi bırakın</b><span>PDF, JPG ve PNG · Türkçe ve İngilizce</span></div>
  <div class="step"><b><span class="step-no">3</span> Sorun</b><span>Yanıtın dayandığı sayfayı anında görün</span></div>
</div>
""",
    unsafe_allow_html=True,
)

service: BelgeIzService | None = st.session_state.service
if service is None:
    st.markdown(
        '<div class="empty">👈 Sol panelden yanıt motorunu seçin, belgelerinizi ekleyin ve '
        '<b>Belgeleri hazırla</b> düğmesine basın.</div>',
        unsafe_allow_html=True,
    )
    st.stop()

total_pages = sum(document.page_count for document in service.documents)
ocr_chunks = sum("ocr" in chunk.extraction_method for chunk in service.chunks)
col1, col2, col3, col4 = st.columns(4)
col1.metric("Belge", len(service.documents))
col2.metric("Sayfa", total_pages)
col3.metric("Kaynak parçası", len(service.chunks))
col4.metric("OCR ile okunan", ocr_chunks)

with st.expander("Hazır belgeleri yönet", expanded=False):
    for document_index, document in enumerate(service.documents):
        info_col, action_col = st.columns([4, 1])
        info_col.markdown(
            f"**{document.document_name}**  \n{document.page_count} sayfa · "
            f"{len(document.chunks)} kaynak parçası"
        )
        if action_col.button(
            "Çıkar",
            key=f"remove_document_{document_index}_{document.document_name}",
            use_container_width=True,
            help=f"{document.document_name} belgesini aktif kaynaklardan çıkar",
        ):
            removed = service.remove_document(document_index)
            reset_chat()
            st.session_state.uploader_version += 1
            st.session_state.notice = f"{removed.document_name} çıkarıldı."
            if not service.chunks:
                st.session_state.service = None
            st.rerun()

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message["role"] == "assistant":
            render_citations(message.get("citations", []))
            render_evidence_status(
                message.get("score"), message.get("evidence_mode", "retrieval")
            )

question = st.chat_input("Belgeleriniz hakkında sorunuzu yazın…")
if question:
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)
    with st.chat_message("assistant"):
        if provider == "openai" and not api_key.strip():
            message = (
                "Yanıt üretmek için sol panelde OpenAI API anahtarını girin "
                "veya ücretsiz yerel Ollama'yı seçin."
            )
            st.warning(message)
            payload = {
                "role": "assistant",
                "content": message,
                "citations": [],
                "score": None,
            }
        else:
            try:
                with st.spinner("Belgelerde kanıt aranıyor ve yanıt hazırlanıyor…"):
                    qa = service.create_qa(
                        api_key=api_key.strip(),
                        model=model.strip(),
                        provider=provider,
                        ollama_url=ollama_url.strip(),
                    )
                    answer = qa.ask(question)
                st.markdown(answer.text)
                citation_payload = [
                    {
                        "chunk_id": citation.chunk_id,
                        "document_name": citation.document_name,
                        "page": citation.page,
                        "text": citation.text,
                    }
                    for citation in answer.citations
                ]
                render_citations(citation_payload)
                render_evidence_status(answer.retrieval_score, answer.evidence_mode)
                payload = {
                    "role": "assistant",
                    "content": answer.text,
                    "citations": citation_payload,
                    "score": answer.retrieval_score,
                    "evidence_mode": answer.evidence_mode,
                }
            except Exception as exc:
                message = f"Yanıt hazırlanamadı: {exc}"
                st.error(message)
                payload = {
                    "role": "assistant",
                    "content": message,
                    "citations": [],
                    "score": None,
                }
    st.session_state.messages.append(payload)

if provider == "ollama":
    privacy_text = "🔒 Yerel mod: belge metni, soru ve yanıt bu bilgisayardan çıkmaz."
else:
    privacy_text = (
        "🔐 OpenAI modu: yalnızca soru ve seçilen kısa kanıt parçaları API'ye gönderilir."
    )
st.markdown(f'<div class="privacy">{privacy_text}</div>', unsafe_allow_html=True)
