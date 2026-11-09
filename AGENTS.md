# Proyecto: control-polizas
 
## Reglas para el agente
1. Responde siempre en español, con lenguaje sencillo: soy principiante.
2. Antes de construir algo nuevo, muestra un plan corto y espera mi aprobación.
3. Después de cada cambio, explica qué archivos cambiaste y en qué capa están.
4. Código comentado en español, señalando los ladrillos: variables, tipos, listas, diccionarios, condicionales, bucles y funciones.
5. No borres archivos ni modifiques nada dentro de data/.
6. Nunca enciendas la app por tu cuenta: yo la enciendo con iniciar_app.bat.
 
## Tecnología
- Gestor: uv (nunca pip). Librerías con "uv add". Ejecutar con "uv run app.py".
- Python 3.12, Flask, pandas, openpyxl, pdfplumber (leer PDF) y fpdf2 (crear PDF). La app NO usa inteligencia artificial.
 
## Arquitectura por capas (respetarla siempre)
- data/ = la bodega: Maestro_Clientes.xlsx y la carpeta polizas/ con los PDF (solo lectura).
- models/datos.py = único lugar que abre archivos. cargar_clientes() lee el Excel con pandas (Cedula como texto sin espacios). leer_poliza(ruta) extrae el texto del PDF con pdfplumber y devuelve un diccionario; cargar_polizas() recorre data/polizas y devuelve una lista de diccionarios.
- models/polizas.py = reglas del negocio: FECHA_CORTE, DIAS_AVISO, estado_poliza(), calcular_resultados(), contar_por_estado(), primas_por_aseguradora(), buscar_inconsistencias(), buscar_por_numero().
- services/generador_aviso.py = crear el aviso de renovación en PDF con fpdf2 (A4 vertical) y devolverlo en bytes.
- controllers/polizas_controller.py = rutas de Flask (Blueprint). No calcula: llama al modelo y al servicio.
- views/ = plantillas HTML (Jinja). Solo muestran. public/static/estilos.css = diseño rojo (#AE1800), negro (#201E1D) y gris claro (#F3F2F2).
- app.py = crea la app Flask en la variable app con template_folder="views", static_folder="public/static", static_url_path="/static", y registra el Blueprint.
 
## Formato de los PDF
- La primera línea del texto es el nombre de la aseguradora.
- Luego hay líneas "Etiqueta: valor" con estas etiquetas: Numero de poliza, Ramo, Tomador / Asegurado, Cedula, Vigencia desde, Vigencia hasta, Prima anual, Forma de pago, Suma asegurada, Asesor.
- Fechas en formato dd/mm/aaaa. Montos como "CRC 228,000.00" (convertir a número; si está vacío, None).
 
## Reglas del negocio
- FECHA_CORTE = 2 de noviembre de 2026. DIAS_AVISO = 30.
- Vencida: hasta < FECHA_CORTE. Por vencer: 0 <= días hasta vencer <= DIAS_AVISO. Vigente: más de DIAS_AVISO días.
- Cruzar cada póliza con el maestro por Cedula para obtener el correo.
- Inconsistencias: (1) cliente del maestro sin ninguna póliza; (2) póliza cuya cédula no está en el maestro; (3) póliza sin prima o con fecha ilegible.
- Primas por aseguradora: suma de la prima de las pólizas no vencidas.
- Resultado esperado con los datos de data/: 12 Vigentes, 5 Por vencer, 3 Vencidas y 3 inconsistencias.
 
## Rutas de la app
- "/" tablero: 3 contadores, primas por aseguradora, inconsistencias y tabla de pólizas ordenada por días para vencer (lo urgente primero).
- "/aviso/" devuelve el aviso en PDF; 404 si la póliza no existe o está vigente.
- "/descargar-avisos" un .zip con los avisos de todas las pólizas por vencer y vencidas.