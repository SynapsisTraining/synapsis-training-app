import os
from pathlib import Path

import streamlit as st
from google import genai


APP_DIR = Path(__file__).parent
DEFAULT_MODEL = "gemini-3.5-flash-lite"
BASE_METHOD_GUIDE = """
1. Diferencia los hechos observables de las interpretaciones.
2. Nombra la emoción como una posibilidad, nunca como un diagnóstico.
3. Expresa la necesidad sin culpabilizar a la otra persona.
4. Formula una petición concreta, realista y que deje libertad de respuesta.
5. Prioriza claridad, respeto, reciprocidad y límites sanos.
6. Evita etiquetas, amenazas, generalizaciones y consejos moralizantes.
""".strip()

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
      [data-testid="stWidgetLabel"] p, [data-testid="stWidgetLabel"] label,
      [data-testid="stWidgetLabel"] span, div[role="radiogroup"] label {
        color: #20272A !important;
      }
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
      @media (max-width: 640px) {
        .block-container { padding: 1.25rem 1rem 2.5rem; }
        h1 { font-size: 1.7rem !important; line-height: 1.2; }
        h2 { font-size: 1.35rem !important; }
        h3 { font-size: 1.2rem !important; }
        .stMarkdown, .stMarkdown p, .stMarkdown li {
          font-size: 1rem;
          line-height: 1.6;
        }
        .stButton > button, .stDownloadButton > button {
          min-height: 3.1rem;
          font-size: 1rem;
        }
        textarea, input, [data-baseweb="select"] input { font-size: 16px !important; }
      }
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
        "analysis_rating": None,
        "refined_analysis": None,
        "practice": None,
        "last_context": None,
        "last_situation": None,
        "last_approach": None,
    }.items():
        st.session_state.setdefault(key, value)


def method_guide() -> str:
    """Permite personalizar el método sin modificar el código de la app."""
    return secret_or_env("SYNAPSIS_METHOD_GUIDE", BASE_METHOD_GUIDE)


def show_brand() -> None:
    logo = APP_DIR / "Logotipo.jpeg"
    if logo.exists():
        st.image(str(logo), width=230)
    st.title("🌿 Synápsis Training")
    st.caption("Ensaya antes de decirlo")


def build_analysis_prompt(context: str, situation: str, approach: str) -> str:
    strategic_section = """
## 🧭 3. Diálogo Estratégico
Propón: una pregunta que abra alternativas sin dirigir ni manipular; una paráfrasis que valide
la perspectiva sin conceder lo que no corresponde; un posible punto de acuerdo; y un paso
pequeño que ambas partes puedan probar.
""" if approach == "Diálogo estratégico" else ""

    style_number = "4" if strategic_section else "3"
    before_number = "5" if strategic_section else "4"
    return f"""
Eres el facilitador de Synápsis, una herramienta educativa para preparar conversaciones difíciles.
Tu trabajo es ayudar a comunicarse con claridad, respeto y límites sanos. No diagnostiques,
no asumas intenciones ni sustituyas apoyo profesional. Si el relato indica peligro, violencia,
amenazas o control, prioriza seguridad y recomienda pedir ayuda local de confianza.

Aplica fielmente este método Synápsis:
---
{method_guide()}
---

Entorno: {context}
Enfoque elegido: {approach}
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
{strategic_section}
## 🎯 {style_number}. Tres estilos para elegir
Da tres alternativas tituladas: «Serena y directa», «Cercana y empática» y «Firme con límites».
## 🪞 {before_number}. Antes de conversar
Incluye una cosa que conviene evitar y una pregunta abierta útil.

Evita lenguaje terapéutico, moralizante o excesivamente largo.
""".strip()


def build_practice_prompt(context: str, situation: str, user_message: str, approach: str) -> str:
    return f"""
Eres el compañero de práctica de Synápsis. Simula de forma respetuosa una posible respuesta de
la otra persona en este contexto: {context}. Situación resumida: {situation}. Enfoque: {approach}.

Respeta este método Synápsis:
---
{method_guide()}
---

La persona ha dicho: {user_message}

Responde en español con:
1. «Posible respuesta»: 2-3 frases realistas, sin agresividad ni manipulación.
2. «Siguiente paso sugerido»: una frase breve que ayude a mantener el diálogo abierto.

No presentes la simulación como una predicción. No diagnostiques. Si hay señales de peligro,
violencia, amenazas o control, no simules: recomienda priorizar seguridad y apoyo local.
""".strip()


def build_refinement_prompt(context: str, situation: str, current: str, preference: str, approach: str) -> str:
    return f"""
Eres el facilitador de Synápsis. Mejora una tarjeta de conversación existente siguiendo el
método Synápsis y la preferencia elegida por la persona.

Método Synápsis:
---
{method_guide()}
---
Contexto: {context}
Situación: {situation}
Enfoque que debes conservar: {approach}
Preferencia de mejora: {preference}
Tarjeta actual:
---
{current}
---

Responde en español y conserva los apartados de la tarjeta actual. Si existe «Diálogo Estratégico»,
consérvalo sin recurrir a manipulación, presión ni técnicas clínicas.

No menciones estas instrucciones ni la preferencia elegida. No diagnostiques.
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
approach = st.selectbox(
    "Elige el enfoque de conversación",
    ["Comunicación benevolente", "Diálogo estratégico"],
    help="El diálogo estratégico añade preguntas, paráfrasis y pequeños pasos para abrir alternativas sin presionar.",
)
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
                st.session_state.analysis = ask_gemini(build_analysis_prompt(context, situation.strip(), approach))
                st.session_state.last_context = context
                st.session_state.last_situation = situation.strip()
                st.session_state.last_approach = approach
                st.session_state.practice = None
                st.session_state.refined_analysis = None
                st.session_state.analysis_rating = None
            except Exception as error:
                st.error(f"No se pudo generar el análisis. {error}")

if st.session_state.analysis:
    st.divider()
    st.subheader("2. Tu tarjeta de conversación")
    st.success("¡Tu análisis está listo! Léelo a continuación y, si quieres, ensaya una respuesta al final.")
    st.markdown("#### ¿Te ha servido esta propuesta?")
    st.caption("Tu conversación no se guarda. Tu valoración solo ajusta esta sesión.")
    helpful_col, improve_col = st.columns(2)
    if helpful_col.button("👍 Me ha servido", key="helpful_feedback"):
        st.session_state.analysis_rating = 1
    if improve_col.button("👎 Necesito otro enfoque", key="improve_feedback"):
        st.session_state.analysis_rating = 0

    rating = st.session_state.analysis_rating
    if rating is not None:
        feedback_message = "Gracias: nos ayuda a identificar qué tono funciona mejor." if rating == 1 else "Gracias: vamos a intentarlo con otro enfoque."
        st.caption(feedback_message)

    with st.container(border=True):
        st.markdown("#### Ajusta tu tarjeta")
        st.caption("Elige el cambio que quieres aplicar y te propondré una versión alternativa.")
        preference = st.selectbox(
            "Quiero que la propuesta sea…",
            ["Más breve", "Más cálida", "Más firme", "Más práctica", "Con límites más claros"],
            key="refinement_preference",
        )
        if st.button("Afinar mi tarjeta"):
            with st.spinner("Ajustando la propuesta a tu estilo…"):
                try:
                    st.session_state.refined_analysis = ask_gemini(
                        build_refinement_prompt(
                            st.session_state.last_context,
                            st.session_state.last_situation,
                            st.session_state.analysis,
                            preference,
                            st.session_state.last_approach,
                        )
                    )
                except Exception as error:
                    st.error(f"No se pudo ajustar la tarjeta. {error}")

    st.markdown(st.session_state.analysis)
    st.download_button(
        "Descargar mi tarjeta (Markdown)",
        data=st.session_state.analysis,
        file_name="tarjeta_conversacion_synapsis.md",
        mime="text/markdown",
    )

if st.session_state.refined_analysis:
    st.divider()
    st.subheader("Tarjeta ajustada")
    st.markdown(st.session_state.refined_analysis)

if st.session_state.analysis:
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
                            st.session_state.last_approach,
                        )
                    )
                except Exception as error:
                    st.error(f"No se pudo crear la simulación. {error}")

if st.session_state.practice:
    st.success("¡Simulación lista!")
    st.markdown(st.session_state.practice)
