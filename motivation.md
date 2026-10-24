# Motivación del proyecto

## Objetivo general

Preparar y explorar las intervenciones del Pleno del Congreso de los Diputados
incluidas en la Entrega 1 y construir indicadores mensuales de volumen, sentimiento,
distribución temática y diversidad léxica. Se pretende establecer una base
reproducible para estudiar posteriormente la relación entre el discurso
parlamentario y la polarización electoral en España.

En esta entrega el análisis es descriptivo. No se estima aún esa relación ni se
incorporan datos electorales. La unidad de observación es el turno de palabra;
las unidades principales de presentación son el mes y el mes por familia de
partido. La agregación por legislatura se ofrece como complemento.

## Preguntas de investigación e hipótesis

**Pendientes de la obtención e interpretación de los resultados**, conforme a la
decisión del grupo. No se presentan hipótesis como si ya estuvieran respaldadas
por datos. Tras inspeccionar las series, la cobertura y los tópicos, se completará
esta sección con al menos una hipótesis clara y verificable, tal como exige el
enunciado. Se indicarán las variables, el periodo y la dirección esperada.

## Justificación del dataset

Se reutiliza la muestra FAIR publicada como configuración `default` de
[political-corpus-es](https://huggingface.co/datasets/adrirana/political-corpus-es),
la misma de la primera entrega: 10.000 intervenciones entre 2016 y 2026, con texto,
fecha, orador, familia de partido, legislatura y procedencia oficial.

La fecha permite crear series mensuales. Los metadatos permiten contextualizar
los cambios por partido y legislatura, y los enlaces al Diario de Sesiones
permiten verificar interpretaciones. Se fija la revisión del dataset y se conserva
el texto original para mantener la trazabilidad.

## Justificación de los indicadores

- **Volumen mensual:** describe la cobertura observada y contextualiza el número
  de intervenciones sobre las que se calculan las demás métricas.
- **Sentimiento con RoBERTuito:** ofrece una clasificación predefinida en español
  (negativo, neutro y positivo), sin construir un clasificador propio. Se conservan
  probabilidades y proporciones de clase, junto con una puntuación media.
- **Tópicos con LDA:** permite explorar los temas que aparecen en el corpus
  mediante un modelo sencillo e interpretable. Un modelo global proporciona
  categorías comunes para comparar periodos y partidos. Los términos y ejemplos
  representativos apoyan la interpretación manual de cada tema.
- **Diversidad léxica con MATTR:** es el único indicador opcional elegido. Usa
  ventanas de longitud fija para reducir la dependencia directa de la longitud
  de los discursos, y se calcula sobre lemas para centrar la comparación en el
  vocabulario, conservando las palabras funcionales.

## Limitaciones y posibles sesgos

- La muestra se estratificó por mes y partido y excluye turnos cortos, la Mesa,
  otras formaciones y casos sin atribución suficientemente respaldada. No
  representa todo el discurso político ni todo el Parlamento. El volumen es un
  conteo de la muestra; no se extrapola sin pesos de muestreo verificados.
- Las familias de partido no son organizaciones idénticas a lo largo del tiempo:
  por ejemplo, Podemos-UP-Sumar agrupa formaciones distintas. Su composición y
  presencia cambian entre legislaturas.
- Los huecos de datos pueden corresponder a recesos, disoluciones o cobertura de
  la fuente. La ausencia de registros no implica sentimiento neutro ni ausencia
  de un tema. Los extremos de la serie incluyen meses incompletos.
- El tipo de debate, los asuntos tratados, la longitud de los turnos y el papel
  de Gobierno/oposición pueden cambiar las métricas sin que cambie la polarización.
- RoBERTuito fue desarrollado para lenguaje de redes sociales. La ironía, las
  citas, las negaciones complejas y el registro parlamentario pueden producir
  errores. Sus probabilidades no están calibradas para este corpus. El sentimiento
  negativo no mide directamente lenguaje polarizante ni polarización electoral.
- La división de frases largas conserva tokens, pero limita el contexto de cada
  fragmento. La segmentación de frases y la lematización pueden cometer errores.
- La detección conservadora de otras lenguas depende de las notas editoriales.
  Puede excluir turnos con traducción útil y no detectar otros pasajes multilingües.
  Se informa de las exclusiones y se conservan los originales para revisión.
- Los tópicos dependen de la limpieza, el vocabulario, el número de componentes y
  la inicialización; no son categorías objetivas. Deben revisarse con ejemplos.
- MATTR mide diversidad de lemas, no complejidad sintáctica. Las intervenciones
  demasiado cortas quedan fuera de ese cálculo. Las medias con pocos turnos
  pueden ser inestables; siempre se acompañan de sus denominadores.
- La ficha del dataset referencia metadatos de barómetros del CIS, pero estos
  no constituyen una serie de polarización electoral ya calculada. No se atribuye
  causalidad a las asociaciones que puedan explorarse en fases posteriores.

## Referencia del dataset

González, A., Hamberg, J., Somolinos, L., Blanco, A. y Sancho, H. (2026).
*political-corpus-es: Intervenciones del Pleno del Congreso de los Diputados
(2016–2026)* [Dataset]. Hugging Face. Compilación CC BY 4.0; textos del Congreso
de los Diputados.
