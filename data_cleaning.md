# Preparación y limpieza

Este documento describe el proceso de preparación y limpieza aplicado al corpus de intervenciones parlamentarias utilizado en la Entrega 2. Las transformaciones se han ejecutado sobre las 10.000 intervenciones procedentes de la Entrega 1.

Se documentan los criterios de validación, normalización, tratamiento de registros problemáticos y generación de representaciones lingüísticas, junto con las estadísticas reales obtenidas durante la ejecución de `preparar.py`.

## Fuente y trazabilidad

Se descarga el Parquet de la configuración `default` del dataset
`adrirana/political-corpus-es`, fijado a la revisión de `config.json`.
Se conserva una copia en `data/raw/`. Cada intervención conserva `id`, texto
original, metadatos, enlaces y fechas de recuperación. El resultado se escribe
en `data/processed/corpus_clean.parquet`.

## Validación de registros

1. Se comprueba que estén las columnas necesarias.
2. Se eliminan únicamente filas completamente idénticas. Un ID repetido con
   contenido distinto detiene el proceso para evitar resolver el conflicto arbitrariamente.
   Dos turnos con IDs distintos y texto coincidente se conservan.
3. Se excluyen las fechas no interpretables como `AAAA-MM-DD`, legislaturas nulas
   y registros con ID, texto, partido o sesión vacíos. Se guardan en
   `reports/excluded_invalid.csv`.
4. Se deriva `month` desde la fecha de la sesión. No se inventa una hora.

## Limpieza conservadora del texto

- `text` no cambia; se crea `text_clean`.
- Se normaliza Unicode NFC y se compactan espacios. Se sustituyen exclusivamente
  siete caracteres de control procedentes de puntuación Windows-1252 por sus
  equivalentes tipográficos (puntos suspensivos, comillas y guiones).
- Se elimina la cabecera inicial del orador con el patrón «El/La señor/señora …:».
  También cubre las erratas «El señora» y «La señor». Una cabecera no reconocida
  activa `header_review`; no se intenta adivinar dónde empieza la intervención.
- Se eliminan por coincidencia literal las acotaciones presentes en
  `text_editorial_notes`, incluidas las interrupciones atribuidas a otros oradores.
  No se borran indiscriminadamente todos los paréntesis. Un JSON de acotaciones
  mal formado detiene el proceso para su revisión.
- Una nota que explicita intervención en catalán, euskera/vasco, gallego, bable,
  asturiano, aragonés o valenciano activa `language_review`. No se traduce ni se
  mezcla automáticamente el original con su traducción.
- Los turnos con revisión de cabecera/lengua o texto limpio vacío permanecen en
  el volumen, con `eligible_nlp=False`, y se listan en `reports/review_texts.csv`.
  Sus indicadores lingüísticos no se calculan. Esta detección por notas no garantiza
  encontrar todos los pasajes en otras lenguas; debe tenerse en cuenta al interpretar.

## Tres representaciones para tres usos

| Representación | Transformación | Uso |
|---|---|---|
| `sentences` | Segmentación con spaCy; conserva texto natural, negación y puntuación | RoBERTuito |
| `lemmas` | Tokens alfabéticos, lematización, minúsculas, `al → a el` y `del → de el`; conserva stopwords | MATTR |
| `topic_tokens` | Lemas anteriores sin stopwords ni fórmulas frecuentes de cortesía | LDA |

Se usa `es_core_news_sm` 3.8.0 con NER y parser desactivados; se añade
`sentencizer`. Las contracciones se descomponen solo en la representación léxica:
no se reescribe el texto enviado a RoBERTuito. Se conservan tildes y la ñ; no hay
stemming ni eliminación de nombres propios. MATTR excluye puntuación y números,
y mide diversidad de lemas. La descomposición mecánica de contracciones también
puede afectar a partículas homógrafas dentro de nombres propios.

La lista de stopwords parte de spaCy y añade `señor`, `señora`, `señoría`,
`presidente`, `presidenta` y `gracia`. Se preservan `no`, `ni`, `nunca`, `jamás`,
`tampoco` y `sin`. La lista exacta se guarda en `reports/stopwords_lda.txt`.

## Valores ausentes

MATTR queda sin valor cuando hay menos de 50 tokens válidos (ventana configurable).
Si el vocabulario de LDA elimina todos los términos de un turno, su mezcla queda
sin valor: no se inventa una distribución uniforme. Los CSV incluyen denominadores
para distinguir estas ausencias de valores reales. Los meses sin registros
no se interpolan; solo los conteos observados se muestran como cero.

<!-- RESUMEN_AUTOMATICO -->

## Resultado de la ejecución

```json
{
  "dataset": "adrirana/political-corpus-es",
  "revision": "3e0d9534eacd578c14c12a2b24dba0b9cdf0e2fc",
  "raw_rows": 10000,
  "exact_duplicates_removed": 0,
  "invalid_rows_excluded": 0,
  "retained_rows": 10000,
  "eligible_nlp": 9973,
  "language_review": 27,
  "header_review": 0,
  "date_min": "2016-08-30",
  "date_max": "2026-09-23",
  "spacy_version": "3.8.7",
  "spacy_model_version": "3.8.0"
}
```
## Interpretación de los resultados de limpieza

El proceso de validación conservó las 10.000 intervenciones originales, sin detectar duplicados exactos ni registros inválidos según los criterios establecidos.

De las intervenciones conservadas, 9.973 (99,73 %) fueron consideradas aptas para calcular indicadores lingüísticos. Las 27 restantes (0,27 %) quedaron señaladas para revisión por la detección de referencias a otras lenguas en sus anotaciones editoriales.

Estas intervenciones se mantienen en el corpus procesado para preservar la cobertura temporal y la trazabilidad de la muestra, pero se excluyen de los análisis lingüísticos automáticos. De esta forma, los indicadores de volumen siguen considerando la totalidad de las intervenciones válidas.

En el análisis de tópicos, el modelo LDA utilizó finalmente 9.972 intervenciones, dado que una de las inicialmente aptas quedó sin términos tras aplicar los filtros de vocabulario.

Los resultados de limpieza se almacenan en `data/processed/corpus_clean.parquet`, mientras que los registros señalados para revisión y las estadísticas complementarias se guardan en `reports/`.