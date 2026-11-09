# services/generador_aviso.py
# CAPA DE SERVICIOS: aquí se crea el aviso de renovación en PDF.
# No lee archivos de datos ni calcula reglas: recibe un diccionario de póliza
# (ya calculado por models/polizas.py) y devuelve el PDF en bytes.

from datetime import date

from fpdf import FPDF

from models.polizas import estado_poliza

# CONSTANTES DE DISEÑO: colores y medidas del documento.
ROJO = (174, 24, 0)  # #AE1800
NEGRO = (32, 30, 29)  # #201E1D
GRIS_CLARO = (243, 242, 242)  # #F3F2F2
GRIS_TEXTO = (120, 120, 120)
BLANCO = (255, 255, 255)

ANCHO_PAGINA = 210  # A4 vertical, en milímetros
MARGEN = 15
ANCHO_UTIL = ANCHO_PAGINA - (MARGEN * 2)


def _texto(valor) -> str:
    """Convierte cualquier valor en texto compatible con latin-1 (tildes y ñ)."""
    # CONDICIONAL: si el valor viene vacío, devolvemos un texto vacío.
    if valor is None:
        return ""

    # VARIABLE: texto normal. Lo pasamos por latin-1 para que fpdf2 no falle.
    return str(valor).encode("latin-1", errors="replace").decode("latin-1")


def _fecha(valor) -> str:
    """Convierte una fecha en texto dd/mm/aaaa. Si no es fecha, devuelve 'No registrada'."""
    # CONDICIONAL: solo formateamos si de verdad es una fecha.
    if isinstance(valor, date):
        return valor.strftime("%d/%m/%Y")

    return "No registrada"


def _monto(valor) -> str:
    """Convierte un número en texto tipo 'CRC 228,000.00'. Si no hay prima, avisa."""
    # CONDICIONAL: si no hay prima, devolvemos el texto pedido.
    if valor is None:
        return "No registrada"

    # VARIABLE: número con separador de miles y dos decimales.
    return f"CRC {valor:,.2f}"


class _AvisoPDF(FPDF):
    """Clase pequeña que solo agrega el pie de página gris a cada hoja."""

    def footer(self):
        # Pie de página: se coloca 15 mm arriba del borde inferior.
        self.set_y(-20)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(*GRIS_TEXTO)
        self.multi_cell(
            ANCHO_UTIL,
            4,
            _texto(
                "Documento ficticio con fines académicos. "
                "No tiene validez legal ni comercial."
            ),
            align="C",
        )


def _banda_superior(pdf: _AvisoPDF) -> None:
    """Dibuja la banda roja con el nombre de la corredora y el título."""
    # Rectángulo rojo que ocupa todo el ancho de la hoja.
    pdf.set_fill_color(*ROJO)
    pdf.rect(0, 0, ANCHO_PAGINA, 32, "F")

    # Texto blanco encima de la banda.
    pdf.set_text_color(*BLANCO)
    pdf.set_font("Helvetica", "B", 16)
    pdf.set_xy(MARGEN, 9)
    pdf.cell(ANCHO_UTIL, 8, _texto("Corredora de Seguros Horizonte"))

    pdf.set_font("Helvetica", "", 11)
    pdf.set_xy(MARGEN, 18)
    pdf.cell(ANCHO_UTIL, 8, _texto("Aviso de renovación de póliza"))


def _saludo(pdf: _AvisoPDF, poliza: dict) -> None:
    """Escribe el saludo con el nombre del asegurado."""
    # Volvemos al color de texto normal y bajamos debajo de la banda.
    pdf.set_text_color(*NEGRO)
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_xy(MARGEN, 45)
    pdf.cell(ANCHO_UTIL, 8, _texto(f"Estimado(a) {poliza.get('nombre') or 'cliente'}:"))


def _parrafo(pdf: _AvisoPDF, poliza: dict) -> None:
    """Escribe el párrafo que cambia según el estado de la póliza."""
    # VARIABLES: datos que usamos en el texto.
    numero = poliza.get("numero") or "sin número"
    hasta = _fecha(poliza.get("hasta"))
    estado = poliza.get("estado") or estado_poliza(poliza.get("hasta"))
    dias = poliza.get("dias")

    # CONDICIONAL: el texto cambia si la póliza ya venció o si está por vencer.
    if estado == "Vencida":
        mensaje = (
            f"Le informamos que su póliza {numero} venció el {hasta}. "
            "Para mantener su cobertura activa, es importante renovarla lo antes posible. "
            "Su asesor se comunicará con usted para ayudarle con el trámite."
        )
    elif estado == "Por vencer":
        # VARIABLE: días restantes (si no vienen, mostramos 0).
        dias_texto = dias if dias is not None else 0
        mensaje = (
            f"Le informamos que su póliza {numero} vence el {hasta}, "
            f"en {dias_texto} días. Su asesor se comunicará con usted "
            "para coordinar la renovación."
        )
    else:
        mensaje = (
            f"Le informamos que su póliza {numero} tiene vigencia hasta el {hasta}. "
            "Su asesor se comunicará con usted para coordinar la renovación."
        )

    # Párrafo de varias líneas, con el mismo ancho útil de la página.
    # Colocamos la "y" debajo del saludo para que los textos no se encimen.
    pdf.set_xy(MARGEN, 55)
    pdf.set_font("Helvetica", "", 11)
    pdf.multi_cell(ANCHO_UTIL, 6, _texto(mensaje))


def _tabla(pdf: _AvisoPDF, poliza: dict) -> None:
    """Dibuja la tabla con los datos principales de la póliza."""
    # LISTA: filas de la tabla. Cada fila es (etiqueta, valor).
    filas = [
        ("Número de póliza", poliza.get("numero")),
        ("Aseguradora", poliza.get("aseguradora")),
        ("Ramo", poliza.get("ramo")),
        ("Cédula", poliza.get("cedula")),
        (
            "Vigencia",
            f"{_fecha(poliza.get('desde'))} al {_fecha(poliza.get('hasta'))}",
        ),
        ("Prima anual", _monto(poliza.get("prima"))),
        ("Forma de pago", poliza.get("pago")),
    ]

    # Medidas de las dos columnas.
    ancho_etiqueta = 55
    ancho_valor = ANCHO_UTIL - ancho_etiqueta
    alto_fila = 9

    # Espacio antes de la tabla.
    pdf.ln(6)

    # Encabezado de la tabla: fondo rojo y texto blanco.
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_fill_color(*ROJO)
    pdf.set_text_color(*BLANCO)
    pdf.set_x(MARGEN)
    pdf.cell(ANCHO_UTIL, alto_fila, _texto("Datos de la póliza"), border=1, fill=True)
    pdf.ln(alto_fila)

    # BUCLE: una fila por cada dato.
    for etiqueta, valor in filas:
        # Etiqueta: fondo gris claro y texto negro.
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_fill_color(*GRIS_CLARO)
        pdf.set_text_color(*NEGRO)
        pdf.set_x(MARGEN)
        pdf.cell(ancho_etiqueta, alto_fila, _texto(etiqueta), border=1, fill=True)

        # Valor: fondo blanco.
        pdf.set_font("Helvetica", "", 10)
        pdf.cell(
            ancho_valor,
            alto_fila,
            _texto(valor) or "No registrado",
            border=1,
            fill=False,
        )
        pdf.ln(alto_fila)


def crear_aviso_pdf(poliza: dict) -> bytes:
    """Crea el aviso de renovación en A4 vertical y devuelve el PDF en bytes."""
    # CONDICIONAL: sin póliza no hay nada que generar.
    if not poliza:
        raise ValueError("Se necesita un diccionario de póliza para crear el aviso.")

    # VARIABLE: documento PDF nuevo, A4 vertical y sin salto automático raro.
    pdf = _AvisoPDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=25)
    pdf.set_margins(MARGEN, MARGEN, MARGEN)
    pdf.add_page()

    # Armamos el documento por partes, en orden.
    _banda_superior(pdf)
    _saludo(pdf, poliza)
    _parrafo(pdf, poliza)
    _tabla(pdf, poliza)

    # DESPEDIDA: cierre del aviso.
    pdf.ln(10)
    pdf.set_font("Helvetica", "", 11)
    pdf.set_x(MARGEN)
    pdf.multi_cell(
        ANCHO_UTIL,
        6,
        _texto("Quedamos atentos a cualquier consulta. Muchas gracias."),
    )

    # VARIABLE: el PDF en bytes, listo para enviarlo por la ruta de Flask.
    return bytes(pdf.output())
