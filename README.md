# Entrega 2 · Preparación e indicadores del discurso parlamentario

Infraestructura mínima para el dataset de la Entrega 1: RoBERTuito, LDA y MATTR,
con agregación mensual y mensual por partido. Las legislaturas son opcionales.
No incluye NER, comparación de modelos ni formulación anticipada de hipótesis.

## 1. Instalación

Python **3.11 o 3.12**. Ejecutar dentro de esta carpeta. Ejemplo para Linux, macOS
o WSL (en Windows, activar el entorno con `.venv\Scripts\activate`):

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
```

Para CPU en Linux/Windows, instalar primero esta variante de PyTorch:

```bash
python -m pip install torch==2.6.0 --index-url https://download.pytorch.org/whl/cpu
```

En macOS, usar `python -m pip install torch==2.6.0`. Para una GPU NVIDIA,
instalar la variante de PyTorch 2.6.0 compatible con CUDA según sus
[instrucciones oficiales](https://pytorch.org/get-started/previous-versions/#v260).
El código usa CUDA cuando está disponible y CPU en los demás casos.

```bash
python -m pip install -r requirements.txt
python -m pip install https://github.com/explosion/spacy-models/releases/download/es_core_news_sm-3.8.0/es_core_news_sm-3.8.0-py3-none-any.whl
```

La primera ejecución necesita Internet para descargar el dataset y RoBERTuito.
Los textos permanecen locales durante el cálculo de los indicadores.
La inferencia sobre todas las intervenciones es el paso más costoso, especialmente
en CPU. Si falta memoria de GPU, reducir `sentiment_batch_size` en `config.json`.

## 2. Ejecución

```bash
python preparar.py
python indicadores.py
python agregar.py
```

Para añadir las dos tablas por legislatura, ejecutar el último paso así:

```bash
python agregar.py --legislaturas
```

Si se cambia el número de tópicos o la ventana de MATTR, se puede conservar
el sentimiento ya calculado:

```bash
python indicadores.py --solo topicos
python agregar.py --legislaturas
```

También existe `python indicadores.py --solo sentimiento`. Si se vuelve a preparar
el corpus con otras transformaciones, hay que recalcular ambos bloques. Una huella
SHA-256 impide combinar indicadores de distintas preparaciones. Cada paso
sobrescribe sus salidas; no reanuda una inferencia parcialmente interrumpida.

## 3. Qué hace cada archivo

| Archivo | Función |
|---|---|
| `config.json` | Revisiones de datos/modelo y parámetros |
| `preparar.py` | Descarga, validación, limpieza, frases y lemas |
| `indicadores.py` | Sentimiento, distribución LDA y MATTR por turno |
| `agregar.py` | Tablas mensuales, por partido y gráficos; legislaturas opcionales |
| `common.py` | Rutas, configuración y comprobación de procedencia |
| `data_cleaning.md` | Reglas de limpieza y resumen automático tras preparar |
| `motivation.md` | Objetivo, justificación y limitaciones; hipótesis pendientes |

## 4. Datos y decisiones de cálculo

Se utiliza exclusivamente la configuración `default` de
[adrirana/political-corpus-es](https://huggingface.co/datasets/adrirana/political-corpus-es):
`data/raw/political_corpus_es.parquet`, fijada a una revisión concreta en la
configuración. Son 10.000 turnos de la muestra publicada, no el corpus completo.
Se conservan todos los metadatos y el texto original. `party` representa la familia
de partido asignada por la fuente; no se reconstruye la militancia de los oradores.

- **Volumen:** número de turnos conservados por mes y por mes × partido.
  Se incluyen los turnos que requieren revisión lingüística. Un cero significa
  que no hay registros en la muestra para esa combinación, no que no hubiera
  actividad parlamentaria. Las demás métricas quedan vacías donde no se pueden calcular.
- **Sentimiento:** checkpoint
  [`pysentimiento/robertuito-sentiment-analysis`](https://huggingface.co/pysentimiento/robertuito-sentiment-analysis),
  con revisión fija. Recibe frases con puntuación, negaciones y palabras funcionales.
  Su límite real es 128 tokens: las frases largas se dividen sin solapamiento ni
  pérdida del final. Se recombinan sus fragmentos ponderando por tokens de contenido;
  después se promedian las frases de cada turno. La clase de una frase es la
  probabilidad máxima. La puntuación del turno es `p_pos - p_neg`, entre −1 y 1.
- **LDA:** un solo modelo global para comparar los mismos tópicos a lo largo del
  tiempo. Usa conteos de lemas, sin stopwords, y devuelve una mezcla por turno.
  Se inicia con **12 tópicos**, 10 iteraciones, `min_df=5`, `max_df=0.8`, vocabulario
  máximo de 15.000 términos y semilla 42. Son parámetros iniciales configurables,
  no una selección de un número óptimo de temas. No se entrena un LDA por mes.
- **MATTR:** media de la proporción tipos/tokens sobre ventanas consecutivas de
  **50 lemas**, conservando stopwords. Se calcula dentro de cada intervención;
  las intervenciones con menos de 50 tokens válidos quedan sin valor. No se
  concatenan oradores, meses ni partidos para calcularla.
- **Agregación:** cada turno aporta el mismo peso dentro de su grupo. El sentimiento,
  las proporciones de clase, MATTR y la mezcla LDA se promedian sobre los turnos
  con valor disponible para cada indicador. Las legislaturas se agregan directamente
  desde los turnos, sin promediar medias mensuales.

## 5. Salidas

`data/processed/` se entrega inicialmente preparada y vacía. Al ejecutar se generan:

| Archivo | Contenido |
|---|---|
| `corpus_clean.parquet` | Texto original/limpio, frases, lemas, tokens LDA, metadatos y banderas |
| `sentiment.parquet` | Probabilidades, proporciones de clase, puntuación y número de frases/fragmentos |
| `topics_mattr.parquet` | MATTR y mezcla de tópicos por turno |
| `interventions_indicators.parquet` | Unión de los datos preparados con todos los indicadores |
| `monthly.csv` | Series mensuales globales |
| `monthly_party.csv` | Series mensuales por partido |
| `legislature.csv` | Resumen por legislatura, opcional |
| `legislature_party.csv` | Resumen por legislatura y partido, opcional |

En los CSV agregados:

| Columnas | Interpretación |
|---|---|
| `n_turns`, `n_sessions`, `n_speakers` | Cobertura observada; los oradores sin nombre no cuentan en el último campo |
| `n_sentiment`, `n_mattr`, `n_topics` | Denominadores efectivos de cada indicador |
| `sentiment` | Media de `p_pos - p_neg` por turno |
| `p_neg`, `p_neu`, `p_pos` | Media de las probabilidades por turno |
| `share_neg`, `share_neu`, `share_pos` | Media de las proporciones de frases clasificadas en cada clase por turno |
| `mattr` | Media de MATTR por turno |
| `topic_00`… | Proporción media de cada tópico; suman 1 cuando hay estimación |
| `coverage` | `con_registros` o `sin_registros_en_muestra` |

En `reports/` quedan los registros de limpieza y ejecución, `review_texts.csv`,
`excluded_invalid.csv`, la lista exacta de stopwords y cuatro PNG: indicadores
mensuales globales/por partido y mapas de proporciones de tópicos globales/por partido.
En los mapas el gris indica ausencia de estimación.

Para interpretar los tópicos, consultar `topic_labels.csv` (15 términos por tema)
y `topic_examples.csv` (tres turnos representativos, fragmento y enlace a la fuente).
Al recalcular LDA se regeneran esas etiquetas. El modelo y su vocabulario se
guardan en `models/lda.joblib`.

Los archivos de datos, modelos y gráficos se excluyen de Git por defecto; deben
incorporarse al paquete de entrega final una vez generados. No se distribuyen
resultados de comprobación como si fueran resultados del corpus.

## Procedencia

González, A., Hamberg, J., Somolinos, L., Blanco, A. y Sancho, H. (2026).
*political-corpus-es: Intervenciones del Pleno del Congreso de los Diputados
(2016–2026)* [Dataset]. Hugging Face. Compilación CC BY 4.0; textos del Congreso
de los Diputados. Se conservan los enlaces y fechas de recuperación de la fuente.

Referencias de implementación:
[RoBERTuito](https://huggingface.co/pysentimiento/robertuito-sentiment-analysis),
[spaCy español](https://spacy.io/models/es),
[LDA de scikit-learn](https://scikit-learn.org/stable/modules/generated/sklearn.decomposition.LatentDirichletAllocation.html).
