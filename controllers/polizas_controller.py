# controllers/polizas_controller.py
# CAPA DE CONTROLADORES: aquí viven las rutas de Flask.
# Este archivo NO calcula nada: solo llama al modelo y al servicio,
# y devuelve una vista HTML o un archivo (PDF / ZIP).

from io import BytesIO
from zipfile import ZIP_DEFLATED, ZipFile

from flask import Blueprint, abort, render_template, send_file

from models.polizas import (
    FECHA_CORTE,
    buscar_inconsistencias,
    buscar_por_numero,
    calcular_resultados,
    contar_por_estado,
    primas_por_aseguradora,
)
from services.generador_aviso import crear_aviso_pdf

# BLUEPRINT: grupo de rutas. app.py lo registra al final.
bp = Blueprint("polizas", __name__)

# LISTA: estados que sí necesitan aviso de renovación.
ESTADOS_CON_AVISO = ("Por vencer", "Vencida")


@bp.route("/")
def inicio():
    """Muestra el tablero con los contadores, primas, inconsistencias y tabla."""
    # VARIABLE: lista de pólizas ya cruzadas con el maestro.
    resultados = calcular_resultados()

    # RENDER: la vista solo muestra; los datos vienen ya calculados.
    return render_template(
        "inicio.html",
        resultados=resultados,
        conteo=contar_por_estado(resultados),
        primas=primas_por_aseguradora(resultados),
        inconsistencias=buscar_inconsistencias(resultados),
        fecha_corte=FECHA_CORTE,
    )


@bp.route("/aviso/<numero>")
def aviso(numero: str):
    """Devuelve el aviso de renovación en PDF para verlo en el navegador."""
    # VARIABLE: póliza encontrada por su número (o None).
    poliza = buscar_por_numero(numero)

    # CONDICIONAL: 404 si la póliza no existe o si todavía está vigente.
    if poliza is None or poliza["estado"] not in ESTADOS_CON_AVISO:
        abort(404)

    # VARIABLE: PDF en bytes, generado por el servicio.
    contenido = crear_aviso_pdf(poliza)

    # SEND_FILE: enviamos el PDF desde memoria, sin guardarlo en disco.
    return send_file(
        BytesIO(contenido),
        mimetype="application/pdf",
        as_attachment=False,
        download_name=f"aviso_{numero}.pdf",
    )


@bp.route("/descargar-avisos")
def descargar_avisos():
    """Arma un .zip en memoria con los avisos de las pólizas por vencer y vencidas."""
    # VARIABLE: todas las pólizas calculadas.
    resultados = calcular_resultados()

    # LISTA: solo las que necesitan aviso.
    pendientes = [p for p in resultados if p["estado"] in ESTADOS_CON_AVISO]

    # VARIABLE: "archivo" en memoria, sin tocar el disco.
    memoria = BytesIO()

    # BUCLE: agregamos un PDF por cada póliza pendiente dentro del zip.
    with ZipFile(memoria, "w", ZIP_DEFLATED) as archivo_zip:
        for poliza in pendientes:
            archivo_zip.writestr(
                f"aviso_{poliza['numero']}.pdf",
                crear_aviso_pdf(poliza),
            )

    # Volvemos al inicio del archivo para poder enviarlo completo.
    memoria.seek(0)

    # SEND_FILE: descarga del zip.
    return send_file(
        memoria,
        mimetype="application/zip",
        as_attachment=True,
        download_name="avisos_renovacion.zip",
    )
