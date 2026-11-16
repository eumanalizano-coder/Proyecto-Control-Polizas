# controllers/polizas_controller.py
# CAPA DE CONTROLADORES: aquí viven las rutas de Flask.
# Este archivo NO calcula nada: solo llama al modelo y al servicio,
# y devuelve una vista HTML o un archivo (PDF / ZIP).

from io import BytesIO
from zipfile import ZIP_DEFLATED, ZipFile

from flask import (
    Blueprint,
    abort,
    flash,
    redirect,
    render_template,
    request,
    send_file,
    url_for,
)

from models.datos import guardar_clientes, ruta_clientes
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

    # VARIABLE: de dónde sale el Excel en uso (uploads/ o data/).
    ruta_excel = ruta_clientes()
    origen_excel = f"{ruta_excel.parent.name}/{ruta_excel.name}"

    # RENDER: la vista solo muestra; los datos vienen ya calculados.
    return render_template(
        "inicio.html",
        resultados=resultados,
        conteo=contar_por_estado(resultados),
        primas=primas_por_aseguradora(resultados),
        inconsistencias=buscar_inconsistencias(resultados),
        fecha_corte=FECHA_CORTE,
        origen_excel=origen_excel,
    )


@bp.route("/importar-excel", methods=["POST"])
def importar_excel():
    """Recibe el Excel del formulario, lo guarda y vuelve al tablero."""
    # VARIABLE: archivo que llegó en el formulario (puede venir vacío).
    archivo = request.files.get("archivo")

    # CONDICIONAL: si no eligieron archivo, avisamos y volvemos.
    if archivo is None or not archivo.filename:
        flash("Selecciona un archivo Excel antes de importar.", "error")
        return redirect(url_for("polizas.inicio"))

    # BLOQUE try/except: guardar_clientes valida y guarda el archivo.
    try:
        total = guardar_clientes(archivo)
    except ValueError as error:
        flash(str(error), "error")
    else:
        flash(f"Excel importado correctamente: {total} clientes.", "ok")

    return redirect(url_for("polizas.inicio"))


@bp.route("/ejecutar-proceso", methods=["POST"])
def ejecutar_proceso():
    """Vuelve a calcular todo y refresca el tablero con un mensaje."""
    # VARIABLE: recalculamos para confirmar que los datos se leyeron bien.
    resultados = calcular_resultados()

    flash(f"Proceso ejecutado: {len(resultados)} pólizas revisadas.", "ok")

    return redirect(url_for("polizas.inicio"))


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
