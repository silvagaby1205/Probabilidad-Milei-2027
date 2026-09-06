# Probabilidad implícita de reelección — Milei 2027

Calcula día a día, desde cuatro ángulos distintos, la probabilidad que el
mercado le asigna a la reelección de Milei en 2027. Metodología completa
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

   Revisá el log de cada paso. El único que usa tus credenciales es el de
   bonos; los otros tres (ICG, Polymarket, spot) son APIs públicas sin login.

6. A partir de ahí, corre solo todos los días hábiles a las 18:00 ART.

## Estructura

```
index.html                   → el sitio (no necesita build, es HTML plano)
data/history.json            → serie del modelo de bonos (forward)
data/icg_history.json        → serie del ICG de la UTDT, un registro por mes publicado
data/polymarket_history.json → serie diaria del precio de Polymarket
data/spot_history.json       → serie diaria del método spot (Marull/FMyA)
calc/calc.py                 → forward de bonos (necesita IOL_USER / IOL_PASS)
calc/icg_calc.py             → chequeo diario del ICG (solo escribe si UTDT publicó algo nuevo)
calc/polymarket_calc.py      → precio diario de Polymarket
calc/spot_calc.py            → riesgo país spot del día, con los anclajes de Marull
.github/workflows/           → la automatización (corre los cuatro scripts todos los días)
```

Solo `calc.py` necesita Secrets (tus credenciales de IOL). Los otros tres
usan APIs públicas sin autenticación:
- ICG y riesgo país spot: [ArgentinaDatos](https://argentinadatos.com/docs.html) (`api.argentinadatos.com`)
- Polymarket: Gamma API (`gamma-api.polymarket.com`)

De estos dos, **Polymarket es el que menos pude verificar en vivo** — no
pude confirmar de antemano el slug exacto del evento ni el formato final de
la respuesta. Si falla en la primera corrida, el script imprime lo que sí
encontró para ajustar el filtro en un par de minutos.

## Ajustar los supuestos de cada modelo

- `MILEI_ANCHOR_BPS` / `PERONISMO_ANCHOR_BPS` en `calc/calc.py`: anclajes del modelo de bonos (250 / 2.000 pb).
- `MILEI_ANCHOR` / `MODERADO_ANCHOR` / `EXTREMO_ANCHOR` en `calc/spot_calc.py`: anclajes del método spot, siguiendo la lámina de Marull/FMyA (200 / 800 / 2.000 pb).

El sitio también deja mover los anclajes del modelo de bonos con sliders,
pero solo para explorar — el valor que queda guardado en el histórico es
siempre el que define el script.
