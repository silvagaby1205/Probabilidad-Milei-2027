# Probabilidad implícita de reelección de Milei a partir del mercado de bonos

**[Ver el sitio en vivo →](#)** *(reemplazar por la URL real de GitHub Pages)*

Indicador diario que utiliza tasas forward implícitas en bonos soberanos argentinos para estimar cuánto del riesgo electoral 2027 está incorporando el mercado. El modelo se actualiza automáticamente con datos de mercado y compara la señal de los bonos con Polymarket y otros enfoques.

**Esto no es una encuesta ni una predicción personal.** Es la transformación de una señal de mercado (el precio de los bonos) en un número interpretable, bajo supuestos explícitos que se pueden auditar y cuestionar.

En 30 segundos: qué mide, cómo, y con qué

| | |
|---|---|
| **Qué mide** | Riesgo país *forward* (2027–2028) convertido a probabilidad implícita, comparado contra Polymarket, riesgo país spot y el ICG de la UTDT |
| **Cómo** | Python calcula TIRs, tasas forward y probabilidades a partir de precios de bonos y curvas de tasas; corre solo, todos los días |
| **Con qué** | Python, GitHub Actions, 4 APIs públicas (IOL, U.S. Treasury, ArgentinaDatos, Polymarket Gamma), HTML/JS sin frameworks para el frontend |
| **Automatizado** | 100% — desde la obtención de precios hasta la publicación del dato, sin intervención manual |

---

## Origen de la metodología

La idea de usar la tasa forward entre los Bonares AO27 y AO28 para aislar el riesgo que el mercado le asigna al período electoral **no es original de este proyecto**. Es una metodología que circula en el análisis de mercado argentino desde 2025-2026, desarrollada y publicada por **GMA Capital** (el "trade electoral"), y replicada por otras consultoras con variantes propias (entre ellas Fernando Marull / FMyA, con un enfoque más simple basado en riesgo país spot).

Fuentes primarias:
- ["Cuál es la probabilidad de que Milei sea reelecto según el precio de los bonos"](https://www.infobae.com/economia/2026/08/24/cual-es-la-probabilidad-de-que-milei-sea-reelecto-segun-el-precio-de-los-bonos-los-numeros-de-una-financiera-local/) — Infobae, 24/08/2026
- ["El mercado ya mira 2027: la señal en los bonos que preocupa a Milei"](https://eleconomista.com.ar/finanzas/el-mercado-ya-mira-2027-senal-bonos-preocupa-milei-anticipa-una-eleccion-mas-pareja-n97782) — El Economista
- ["Riesgo país arriba de 500 puntos: la cronología de eventos"](https://www.cronista.com/finanzas-mercados/riesgo-pais-arriba-de-500-puntos-la-cronologia-de-eventos-que-explica-la-peor-racha-del-ano-para-los-bonos/) — El Cronista
- [Escenario alternativo de anclajes (217/1600 pb)](https://x.com/julianyosovitch/status/2096750297553264937) — Julián Yosovitch, con datos de Portfolio Personal Inversiones

**Lo que aporta este proyecto no es la metodología en sí, sino:**
- Reimplementación desde cero en Python, a partir de precios y curvas crudas (no de un número ya publicado)
- Automatización diaria end-to-end, sin intervención manual
- Reconstrucción histórica de la serie (mayo–agosto 2026), marcada explícitamente como estimada
- Comparación sistemática contra Polymarket, riesgo país spot (con dos variantes de rival) y el ICG de la UTDT
- Visualización pública, reproducible y con el código fuente auditable
- Exposición explícita de los supuestos (anclajes de escenario) como parámetros modificables, no como constantes ocultas

---

## Qué aporta el proyecto (para quien lo mire técnicamente)

Financial markets · Yield curves · Forward rates · Sovereign risk · Recolección de datos vía APIs públicas · Transformación y validación de datos · Automatización (GitHub Actions) · Visualización sin frameworks (SVG + JS) · Investigación reproducible

El objetivo del proyecto no fue desarrollar una nueva metodología electoral, sino convertir una metodología de mercado ya existente en un indicador reproducible, auditable y actualizado diariamente.

---

## Metodología

1. TIR de AO27C (vence 29/10/2027) y AO28C (vence 31/10/2028), a partir de precio y flujo de fondos real de cada bono
2. Tasa forward soberana implícita entre ambos vencimientos: `(1+y28)^t28 = (1+y27)^t27 · (1+f)^(t28−t27)`
3. Tasa forward de la curva UST para el mismo tramo, interpolada linealmente sobre CMT 1–2–3 años
4. Riesgo país forward implícito = forward soberano − forward libre de riesgo
5. Conversión a probabilidad mediante una interpolación lineal entre dos escenarios de referencia:

```
p = (RP_oposición − RP_forward) / (RP_oposición − RP_Milei)
```

Esto **no** es una probabilidad que salga directamente de los bonos — es una transformación de una señal de mercado bajo dos anclajes de escenario elegidos por el analista. Cambiar esos anclajes cambia el resultado; el modelo lo deja explícito en vez de esconderlo.

### Escenarios

| | RP si gana Milei | RP si gana la oposición | Probabilidad implícita hoy* |
|---|---|---|---|
| **Escenario base (GMA)** | 250 pb | 2.000 pb | 50,1% |
| **Escenario alternativo (Yosovitch/EMBI)** | 217 pb (≈ EMBI+ Global) | 1.600 pb | 34,4% |

*Con un riesgo país forward de referencia de 1.124 pb — el número exacto varía día a día; el sitio en vivo lo recalcula con el dato del momento.

Los 217 y 1.600 del escenario alternativo son referencias externas de mercado citadas por un analista financiero, no precios de mercado observables que por sí solos identifiquen una probabilidad objetiva — igual de subjetivos, en ese sentido, que los 250/2.000 del escenario base.

### Sensibilidad a los escenarios

La probabilidad no sale de los bonos: sale de dónde se ponen los dos anclajes. Con el mismo riesgo país forward (1.124 pb), moviendo únicamente los anclajes:

| Milei \ Oposición | 1.600 pb | 1.800 pb | 2.000 pb | 2.200 pb |
|---|---|---|---|---|
| 150 pb | 32,8% | 41,0% | 47,4% | 52,5% |
| 200 pb | 34,0% | 42,2% | 48,7% | 53,8% |
| 217 pb | 34,4% | 42,7% | 49,1% | 54,3% |
| 250 pb | 35,3% | 43,6% | 50,1% | 55,2% |
| 300 pb | 36,6% | 45,1% | 51,5% | 56,6% |

El sitio en vivo deja mover estos dos anclajes con sliders para explorar esto de forma interactiva.

---

## Comparador de señales

El sitio muestra cuatro formas distintas de extraer una señal electoral del mercado, más una quinta que no es una probabilidad:

| Señal | Qué es |
|---|---|
| Tasas forward (bonos) | El modelo principal de este proyecto |
| Polymarket | Precio de un mercado de predicción, incluye balotaje |
| Riesgo país spot vs. PJ extremo | Método de Fernando Marull/FMyA, con el riesgo país de hoy tal cual |
| Riesgo país spot vs. oposición moderada | Misma cuenta, con un rival menos extremo |

El objetivo de esta comparación **no es decidir cuál es "la correcta"**, sino mostrar cómo distintos supuestos y distintas fuentes de datos llevan a números distintos frente a la misma pregunta.

---

## Indicadores complementarios

**ICG (Índice de Confianza en el Gobierno, UTDT):** mide confianza en el gobierno, no intención de voto ni probabilidad electoral. Se muestra en el sitio como una serie separada, con una conversión aproximada a intención de voto (calibrada contra 13 elecciones pasadas), pero **deliberadamente no se mezcla** con los cuatro modelos de probabilidad de arriba.

---

## Limitaciones

- Prima por plazo, liquidez y convexidad de los bonos, no solo riesgo electoral
- El riesgo país soberano incorpora factores macroeconómicos y políticos simultáneamente, no exclusivamente electorales
- Diferencias de duración entre los bonos usados
- El resultado depende de los anclajes de escenario elegidos, que son una hipótesis del analista, no un dato de mercado
- Una tasa forward no equivale directamente a una probabilidad electoral "pura" — es una probabilidad implícita en precios, sujeta a todo lo anterior
- El tramo estimado de la serie histórica (mayo–agosto 2026) viene de leer un gráfico ya publicado, no de precios crudos propios

---

## Próximas extensiones (no implementadas — future work)

**Riesgo país vs. fundamentos.** [BondTerminal](https://bondterminal.com/sovereign-signal) construye un score de fundamentos soberanos a partir de nueve variables macro/fiscales/institucionales y lo compara contra spreads de bonos. La idea, si los datos lo permiten, sería mostrar el riesgo país observado, un benchmark de riesgo país asociado a fundamentos, y la brecha entre ambos — **sin llamar automáticamente a esa brecha "riesgo político"**, ya que puede incluir liquidez, percepción de riesgo, expectativas y otros factores no capturados por el modelo de fundamentos. BondTerminal usa una metodología propia, cuyo spread puede diferir del EMBI+ de JPMorgan; de implementarse, quedaría documentado como referencia externa, no como metodología propia.

**Electoral Stress Test (destrucción implícita de market cap).** Idea original de Juan I. Fernandez: tomar un escenario de riesgo país, recalcular el precio teórico de cada bono soberano bajo ese spread (bono por bono, porque la sensibilidad depende de duration, cupones y amortizaciones de cada título), multiplicar por el nominal en circulación, y comparar el market cap soberano resultante contra el actual — eventualmente extendido al Merval, si se puede definir una metodología rigurosa. No se van a inventar datos de market cap ni asumir una caída porcentual uniforme entre bonos.

---

## Conexión académica

Este proyecto forma parte de mi interés académico por la dinámica del riesgo país y por la utilización de información financiera para extraer expectativas del mercado. Estoy además desarrollando mi tesis de la Licenciatura en Economía sobre riesgo país — son dos trabajos distintos, pero que comparten motivación.

---

## Estructura del repositorio

```
index.html                   → el sitio (HTML/JS plano, sin build)
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

Tecnologías realmente usadas en el código (sin inflar la lista): Python 3 (`requests`, `zoneinfo`), JavaScript vanilla (sin frameworks), SVG generado dinámicamente para los gráficos, GitHub Actions para la automatización, GitHub Pages para el hosting.

## Puesta en marcha

1. Activá la API en tu cuenta de IOL: Mi Cuenta → Personalización → APIs.
2. Cargá `IOL_USER` e `IOL_PASS` como Secrets del repo (Settings → Secrets and variables → Actions). ICG, Polymarket y el spot usan APIs públicas, sin credenciales.
3. Activá GitHub Pages (Settings → Pages → Deploy from a branch → `main` → `/ (root)`).
4. Corré el workflow manualmente una vez (Actions → Run workflow) para confirmar que las cuatro fuentes de datos responden bien.
5. A partir de ahí, corre solo todos los días hábiles a las 18:00 ART.

---

## Resumen para LinkedIn

> Tomé una metodología de mercado ya existente —usar tasas forward entre bonos soberanos para aislar cuánto riesgo electoral está incorporando el precio de la deuda argentina, desarrollada originalmente por GMA Capital— y la convertí en un sistema automatizado: obtención diaria de datos vía APIs públicas, cálculo reproducible en Python, y comparación sistemática contra Polymarket, riesgo país spot y el ICG de la UTDT. El proyecto queda documentado con sus límites explícitos (los anclajes de escenario son hipótesis, no datos de mercado) y con el código fuente abierto para auditar cada paso. Todo corre solo, todos los días, vía GitHub Actions.
