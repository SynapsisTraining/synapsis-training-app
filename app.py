import os
from pathlib import Path

import streamlit as st
from google import genai


APP_DIR = Path(__file__).parent
DEFAULT_MODEL = "gemini-3.5-flash-lite"
FUNDAMENTAL_PRINCIPLE = """
Principio fundamental e irrenunciable: una cosa es lo que sucede —el hecho observable, las palabras
concretas o la conducta verificable— y otra distinta es lo que una persona interpreta, supone o
construye con su pensamiento sobre ello. Separa siempre ambas capas. No presentes una interpretación,
emoción, intención o necesidad como si fuera un hecho; nómbrala como experiencia propia o posibilidad.
""".strip()
BASE_METHOD_GUIDE = """
COMUNICACIÓN BENEVOLENTE — Arquitectura 1.1

No es una secuencia rígida: enseña a reconocer el estado de una interacción y elegir
la respuesta más adecuada.

PARA: crea espacio antes de reaccionar.
MIRA: distingue hechos, tu experiencia y la posible experiencia de la otra persona.
ELIGE: decide qué necesita la interacción ahora.
ACTÚA: expresa, escucha o repara.

Principio fundamental: lo que sucede (hecho observable) es diferente de lo que interpreto y construyo
con mi pensamiento sobre ello. Primero se observa; después se formula la interpretación como una
posibilidad, no como una certeza.

Principios: me comprendo, me expreso y te comprendo.
Competencias observables: regulación, autocomprensión, expresión, escucha,
discriminación, estrategia y reparación.

Regla central antes de intervenir: observar antes de juzgar, comprender antes de
responder, expresar antes de acusar y pedir antes de exigir. Se traduce siempre en:
Observar → Comprender → Expresar → Pedir.

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


def build_analysis_prompt(
    context: str, situation: str, role: str, expression_purpose: str = ""
) -> str:
    role_guidance = (
        "La persona quiere expresar algo propio. Prioriza una expresión clara, una petición o un límite "
        "cuando sea adecuado."
        if role == "Quiero expresar algo"
        else "La persona quiere escuchar y comprender. Prioriza presencia, preguntas abiertas, paráfrasis "
        "y aclaración antes de dar su propia posición."
    )
    text_origin = (
        "Lee el texto como una formulación que la persona quiere expresar o ya ha expresado. No digas que "
        "ha recibido ese mensaje ni atribuyas esas palabras a la otra persona."
        if role == "Quiero expresar algo"
        else "Lee el texto como un mensaje o conducta de la otra persona que la persona quiere comprender."
    )
    purpose_guidance = (
        f"""Antes de redactar, ten en cuenta estas respuestas de la persona sobre lo que espera
conseguir al expresarse:
---
{expression_purpose}
---
Úsalas como brújula para la elección, la intervención y la tarjeta. No las repitas literalmente ni
conviertas el deseo de la persona en una exigencia hacia la otra."""
        if role == "Quiero expresar algo" and expression_purpose.strip()
        else ""
    )
    meaning_section = (
        """## 🗣️ ¿Cómo podría recibirlo la otra persona?
Explica primero, de forma breve, el sentido explícito de la frase que la persona quiere expresar.
Después describe cómo podría sentirse quien la lee o escucha y qué necesidad podría activarse en esa
persona. Enumera de dos a cuatro parejas posibles de emoción y necesidad (por ejemplo: «podría
sentirse presionada → podría necesitar seguridad»). Usa siempre formulaciones prudentes: son efectos
posibles del mensaje, no una lectura de la mente. Incluye un «Índice de agresividad de la interacción:
X/10», basado solo en el lenguaje, los hechos y la tensión descritos; nunca califiques a una persona.
Añade la activación Verde, Amarillo o Rojo como orientación para el ritmo."""
        if role == "Quiero expresar algo"
        else """## 🪞 ¿Qué podría estar sintiendo al leer o escuchar esto?
Explica primero, de forma breve, las palabras o hechos observables que ha comunicado la otra persona.
Después describe qué podría estar sintiendo la persona consultante al leer o escuchar ese mensaje y
qué necesidad propia podría activarse. Enumera de dos a cuatro parejas posibles de emoción y necesidad
(por ejemplo: «podrías sentirte inquieta → podrías necesitar claridad»). Usa formulaciones prudentes:
son posibilidades para que la persona se reconozca, no una interpretación cerrada ni un diagnóstico.
Incluye un «Índice de agresividad de la interacción: X/10», basado solo en el lenguaje, los hechos y
la tensión descritos, y la activación Verde, Amarillo o Rojo como orientación para el ritmo. Si falta
información, dilo y formula una pregunta abierta útil."""
    )
    benevolent_alternatives = (
        """## 🔎 Señales en mi expresión
Revisa la formulación en cinco dimensiones: **acusación**, **victimismo**, **declinación de
responsabilidad**, **reproche** y **falta de intención de mejora**. Para cada una indica «presente»,
«posible» o «no observable» y ofrece una justificación muy breve basada en palabras concretas del
texto. Entiende «victimismo» solo como una posible expresión de impotencia o de poner todo el peso
fuera de uno mismo, nunca como etiqueta de la persona. Entiende «declinación de responsabilidad» como
evitar reconocer la propia parte de elección o contribución, no como obligar a asumir culpas ajenas.

## 🌿 Tres alternativas más benevolentes
Si alguna de esas señales está presente o es posible, ofrece **al menos tres** versiones alternativas
que mantengan el asunto importante, el límite o la petición, pero reduzcan la agresividad. Titúlalas
«1. Serena y directa», «2. Cercana y empática» y «3. Firme con límites». No las presentes como frases
mágicas: explica en una línea qué cambia cada una. Si todas las señales son «no observable» y la
formulación ya es clara y benevolente, indica brevemente que no es necesario reformularla y no
inventes un problema. En las alternativas usa de forma natural, repartidos entre ellas, estos términos:
«entiendo», «comprendo», «observo», «deseo», «respeto», «ofrezco», «me comprometo» y «mejorar».
Mantén el sentido del mensaje: no uses esas palabras solo como adorno ni elimines un límite legítimo."""
        if role == "Quiero expresar algo"
        else ""
    )
    return f"""
Eres el facilitador de Synápsis, una herramienta educativa de entrenamiento para conversaciones
difíciles. Enseñas a reconocer el estado de una interacción y elegir una respuesta adecuada,
no a encontrar una frase perfecta. No diagnostiques ni asumas intenciones. Si aparece peligro,
violencia, amenazas o control, prioriza seguridad y apoyo local de confianza.

{FUNDAMENTAL_PRINCIPLE}

Aplica fielmente este método Synápsis:
---
{method_guide()}
---

Entorno: {context}
Posición desde la que llega: {role}
Orientación para esta práctica: {role_guidance}
Regla de lectura del texto: {text_origin}
{purpose_guidance}
Situación o mensaje de la persona:
---
{situation}
---

Responde en español, con calidez y precisión. No repitas el relato. Usa exactamente estos
apartados Markdown:

{meaning_section}
{benevolent_alternatives}
## 🛑 PARA
Indica qué reacción automática conviene detener y cuál es el avance más seguro ahora.
## 🧩 Antes de intervenir
Aplica de forma breve y explícita esta secuencia:
- **Observar:** separa un hecho o unas palabras concretas de cualquier interpretación.
- **Comprender:** formula qué podría estar viviendo o necesitando la otra persona, como posibilidad.
- **Expresar:** nombra en primera persona el impacto, emoción o necesidad propia, sin acusar.
- **Pedir:** propone una petición concreta, posible y libre de presión; no una exigencia.
## 🧭 ELIGE
Elige una sola acción entre: escuchar, aclarar, expresar, negociar, poner un límite, detenerse o
reparar. Explica en una frase por qué esa es la necesidad de la interacción ahora.
## 💬 ACTÚA
Propón una intervención breve, realista y en primera persona que ejecute la acción elegida. Cuando
corresponda, incluye una petición concreta y libre de presión. Si el estado es Rojo, ofrece una pausa
segura: no intentes resolver el contenido del conflicto.
## 💳 Tarjeta de conversación
Reúne una propuesta breve y usable para esta situación: una frase de inicio, una pregunta abierta
o escucha útil cuando corresponda, y un posible siguiente paso. Mantén claridad, respeto y límites
sanos; adapta la tarjeta a la posición desde la que llega la persona. Si hay una petición, debe ser
concreta, posible y permitir una respuesta libre.
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
        "Las seis fases deben ayudar a expresar con claridad, sin perder escucha ni respeto."
        if role == "Quiero expresar algo"
        else "Las seis fases deben ayudar a escuchar y comprender primero, sin asumir ni interrogar."
    )
    return f"""
Eres el facilitador de Synápsis. Diseña un diálogo estratégico breve de seis fases, con una
intervención de la persona y una posible réplica del interlocutor en cada fase. Su función es abrir
alternativas y avanzar con claridad, nunca convencer, presionar ni manipular. Contexto: {context}. Situación: {situation}.
Posición de la persona: {role}. {role_guidance}

{FUNDAMENTAL_PRINCIPLE}

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
## 4. Simplificar para avanzar — principios de diseño de Maeda
**Tú:** reduce el asunto a una sola cuestión importante, organiza lo esencial y formula una pregunta
o propuesta sencilla. Evita añadir detalles, reproches o soluciones múltiples; la simplicidad debe
dar claridad, no ocultar lo importante.
**La otra persona podría responder:** una réplica verosímil.
## 5. Conectar desde la persona — psicología humanista de Rogers
**Tú:** muestra empatía, congruencia y respeto incondicional por la persona sin aprobar una conducta
dañina. Nombra de manera prudente lo que parece importante para ella y expresa tu posición con
autenticidad.
**La otra persona podría responder:** una réplica verosímil.
## 6. Desescalar antes de resolver — Doug Noll
**Tú:** si hay intensidad, deja de discutir el contenido por un momento y refleja la emoción posible
en una frase breve de segunda persona, sin diagnosticar ni decir que sabes lo que siente (por ejemplo:
«Parece que esto te ha hecho sentir muy frustrado»). Después ofrece una pausa o una pregunta que
reduzca la tensión. Si no hay intensidad, usa esta fase para prevenir la escalada con una validación
breve y volver al propósito.
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

{FUNDAMENTAL_PRINCIPLE}

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
st.write("Mejorar nuestra comunicación es mejorar nuestras relaciones, nuestro trabajo, nuestra vida.")
st.caption("Observar · Comprender · Expresar · Pedir  |  PARA · ELIGE · ACTÚA")
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
expression_purpose = ""
situation = st.text_area(
    "¿Qué ha pasado o qué te gustaría abordar?",
    placeholder="Ej.: Me frustró enterarme tarde de un cambio que afecta a mi trabajo.",
    height=140,
)
if role == "Quiero expresar algo":
    st.markdown("#### Después de escribirlo: ¿qué esperas conseguir?")
    st.caption("Estas tres preguntas son opcionales; sirven para orientar tu propuesta con más claridad.")
    purpose_understanding = st.text_input(
        "1. ¿Qué te gustaría que la otra persona comprendiera?",
        key="purpose_understanding",
    )
    purpose_next_step = st.text_input(
        "2. ¿Qué cambio, decisión o siguiente paso te gustaría abrir?",
        key="purpose_next_step",
    )
    purpose_care = st.text_input(
        "3. ¿Qué quieres cuidar al decirlo?",
        placeholder="Por ejemplo: el respeto, la relación, un límite o la confianza.",
        key="purpose_care",
    )
    expression_purpose = (
        f"1. Que comprenda: {purpose_understanding or 'Sin respuesta.'}\n"
        f"2. Siguiente paso: {purpose_next_step or 'Sin respuesta.'}\n"
        f"3. Lo que quiero cuidar: {purpose_care or 'Sin respuesta.'}"
    )

if st.button("Preparar mi conversación", type="primary"):
    if not situation.strip():
        st.warning("Escribe unas líneas sobre la situación para poder ayudarte.")
    else:
        with st.spinner("Preparando una forma más clara de expresarlo…"):
            try:
                st.session_state.analysis = ask_gemini(
                    build_analysis_prompt(context, situation.strip(), role, expression_purpose)
                )
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
    analysis_question = (
        "¿Cómo podría recibirlo la otra persona?"
        if st.session_state.last_role == "Quiero expresar algo"
        else "¿Qué podría estar sintiendo al leer o escuchar esto?"
    )
    st.subheader(f"2. {analysis_question}")
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

if st.session_state.refined_analysis:
    st.divider()
    st.subheader("Tarjeta ajustada")
    st.markdown(st.session_state.refined_analysis)

if st.session_state.analysis:
    st.divider()
    st.subheader("3. Diálogo estratégico: seis fases")
    st.caption("Recibirás seis intervenciones tuyas y seis posibles respuestas para ensayar el avance de la conversación.")
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
    st.caption("Tu conversación y esta valoración no se guardan: se eliminan al recargar la página.")
    rating = st.session_state.analysis_rating
    helpful_col, improve_col = st.columns(2)
    if helpful_col.button("👍 Me ha servido", key="helpful_feedback", disabled=rating is not None):
        st.session_state.analysis_rating = 1
        rating = 1
    if improve_col.button("👎 Necesito otro enfoque", key="improve_feedback", disabled=rating is not None):
        st.session_state.analysis_rating = 0
        rating = 0

    if rating is not None:
        feedback_message = "Gracias por indicarlo." if rating == 1 else "Gracias por indicarlo: puedes ajustar la tarjeta o preparar otra conversación."
        st.caption(feedback_message)

    st.download_button(
        "Descargar mi tarjeta (Markdown)",
        data=st.session_state.refined_analysis or st.session_state.analysis,
        file_name="tarjeta_conversacion_synapsis.md",
        mime="text/markdown",
    )
    st.markdown("#### ¿Quieres compartir una sugerencia?")
    st.caption("Solo se enviará lo que tú decidas escribir en el correo.")
    st.link_button(
        "✉️ Enviar una sugerencia",
        "mailto:jgledo@gmail.com?subject=Sugerencia%20para%20Syn%C3%A1psis%20Training&body=Hola%2C%20me%20gustar%C3%ADa%20compartir%20esta%20sugerencia%3A%0A%0A",
    )
