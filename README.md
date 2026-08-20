# Synápsis — Ensaya antes de decirlo

Una primera versión de una app de Streamlit para preparar conversaciones difíciles y ensayarlas con Gemini.

## 1. Antes de empezar

Necesitas Python 3.10 o posterior y una clave de Gemini API creada en [Google AI Studio](https://aistudio.google.com/app/apikey).

## 2. Instalar y configurar

Desde esta carpeta, crea un entorno virtual e instala las dependencias:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Copia el archivo de ejemplo de secretos y añade tu clave. Nunca subas ese archivo a Git ni la pegues en el código:

```bash
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
```

Abre `.streamlit/secrets.toml` y reemplaza `pega_aqui_tu_clave` por tu clave real.

## 3. Probar la app

```bash
streamlit run app.py
```

Se abrirá una dirección local en el navegador. Si tienes `Logotipo.jpeg`, déjalo junto a `app.py`; si no, la app muestra el título con el icono.

## 4. Publicarla en Streamlit Community Cloud

1. Sube estos archivos a un repositorio privado o público de GitHub, excluyendo `.streamlit/secrets.toml`.
2. En [Streamlit Community Cloud](https://share.streamlit.io/), crea una nueva app y elige el repositorio y `app.py`.
3. En la configuración de la app, abre **Secrets** y pega:

   ```toml
   GEMINI_API_KEY = "tu_clave_real"
   GEMINI_MODEL = "gemini-3.5-flash-lite"
   ```

4. Guarda y despliega. La app se reiniciará con la clave protegida.

## Decisiones de esta versión

- La clave solo se lee desde secretos o una variable de entorno; no queda en el código.
- El modelo se puede cambiar mediante `GEMINI_MODEL`, sin modificar la aplicación.
- El resultado se organiza como tarjeta de conversación y ofrece un ensayo posterior.
- Incluye límites explícitos: no es terapia ni sustituye atención de emergencia.
