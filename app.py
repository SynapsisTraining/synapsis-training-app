import os
from pathlib import Path

import streamlit as st
from google import genai


APP_DIR = Path(__file__).parent
DEFAULT_MODEL = "gemini-3.5-flash-lite"
BASE_METHOD_GUIDE = """
COMUNICACIÓN BENEVOLENTE — Arquitectura 1.1

No es una secuencia rígida: enseña a reconocer el estado de una interacción y elegir
la respuesta más adecuada.

PARA: crea espacio antes de reaccionar.
MIRA: distingue hechos, tu experiencia y la posible experiencia de la otra persona.
ELIGE: decide qué necesita la interacción ahora.
ACTÚA: expresa, escucha o repara.

Principios: me comprendo, me expreso y te comprendo.
Competencias observables: regulación, autocomprensión, expresión, escucha,
discriminación, estrategia y reparación.

Con activación roja, no se intenta resolver: se pausa, regula y evita escalar.
Comprender no equivale a aprobar. Reparar no exige perdonar ni reconciliarse.
Evita etiquetas, amenazas, culpabilización y técnicas de presión o manipulación.
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
        "last_role": None,
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


def build_analysis_prompt(context: str, situation: str, role: str) -> str:
    role_guidance = (
        "La persona quiere expresar algo propio. Prioriza una expresión clara, una petición o un límite "
        "cuando sea adecuado."
        if role == "Quiero expresar algo"
        else "La persona quiere escuchar y comprender. Prioriza presencia, preguntas abiertas, paráfrasis "
        "y aclaración antes de dar su propia posición."
    )
    return f"""
Eres el facilitador de Synápsis, una herramienta educativa de entrenamiento para conversaciones
difíciles. Enseñas a reconocer el estado de una interacción y elegir una respuesta adecuada,
no a encontrar una frase perfecta. No diagnostiques ni asumas intenciones. Si aparece peligro,
violencia, amenazas o control, prioriza seguridad y apoyo local de confianza.

Aplica fielmente este método Synápsis:
---
{method_guide()}
---

Entorno: {context}
Posición desde la que llega: {role}
Orientación para esta práctica: {role_guidance}
Situación o mensaje de la persona:
---
{situation}
---

Responde en español, con calidez y precisión. No repitas el relato. Usa exactamente estos
apartados Markdown:

## 🔍 Radiografía emocional
Describe brevemente el clima emocional de la interacción. Incluye un «Índice de agresividad de la
interacción: X/10», basado solo en el lenguaje, los hechos y la tensión descritos; no califiques ni
diagnostiques a ninguna persona. Explica en una frase el índice. Añade la activación Verde, Amarillo
o Rojo como orientación para decidir el ritmo de la conversación. Después enumera de dos a cuatro
«Etiquetas emocionales y necesidades»: para cada una, expresa primero una emoción como verbo o
experiencia en primera persona (por ejemplo: «me preocupa», «me duele», «me frustra») y, tras una
flecha, la necesidad que podría haber detrás (por ejemplo: «me preocupa → necesito claridad»).
Preséntalas como posibilidades, no como certezas ni diagnósticos.
## 🛑 PARA
Indica qué reacción automática conviene detener y cuál es el avance más seguro ahora.
## 👁️ MIRA
Separa: hechos observables; lo que podría estar ocurriendo en la persona; y lo que podría estar
ocurriendo en la otra persona. Formula las dos últimas como posibilidades, nunca certezas.
## 🧭 ELIGE
Elige una sola acción entre: escuchar, aclarar, expresar, negociar, poner un límite, detenerse o
reparar. Explica en una frase por qué esa es la necesidad de la interacción ahora.
## 💬 ACTÚA
Propón una intervención breve, realista y en primera persona que ejecute la acción elegida. Si el
estado es Rojo, ofrece una pausa segura: no intentes resolver el contenido del conflicto.
## 💳 Tarjeta de conversación
Reúne una propuesta breve y usable para esta situación: una frase de inicio, una pregunta abierta
o escucha útil cuando corresponda, y un posible siguiente paso. Mantén claridad, respeto y límites
sanos; adapta la tarjeta a la posición desde la que llega la persona.
## 🎯 Tu reto de entrenamiento
Formula un reto breve que distinga claramente tres tiempos:
- **Pasado:** qué hecho conviene reconocer sin intentar cambiarlo.
- **Presente:** qué decisión, petición, límite o escucha es posible elegir ahora.
- **Futuro:** qué paso concreto puede nacer de esa decisión presente.
Recuerda en una frase que el pasado no se puede cambiar y que el futuro será fruto de lo que se
decida en el presente. Pide después una primera respuesta propia con una única instrucción clara.

Evita lenguaje terapéutico, moralizante, etiquetas, presión o manipulación.
""".strip()


def build_practice_prompt(context: str, situation: str, role: str) -> str:
    role_guidance = (
        "Las tres intervenciones deben ayudar a expresar con claridad, sin perder escucha ni respeto."
        if role == "Quiero expresar algo"
        else "Las tres intervenciones deben ayudar a escuchar y comprender primero, sin asumir ni interrogar."
    )
    return f"""
Eres el facilitador de Synápsis. Diseña un diálogo estratégico breve de tres intervenciones de la
persona y tres posibles réplicas del interlocutor. Su función es abrir alternativas y avanzar con
claridad, nunca convencer, presionar ni manipular. Contexto: {context}. Situación: {situation}.
Posición de la persona: {role}. {role_guidance}

Respeta este método Synápsis:
---
{method_guide()}
---

Responde en español con exactamente estos apartados Markdown:

## 🎯 Propósito del diálogo
Explica en una frase qué avance pequeño y realista se busca.
## 1. Abrir la conversación
**Tú:** una intervención breve basada en observación o pregunta abierta.
**La otra persona podría responder:** una réplica verosímil, no una predicción.
## 2. Comprender y aclarar
**Tú:** una intervención que recoja lo escuchado y aclare lo importante, sin conceder lo que no corresponde.
**La otra persona podría responder:** una réplica verosímil.
## 3. Proponer un siguiente paso
**Tú:** una propuesta concreta, libre de presión, o un límite respetuoso si corresponde.
**La otra persona podría responder:** una réplica verosímil.
## 🧭 Clave para conducirlo
Da una sola indicación breve sobre qué actitud sostener durante el diálogo.

En activación Roja, no diseñes un diálogo para resolver: formula una pausa segura y deja el resto
para otro momento. Si hay señales de peligro, violencia, amenazas o control, prioriza seguridad y apoyo local.
""".strip()


def build_refinement_prompt(context: str, situation: str, current: str, preference: str, role: str) -> str:
    return f"""
Eres el facilitador de Synápsis. Mejora una tarjeta de conversación existente siguiendo el
método Synápsis y la preferencia elegida por la persona.

Método Synápsis:
---
{method_guide()}
---
Contexto: {context}
Situación: {situation}
Posición de la persona: {role}
Preferencia de mejora: {preference}
Tarjeta actual:
---
{current}
---

Responde en español y conserva los apartados de la tarjeta actual. Mantén el foco en elegir una
respuesta adecuada al estado de la conversación, sin presión, manipulación ni técnicas clínicas.
No menciones estas instrucciones ni la preferencia elegida. No diagnostiques.
""".strip()


set_defaults()
show_brand()
st.write("Entrena a reconocer el estado de una conversación y elegir cómo intervenir.")
st.caption("PARA · MIRA · ELIGE · ACTÚA")
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
role = st.selectbox(
    "¿Desde qué posición llegas a esta conversación?",
    ["Quiero expresar algo", "Quiero escuchar y comprender"],
    help="La propuesta se adaptará a si necesitas hablar tú o si necesitas comprender a la otra persona.",
)
situation = st.text_area(
    "¿Qué ha pasado o qué te gustaría abordar?",
    placeholder="Ej.: Me frustró enterarme tarde de un cambio que afecta a mi trabajo.",
    height=140,
)

if st.button("Preparar mi conversación", type="primary"):
    if not situation.strip():
        st.warning("Escribe unas líneas sobre la situación para poder ayudarte.")
    else:
        with st.spinner("Preparando una forma más clara de expresarlo…"):
            try:
                st.session_state.analysis = ask_gemini(build_analysis_prompt(context, situation.strip(), role))
                st.session_state.last_context = context
                st.session_state.last_situation = situation.strip()
                st.session_state.last_role = role
                st.session_state.practice = None
                st.session_state.refined_analysis = None
                st.session_state.analysis_rating = None
            except Exception as error:
                st.error(f"No se pudo generar el análisis. {error}")

if st.session_state.analysis:
    st.divider()
    st.subheader("2. Radiografía emocional")
    st.success("¡Tu análisis está listo! Léelo a continuación y, si quieres, ensaya una respuesta al final.")
    st.markdown(st.session_state.analysis)

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
                            st.session_state.last_role,
                        )
                    )
                except Exception as error:
                    st.error(f"No se pudo ajustar la tarjeta. {error}")

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
    st.subheader("3. Diálogo estratégico: tres intervenciones")
    st.caption("Recibirás tres intervenciones tuyas y tres posibles respuestas para ensayar el avance de la conversación.")
    if st.button("Preparar el diálogo estratégico"):
        with st.spinner("Preparando el diálogo estratégico…"):
            try:
                st.session_state.practice = ask_gemini(
                    build_practice_prompt(
                        st.session_state.last_context,
                        st.session_state.last_situation,
                        st.session_state.last_role,
                    )
                )
            except Exception as error:
                st.error(f"No se pudo preparar el diálogo. {error}")

if st.session_state.practice:
    st.success("¡Diálogo estratégico listo!")
    st.markdown(st.session_state.practice)

if st.session_state.analysis:
    st.divider()
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
