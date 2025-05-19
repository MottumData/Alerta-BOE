# Sistema de Alerta de cambios en BOE sobre Biodiversidad

![Logo Mottum](https://mottum.io/wp-content/uploads/2023/07/Logo-Mottum-oscuro-fondo-transp-512w.png)


**Solución presentada para el Hackathon "Soluciones GenAI para la Biodiversidad" de Algoritmos Verdes.**
[![Hackathon Badge](https://img.shields.io/badge/Hackathon-Algoritmos%20Verdes%20GenAI%20Biodiversidad-brightgreen)](https://algoritmosverdes.gob.es/es/hackathon/soluciones-genai-para-la-biodiversidad)


## 1. El Reto: Problema de Biodiversidad 

### **Relevancia** 💡
Mantenerse al día con la legislación sobre biodiversidad publicada en boletines oficiales (como el BOE) es crucial para la conservación, la investigación y la gestión ambiental en España. Sin embargo, el volumen y la frecuencia de las publicaciones hacen que el seguimiento manual sea una tarea ingente y propensa a retrasos.

### **Ineficiencia Actual** ⏳
La principal dificultad radica en la necesidad de revisar manualmente extensos documentos oficiales para identificar, interpretar y resumir las secciones relevantes para la biodiversidad. Este proceso consume mucho tiempo y recursos, ralentizando la capacidad de respuesta y la toma de decisiones informadas por parte de administraciones, empresas y centros de investigación.


## 2. Nuestra Solución:
*   **Descripción General:** Esta solución se conecta con la API del BOE, consulta de forma diaria los boletines de los ministerios y departamentos previamente configurados, y extrae todos sus documentos publicados. Una vez extraídos se  genera un resumen para cada uno de ellos y se envían estos resumenes por email al usuario. 
*   **Enfoque GenAI:** 
    *   Clasificación binaria con LLM: Cada disposición extraída se pasa por un modelo instructivo el cual devuelve true si la información de el BOE está relacionada con biodiversidad y false en caso contrario.

    *   Filtrado por ministerio: Sólo procesamos los boletines de los organismos que interesan (Medio Ambiente, Ciencia, Agricultura, …), solo de aquellos que suban BOEs relacionados con la temática de la Biodiversidad.

    *   Resumen automático: Para cada documento marcado como true, el LLM genera un resumen con los puntos claves que se tratan en cada BOE.

## 3. Características Principales

*   Funcionalidades clave
    *   API del BOE: Extracción automática de los documentos publicados por los ministerios seleccionados.

    *   Clasificación binaria: LLM que etiqueta cada BOE en función de su relación con la biodiversidad.

    *   Generación de resúmenes: Resumen de 3–4 frases del contenido del BOE

    *   Alerts & Notificaciones: Envío por email de los resúmenes, sólo de los documentos clasificados como TRUE en el contexto de Biodiversidad.

## 4. Demo / Presentación
  
*   Enlace a un vídeo corto mostrando la aplicación en funcionamiento.
*   Enlace a la presentación de diapositivas (si la hay).

## 5. Stack Tecnológico

*   **Lenguajes:** Python, etc.
*   **Frameworks/Librerías Principales:** Langchain, Ollama.
*   **Modelos GenAI Utilizados:** Especifica los modelos LLM (ej: `hdnh2006/salamandra-7b-instruct`, `all-mpnet-base-v2` para embeddings).
*   **Infraestructura:**: Maquina en la que se desarrolla de Azure
*   **Otros:** CodeCarbon (para medición de emisiones), etc.
*   

## Instalación 

*   Instalamos las dependencias del proyecto
```bash
requirements.txt
```

*   Instalamos ollama en caso de no tenerlo instalado
(https://ollama.com/download/windows)

## Uso 
- Incluir los correos de los destinatarios en el archivo destinatarios.json en formato json.
- run:
```bash
python main.py
```