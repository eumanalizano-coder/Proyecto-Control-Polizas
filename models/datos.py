# models/datos.py
# CAPA DE DATOS: este es el único archivo que abre archivos.
# Aquí convertimos el Excel y los PDF en datos que Python puede usar.

import shutil
from datetime import date, datetime
from pathlib import Path

import pandas as pd
import pdfplumber

# RUTAS: ubicación de la "bodega" de datos.
# Path(__file__) es este archivo; .parent es models/; .parent.parent es la raíz.
RAIZ = Path(__file__).resolve().parent.parent
CARPETA_DATOS = RAIZ / "data"
RUTA_CLIENTES = CARPETA_DATOS / "Maestro_Clientes.xlsx"
CARPETA_POLIZAS = CARPETA_DATOS / "polizas"

# CARPETA DE SUBIDAS: aquí se guarda el Excel que importa el usuario.
# Nunca tocamos data/: los archivos originales quedan intactos.
CARPETA_SUBIDAS = RAIZ / "uploads"
RUTA_CLIENTES_SUBIDOS = CARPETA_SUBIDAS / "Maestro_Clientes.xlsx"

# DICCIONARIO CAMPOS: etiqueta que aparece en el PDF -> nombre del campo en Python.
CAMPOS = {
    "Numero de poliza": "numero",
    "Ramo": "ramo",
    "Tomador / Asegurado": "nombre",
    "Cedula": "cedula",
    "Vigencia desde": "desde",
    "Vigencia hasta": "hasta",
    "Prima anual": "prima",
    "Forma de pago": "pago",
    "Suma asegurada": "suma",
    "Asesor": "asesor",
}


def _a_fecha(valor: str | None) -> date | None:
    """Convierte un texto dd/mm/aaaa en una fecha. Si está vacío o mal escrito, devuelve None."""
    # CONDICIONAL: si no hay valor, no se puede convertir.
    if not valor or not valor.strip():
        return None

    # BLOQUE try/except: intenta convertir; si falla, devuelve None.
    try:
        return datetime.strptime(valor.strip(), "%d/%m/%Y").date()
    except ValueError:
        return None


def _a_numero(valor: str | None) -> float | None:
    """Convierte un monto como 'CRC 228,000.00' en 228000.0. Si está vacío, devuelve None."""
    # CONDICIONAL: si no hay valor, no se puede convertir.
    if not valor or not valor.strip():
        return None

    # VARIABLE: quitamos 'CRC', las comas y los espacios.
    limpio = valor.replace("CRC", "").replace(",", "").strip()

    # BLOQUE try/except: intenta convertir a número; si falla, devuelve None.
    try:
        return float(limpio)
    except ValueError:
        return None


def ruta_clientes() -> Path:
    """Devuelve el Excel que debe usarse: primero el importado, luego el de data/."""
    # CONDICIONAL: si el usuario ya importó un Excel, ese manda.
    if RUTA_CLIENTES_SUBIDOS.exists():
        return RUTA_CLIENTES_SUBIDOS

    # Si no, usamos el archivo original de data/.
    return RUTA_CLIENTES


def cargar_clientes() -> pd.DataFrame:
    """Lee el Excel de clientes (hoja 'Clientes') y devuelve un DataFrame."""
    # VARIABLE: DataFrame con los clientes.
    # dtype={'Cedula': str} obliga a leer la cédula como texto, no como número.
    clientes = pd.read_excel(
        ruta_clientes(),
        sheet_name="Clientes",
        dtype={"Cedula": str},
    )

    # COLUMNA Cedula: texto, sin espacios.
    # fillna('') evita que una cédula vacía se convierta en el texto 'nan'.
    clientes["Cedula"] = (
        clientes["Cedula"]
        .fillna("")
        .astype(str)
        .str.replace(" ", "", regex=False)
        .str.strip()
    )

    return clientes


def guardar_clientes(archivo) -> int:
    """Valida el Excel subido, lo guarda en uploads/ y devuelve cuántos clientes tiene.

    Si el archivo no sirve, lanza ValueError con un mensaje claro.
    """
    # VARIABLE: nombre del archivo que envió el navegador.
    nombre = getattr(archivo, "filename", "") or ""

    # CONDICIONAL: solo aceptamos archivos .xlsx.
    if not nombre.lower().endswith(".xlsx"):
        raise ValueError("El archivo debe ser un Excel con extensión .xlsx.")

    # BLOQUE try/except: intentamos leer la hoja "Clientes" para validar.
    try:
        archivo.seek(0)
        datos = pd.read_excel(archivo, sheet_name="Clientes", dtype={"Cedula": str})
    except Exception as error:
        raise ValueError(
            "No se pudo leer el Excel. Revisa que tenga una hoja llamada 'Clientes'."
        ) from error

    # CONDICIONAL: el Excel debe traer la columna Cedula.
    if "Cedula" not in datos.columns:
        raise ValueError("El Excel no tiene la columna 'Cedula'.")

    # CONDICIONAL: no aceptamos un Excel vacío.
    if len(datos) == 0:
        raise ValueError("El Excel no tiene clientes.")

    # CARPETA: la creamos si todavía no existe.
    CARPETA_SUBIDAS.mkdir(parents=True, exist_ok=True)

    # GUARDAR: copiamos el archivo subido a uploads/.
    archivo.seek(0)
    with open(RUTA_CLIENTES_SUBIDOS, "wb") as salida:
        shutil.copyfileobj(archivo, salida)

    # Devolvemos cuántos clientes trajo.
    return len(datos)


def leer_poliza(ruta_pdf: str | Path) -> dict:
    """Lee un PDF de póliza y devuelve un diccionario con sus datos."""
    # VARIABLE: convertimos la ruta a Path para trabajar con archivos.
    ruta = Path(ruta_pdf)

    # DICCIONARIO: todos los campos empiezan en None.
    # Así el diccionario siempre tiene las mismas llaves, aunque falte un dato.
    datos = {
        "archivo": ruta.name,
        "aseguradora": None,
        "numero": None,
        "ramo": None,
        "nombre": None,
        "cedula": None,
        "desde": None,
        "hasta": None,
        "prima": None,
        "pago": None,
        "suma": None,
        "asesor": None,
    }

    # ABRIR PDF: pdfplumber lee el archivo y lo cierra al terminar el bloque with.
    with pdfplumber.open(ruta) as pdf:
        # VARIABLE: texto de la primera página.
        texto = pdf.pages[0].extract_text() or ""

    # LISTA: separamos el texto en líneas y quitamos líneas vacías.
    lineas = [linea.strip() for linea in texto.splitlines() if linea.strip()]

    # CONDICIONAL: si el PDF no tiene texto, devolvemos el diccionario vacío.
    if not lineas:
        return datos

    # VARIABLE: la primera línea es el nombre de la aseguradora.
    datos["aseguradora"] = lineas[0]

    # BUCLE: recorremos las líneas siguientes.
    for linea in lineas[1:]:
        # CONDICIONAL: solo nos interesan las líneas con formato 'Etiqueta: valor'.
        if ":" not in linea:
            continue

        # VARIABLE: separamos la etiqueta y el valor en el primer ':'.
        etiqueta, valor = linea.split(":", 1)
        etiqueta = etiqueta.strip()
        valor = valor.strip()

        # CONDICIONAL: si la etiqueta está en CAMPOS, guardamos el valor.
        if etiqueta in CAMPOS:
            campo = CAMPOS[etiqueta]
            datos[campo] = valor

    # CONVERSIONES: fechas y números.
    datos["desde"] = _a_fecha(datos["desde"])
    datos["hasta"] = _a_fecha(datos["hasta"])
    datos["prima"] = _a_numero(datos["prima"])
    datos["suma"] = _a_numero(datos["suma"])

    return datos


def cargar_polizas() -> list[dict]:
    """Recorre data/polizas en orden alfabético y devuelve una lista de diccionarios."""
    # LISTA: rutas de los PDF, ordenadas por nombre de archivo.
    rutas = sorted(CARPETA_POLIZAS.glob("*.pdf"), key=lambda ruta: ruta.name)

    # LISTA: aquí guardaremos el diccionario de cada póliza.
    polizas = []

    # BUCLE: leemos cada PDF y agregamos su diccionario a la lista.
    for ruta in rutas:
        polizas.append(leer_poliza(ruta))

    return polizas
