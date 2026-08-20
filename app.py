import os
from pathlib import Path

import streamlit as st
from google import genai


APP_DIR = Path(__file__).parent
DEFAULT_MODEL = "gemini-3.5-flash-lite"

st.set_page_config(
    page_title="Synápsis Training | Ensaya antes de decirlo",
    page_icon="🌿",
    layout="centered",
)

st.markdown(
    """
    <style>
      .stApp { background: #F9F9FB; }
      h1, h2, h3 { color: #2D3436 !important; font-family: 'Helvetica Neue', sans-serif; }
      .stMarkdown, .stMarkdown p, .stMarkdown li {
        color: #20272A !important;
        font-size: 1.06rem;
        line-height: 1.65;
      }
      .stMarkdown strong { color: #11191C !important; }
      ::selection { background: #CDE8D4; color: #163321; }
      ::-moz-selection { background: #CDE8D4; color: #163321; }
      .stButton > button, .stDownloadButton > button {
        background: #2D3436; color: white; border: 0; border-radius: 8px;
        font-weight: 700; width: 100%;
      }
      .stButton > button:hover, .stDownloadButton > button:hover {
        background: #4A7C59; color: white;
      }
      div[data-testid="stAlert"] { border-radius: 10px; }
    </style>
    """,
    unsafe_allow_html=True,
)


def secret_or_env(name: str, default: str | None = None) -> str | None:
    """Permite usar Secrets de Streamlit Cloud o variables locales."""
    return st.secrets.get(name, os.getenv(name, default))


@st.cache_resource
def get_client(api_key: str):
    return genai.Client(
        api_key=api_key,
        http_options={"api_version": "v1", "timeout": 30_000},
    )


def ask_gemini(instruction: str) -> str:
    api_key = secret_or_env("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("Falta configurar GEMINI_API_KEY. Consulta el README para añadirla de forma segura.")

    model = secret_or_env("GEMINI_MODEL", DEFAULT_MODEL)
    client = get_client(api_key)
    interaction = client.interactions.create(model=model, input=instruction)
    answer = getattr(interaction, "output_text", "")
    if not answer:
        raise RuntimeError("Gemini no devolvió texto. Inténtalo de nuevo en unos segundos.")
    return answer


def set_defaults() -> None:
    for key, value in {
        "analysis": None,
        "practice": None,
        "last_context": None,
        "last_situation": None,
    }.items():
        st.session_state.setdefault(key, value)


def show_brand() -> None:
    logo = APP_DIR / "Logotipo.jpeg"
    if logo.exists():
        st.image(str(logo), width=230)
    st.title("🌿 Synápsis Training")
    st.caption("Ensaya antes de decirlo")


def build_analysis_prompt(context: str, situation: str) -> str:
    return f"""
Eres el facilitador de Synápsis, una herramienta educativa para preparar conversaciones difíciles.
Tu trabajo es ayudar a comunicarse con claridad, respeto y límites sanos. No diagnostiques,
no asumas intenciones ni sustituyas apoyo profesional. Si el relato indica peligro, violencia,
amenazas o control, prioriza seguridad y recomienda pedir ayuda local de confianza.

Entorno: {context}
Situación o mensaje de la persona:
---
{situation}
---

Responde en español, con calidez y de forma práctica. No repitas el texto original de manera
innecesaria. Usa exactamente estos apartados Markdown:

## 🔍 Qué puede estar pasando
Describe hechos observables, posible emoción y necesidad, separando cada elemento con prudencia.
## 🌿 Lo que podrías decir
Propón una frase breve en primera persona que incluya observación, impacto/necesidad y petición.
## 🎯 Tres estilos para elegir
Da tres alternativas tituladas: «Serena y directa», «Cercana y empática» y «Firme con límites».
## 🪞 Antes de conversar
Incluye una cosa que conviene evitar y una pregunta abierta útil.

Evita lenguaje terapéutico, moralizante o excesivamente largo.
""".strip()


def build_practice_prompt(context: str, situation: str, user_message: str) -> str:
    return f"""
Eres el compañero de práctica de Synápsis. Simula de forma respetuosa una posible respuesta de
la otra persona en este contexto: {context}. Situación resumida: {situation}

La persona ha dicho: {user_message}

Responde en español con:
1. «Posible respuesta»: 2-3 frases realistas, sin agresividad ni manipulación.
2. «Siguiente paso sugerido»: una frase breve que ayude a mantener el diálogo abierto.

No presentes la simulación como una predicción. No diagnostiques. Si hay señales de peligro,
violencia, amenazas o control, no simules: recomienda priorizar seguridad y apoyo local.
""".strip()


set_defaults()
show_brand()
st.write("Prepara una conversación difícil, elige el tono y ensaya una posible respuesta.")
st.info("Synápsis es una ayuda de comunicación, no terapia ni atención de emergencia.", icon="ℹ️")

contexts = [
    "Personal / familiar",
    "Equipo deportivo",
    "Comunidad de vecinos",
    "Empresa / equipo de trabajo",
    "Centro educativo / claustro",
]

st.subheader("1. Prepara la conversación")
context = st.selectbox("¿En qué entorno ocurre?", contexts)
situation = st.text_area(
    "¿Qué ha pasado o qué te gustaría decir?",
    placeholder="Ej.: Me frustró enterarme tarde de un cambio que afecta a mi trabajo.",
    height=140,
)

if st.button("Preparar mi conversación", type="primary"):
    if not situation.strip():
        st.warning("Escribe unas líneas sobre la situación para poder ayudarte.")
    else:
        with st.spinner("Preparando una forma más clara de expresarlo…"):
            try:
                st.session_state.analysis = ask_gemini(build_analysis_prompt(context, situation.strip()))
                st.session_state.last_context = context
                st.session_state.last_situation = situation.strip()
                st.session_state.practice = None
            except Exception as error:
                st.error(f"No se pudo generar el análisis. {error}")

if st.session_state.analysis:
    st.divider()
    st.subheader("2. Tu tarjeta de conversación")
    st.success("¡Tu análisis está listo! Léelo a continuación y, si quieres, ensaya una respuesta al final.")
    st.markdown(st.session_state.analysis)
    st.download_button(
        "Descargar mi tarjeta (Markdown)",
        data=st.session_state.analysis,
        file_name="tarjeta_conversacion_synapsis.md",
        mime="text/markdown",
    )

    st.divider()
    st.subheader("3. Ensaya una respuesta")
    practice_input = st.text_area(
        "Escribe la frase que quieres practicar",
        placeholder="Ej.: Me gustaría que la próxima vez me avises antes de decidirlo.",
        height=100,
    )
    if st.button("Simular una respuesta"):
        if not practice_input.strip():
            st.warning("Escribe primero la frase que quieres ensayar.")
        else:
            with st.spinner("Ensayando la conversación…"):
                try:
                    st.session_state.practice = ask_gemini(
                        build_practice_prompt(
                            st.session_state.last_context,
                            st.session_state.last_situation,
                            practice_input.strip(),
                        )
                    )
                except Exception as error:
                    st.error(f"No se pudo crear la simulación. {error}")

if st.session_state.practice:
    st.success("¡Simulación lista!")
    st.markdown(st.session_state.practice)
