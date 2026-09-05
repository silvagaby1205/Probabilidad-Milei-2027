# Probabilidad implícita de reelección — Milei 2027

Calcula día a día, a partir de tasas forward de bonos soberanos, la probabilidad
que el mercado le asigna a la reelección de Milei en 2027. Metodología completa
explicada en el propio sitio (`index.html`).

## Puesta en marcha (una sola vez)

1. **Creá el repo en GitHub** y subí estos archivos tal cual están (mantené las carpetas `.github/`, `calc/` y `data/`).

2. **Activá la API en tu cuenta de IOL**, si todavía no lo hiciste:
   Mi Cuenta → Personalización → APIs, aceptar los términos.

3. **Cargá tus credenciales como Secrets del repo** (nunca en el código):
   Settings → Secrets and variables → Actions → New repository secret
   - `IOL_USER`: tu usuario de InvertirOnline
   - `IOL_PASS`: tu contraseña de InvertirOnline

4. **Activá GitHub Pages**:
   Settings → Pages → Source: "Deploy from a branch" → rama `main`, carpeta `/ (root)`.
   Te va a quedar publicado en `https://<tu-usuario>.github.io/<repo>/`.

5. **Corré el workflow manualmente la primera vez** para verificar que todo
   funciona antes de dejarlo en automático:
   Actions → "Actualización diaria de probabilidad" → Run workflow.

   Revisá el log. Si algo falla, lo más probable es que sea uno de estos dos
   puntos (están marcados con un comentario en `calc/calc.py`):
   - El nombre del campo de precio que devuelve el endpoint de cotización de IOL.
   - El nombre de los campos de la curva UST en el feed de treasury.gov.

   El script imprime la respuesta cruda en el error si alguno de los dos falla,
   así que se ajusta rápido.

6. A partir de ahí, corre solo todos los días hábiles a las 18:00 ART y va
   sumando un punto por día a `data/history.json`, que es lo que lee el sitio.

## Estructura

```
index.html                  → el sitio (no necesita build, es HTML plano)
data/history.json           → serie histórica del modelo de bonos (la actualiza el workflow)
data/icg_history.json       → serie del ICG de la UTDT, un registro por mes publicado
data/polymarket_history.json → serie diaria del precio de Polymarket
calc/calc.py                → el cálculo diario del forward de bonos
calc/icg_calc.py            → el chequeo diario del ICG (solo escribe si UTDT publicó algo nuevo)
calc/polymarket_calc.py     → el precio diario de Polymarket
.github/workflows/          → la automatización (corre los tres scripts todos los días)
```

`calc/icg_calc.py` y `calc/polymarket_calc.py` no necesitan ningún Secret
nuevo — ambas fuentes son públicas. Son las piezas menos probadas de las
tres: no pude previsualizar en vivo ni el Excel de UTDT ni la respuesta
exacta de la API de Polymarket, así que en la primera corrida conviene
mirar el log de esos dos pasos puntuales. Si no encuentran el dato,
imprimen lo que sí encontraron para ajustar el filtro en un par de minutos.

## Ajustar los supuestos del modelo

`MILEI_ANCHOR_BPS` y `PERONISMO_ANCHOR_BPS` en `calc/calc.py` son los dos
escenarios de referencia (250 pb y 2.000 pb, siguiendo la convención de
GMA Capital / FMyA). Cambiarlos ahí cambia el dato que se guarda; el sitio
también deja moverlos con los sliders, pero solo para explorar — el valor que
queda guardado en el histórico es siempre el que define el script.
