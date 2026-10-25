# Motivación del proyecto

## 1. Objetivo general

El objetivo de este proyecto es preparar y explorar las intervenciones del Pleno del Congreso de los Diputados recogidas en el dataset FAIR desarrollado durante la Entrega 1, correspondientes al periodo 2016–2026.

A partir de este corpus, se construyen indicadores temporales de volumen de intervenciones, sentimiento, distribución temática y diversidad léxica, con el propósito de identificar patrones en la evolución del discurso parlamentario español.

La investigación pretende establecer una base reproducible para estudiar, en posteriores entregas, posibles relaciones entre las características del discurso parlamentario y la polarización electoral en España.

En esta segunda entrega el análisis es descriptivo. No se incorporan todavía medidas de polarización electoral ni se establecen relaciones causales.

La unidad de observación es cada turno de palabra. Los indicadores se agregan principalmente por mes y familia política, incorporando comparaciones por legislatura como análisis complementario.

## 2. Preguntas de investigación e hipótesis

El análisis exploratorio se plantea las siguientes preguntas:

- ¿Cómo evoluciona el sentimiento medio de las intervenciones parlamentarias entre 2016 y 2026?
- ¿Se observan diferencias en el sentimiento de las intervenciones de una misma familia política entre periodos de Gobierno y oposición?
- ¿Cómo varía la distribución de los principales tópicos parlamentarios entre partidos y legislaturas?
- ¿Presenta la diversidad léxica cambios relevantes a lo largo del periodo analizado?

### Hipótesis principal

**H1:** Las intervenciones de las familias políticas presentan, en promedio, puntuaciones de sentimiento más negativas durante los periodos en los que ejercen la oposición que durante aquellos en los que forman parte del Gobierno, dentro del intervalo 2016–2026.

**H0:** No existe una diferencia sistemática hacia puntuaciones más negativas en el sentimiento medio de las intervenciones durante los periodos de oposición respecto a los periodos de Gobierno.

### Variables y procedimiento de verificación

Para estudiar esta hipótesis se utilizan las siguientes variables:

- **Variable dependiente:** puntuación de sentimiento de cada intervención, obtenida mediante RoBERTuito.
- **Variable explicativa:** situación de la familia política en cada periodo, diferenciando Gobierno y oposición.
- **Variables de contextualización:** fecha, legislatura, familia política y número de intervenciones disponibles.

La puntuación de sentimiento se define como:

**Sentimiento = P(positivo) − P(negativo)**

Sus valores se encuentran entre −1 y 1, donde valores menores indican una mayor probabilidad relativa de sentimiento negativo.

La verificación requeriría identificar el papel de cada formación en los distintos periodos y comparar las puntuaciones de sentimiento entre etapas de Gobierno y oposición, preferiblemente dentro de una misma familia política.

En esta entrega se utilizan las agregaciones por mes, partido y legislatura para identificar patrones preliminares. No se incluye todavía una codificación sistemática de Gobierno/oposición para todas las intervenciones, por lo que la hipótesis queda formulada para su contraste posterior.

## 3. Justificación del dataset

Se reutiliza el dataset FAIR [political-corpus-es](https://huggingface.co/datasets/adrirana/political-corpus-es), publicado en Hugging Face durante la primera entrega.

El corpus contiene 10.000 intervenciones parlamentarias del Congreso de los Diputados correspondientes al periodo comprendido entre el 30 de agosto de 2016 y el 23 de septiembre de 2026.

Cada intervención incluye un identificador, contenido textual, fecha, información sobre el orador, familia política, legislatura y referencias a la fuente oficial.

Este conjunto de datos es adecuado para el estudio porque combina tres dimensiones fundamentales:

- **Temporal:** permite estudiar la evolución de los indicadores a lo largo de aproximadamente diez años.
- **Política:** permite comparar intervenciones de diferentes familias políticas y legislaturas.
- **Textual:** proporciona el contenido necesario para aplicar modelos de sentimiento, tópicos y diversidad léxica.

La procedencia oficial y los enlaces a los registros parlamentarios permiten mantener la trazabilidad de las observaciones.

Durante la preparación se conservaron las 10.000 intervenciones originales. De ellas, 9.973 fueron consideradas aptas para el análisis lingüístico y 27 quedaron señaladas para revisión por sus características lingüísticas.

Las transformaciones y exclusiones aplicadas están documentadas en `data_cleaning.md`. Los resultados se almacenan en `data/processed/`.

## 4. Justificación de los indicadores

### 4.1. Volumen temporal

Se calcula el número de intervenciones por mes, familia política y legislatura.

Este indicador permite contextualizar los resultados y determinar el número de observaciones disponibles en cada periodo.

Como la muestra está estratificada, los conteos representan la cobertura del corpus, no necesariamente el volumen total de actividad parlamentaria.

### 4.2. Análisis de sentimiento

Se utiliza el modelo preentrenado `pysentimiento/robertuito-sentiment-analysis`, que identifica sentimiento positivo, neutro y negativo en textos en español.

El análisis conserva las probabilidades de cada categoría y obtiene una puntuación continua de sentimiento por intervención.

Posteriormente, estas puntuaciones se agregan por intervalos temporales y familias políticas.

El indicador resulta especialmente relevante para explorar diferencias en el tono afectivo de las intervenciones entre periodos y partidos.

Sin embargo, el sentimiento negativo no constituye por sí mismo una medida directa de polarización política.

### 4.3. Distribución de tópicos

Se aplica Latent Dirichlet Allocation (LDA), utilizando representaciones lematizadas del texto y un vocabulario limitado a 15.000 términos.

El modelo identifica 12 tópicos y obtiene distribuciones temáticas para 9.972 intervenciones.

Los tópicos se interpretan mediante sus palabras representativas y ejemplos de intervenciones, asignando etiquetas descriptivas.

Sus proporciones se agregan temporalmente y por familia política para estudiar la evolución de los temas y sus posibles diferencias entre grupos.

### 4.4. Diversidad léxica

Como único indicador opcional se utiliza MATTR (*Moving-Average Type-Token Ratio*).

Se calcula sobre lemas mediante ventanas móviles de 50 tokens, lo que reduce parte de la dependencia de la longitud de las intervenciones.

Permite comparar la variedad del vocabulario entre periodos y familias políticas.

## 5. Resultados exploratorios

### 5.1. Cobertura temporal

El corpus conserva las 10.000 intervenciones iniciales, distribuidas entre las legislaturas XII, XIII, XIV y XV.

| Legislatura | Intervenciones |
|---|---:|
| XII | 2.797 |
| XIII | 129 |
| XIV | 3.779 |
| XV | 3.295 |

La legislatura XIII presenta una cobertura especialmente reducida, por lo que sus indicadores son menos estables.

Estos recuentos corresponden a las intervenciones de la muestra y no deben interpretarse como volúmenes totales de actividad parlamentaria.

### 5.2. Evolución del sentimiento

Las puntuaciones medias obtenidas mediante RoBERTuito son negativas en las cuatro legislaturas.

| Legislatura | Sentimiento medio |
|---|---:|
| XII | −0,208 |
| XIII | −0,271 |
| XIV | −0,308 |
| XV | −0,326 |

Se observa que las muestras correspondientes a las legislaturas posteriores presentan puntuaciones medias progresivamente más negativas.

Al examinar los resultados por familia política, también se identifican diferencias relevantes.

Por ejemplo, el Partido Popular presenta una puntuación media aproximada de −0,068 en la legislatura XII, frente a −0,410 y −0,406 en las legislaturas XIV y XV, respectivamente.

Este patrón resulta compatible con la hipótesis de que el papel de Gobierno u oposición puede estar relacionado con el sentimiento del discurso. Sin embargo, no permite generalizar dicho comportamiento a todas las familias políticas ni afirmar que el papel institucional sea su causa.

Para evaluar la hipótesis de forma general sería necesario identificar los periodos de Gobierno y oposición de cada partido, así como considerar los posibles factores de confusión.

### 5.3. Distribución temática

Las proporciones medias de los tópicos muestran diferencias entre legislaturas y familias políticas.

Entre las variaciones observadas destacan:

- El tópico `topic_01`, asociado con identidad nacional, aumenta aproximadamente del 5,3 % en la legislatura XII al 11,7 % en la XV.
- El tópico `topic_08`, relacionado con la confrontación entre partidos, pasa aproximadamente del 18,4 % al 24,2 % entre esas mismas legislaturas.
- Otros tópicos, como los vinculados al procedimiento parlamentario y los derechos sociales, muestran cambios en su peso relativo.

Estas proporciones representan la pertenencia media de las intervenciones a los tópicos, no una clasificación exclusiva de los textos.

Los resultados evidencian que la composición temática de la muestra cambia entre periodos. No obstante, los tópicos son agrupaciones estadísticas y sus etiquetas requieren interpretación.

### 5.4. Diversidad léxica

Los valores medios de MATTR son:

| Legislatura | MATTR medio |
|---|---:|
| XII | 0,688 |
| XIII | 0,690 |
| XIV | 0,692 |
| XV | 0,694 |

Se aprecia un ligero incremento, aunque los valores son muy similares entre legislaturas.

En consecuencia, la diversidad léxica presenta una relativa estabilidad en el periodo analizado.

Este indicador no permite extraer conclusiones directas sobre la calidad, profundidad o complejidad argumentativa del discurso.

## 6. Limitaciones y posibles sesgos

- **Representatividad:** la muestra fue estratificada por mes y familia política y excluye determinados tipos de intervenciones. No representa de manera exhaustiva toda la actividad parlamentaria española.
- **Cobertura temporal:** las legislaturas tienen diferentes duraciones y tamaños muestrales. Algunos meses están incompletos o carecen de observaciones.
- **Cambios políticos:** las agrupaciones utilizadas no siempre mantienen la misma composición entre legislaturas. Por ejemplo, Podemos-UP-Sumar reúne distintas formaciones a lo largo del periodo.
- **Gobierno y oposición:** el papel institucional puede cambiar dentro de una legislatura o depender de acuerdos y coaliciones. No se ha construido una variable completa que identifique esta situación para cada intervención.
- **Contexto de las intervenciones:** los asuntos debatidos, el tipo de intervención, la duración del discurso y el contexto histórico pueden influir en los indicadores.
- **Modelo de sentimiento:** RoBERTuito fue desarrollado para textos de redes sociales. La ironía, las citas, la negación y el registro parlamentario pueden reducir su precisión. Sus probabilidades no están necesariamente calibradas para este corpus.
- **Modelado de tópicos:** LDA depende del vocabulario, la limpieza y los parámetros elegidos. Algunos tópicos reflejan características lingüísticas o procedimentales, no únicamente asuntos políticos.
- **Procesamiento lingüístico:** la lematización, segmentación y detección de otras lenguas pueden producir errores. Los originales se conservan para facilitar la revisión.
- **Diversidad léxica:** MATTR mide variedad de vocabulario, no calidad ni complejidad argumentativa. Las intervenciones demasiado cortas no reciben una puntuación.
- **Alcance estadístico:** el estudio es exploratorio y descriptivo. Las diferencias observadas no demuestran significación estadística ni relaciones causales.

No se incorpora todavía una medida externa de polarización electoral, por lo que tampoco puede establecerse una relación directa entre los indicadores lingüísticos y la polarización electoral.

## 7. Conclusiones

El proceso desarrollado ha permitido generar indicadores temporales, temáticos y lingüísticos sobre una muestra de 10.000 intervenciones del Congreso de los Diputados.

El análisis de sentimiento muestra puntuaciones medias negativas en todas las legislaturas consideradas, con diferencias entre periodos y familias políticas.

En particular, los cambios observados en el sentimiento medio del Partido Popular sugieren que resulta interesante estudiar la posible relación entre el papel institucional de los partidos y el tono de sus intervenciones. Sin embargo, los resultados actuales no permiten confirmar que exista un patrón generalizado entre Gobierno y oposición.

La distribución temática también presenta variaciones entre familias políticas y legislaturas. Por su parte, la diversidad léxica mantiene valores relativamente estables durante el periodo analizado.

Estos resultados proporcionan una base para formular y posteriormente contrastar hipótesis sobre la evolución del discurso parlamentario y sus posibles relaciones con la polarización electoral.

## 8. Referencia del dataset

González, A., Hamberg, J., Somolinos, L., Blanco, A. y Sancho, H. (2026). *political-corpus-es: Intervenciones del Pleno del Congreso de los Diputados (2016–2026)* [Dataset]. Hugging Face.

https://huggingface.co/datasets/adrirana/political-corpus-es