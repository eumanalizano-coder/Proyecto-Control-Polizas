# models/polizas.py
# CAPA DE NEGOCIO: aquí están las reglas de las pólizas.
# No abrimos archivos aquí: usamos las funciones de models/datos.py.

from datetime import date

from models.datos import cargar_clientes, cargar_polizas

# CONSTANTES: fecha de corte y días de aviso.
FECHA_CORTE = date(2026, 11, 9)
DIAS_AVISO = 30


def estado_poliza(hasta: date | None, fecha_corte: date = FECHA_CORTE) -> str:
    """Devuelve el estado de una póliza según su fecha de vencimiento."""
    # CONDICIONAL: si no hay fecha, no podemos calcular el estado.
    if hasta is None:
        return "Sin fecha"

    # VARIABLE: días que faltan para vencer (pueden ser negativos).
    dias = (hasta - fecha_corte).days

    # CONDICIONAL: comparamos los días con la fecha de corte y el aviso.
    if dias < 0:
        return "Vencida"
    elif dias <= DIAS_AVISO:
        return "Por vencer"
    else:
        return "Vigente"


def calcular_resultados(fecha_corte: date = FECHA_CORTE) -> list[dict]:
    """Cruza pólizas y clientes, calcula días/estado y ordena por urgencia."""
    # VARIABLE: DataFrame de clientes y lista de pólizas.
    clientes = cargar_clientes()
    polizas = cargar_polizas()

    # DICCIONARIO: cédula -> fila del cliente, para buscar rápido.
    clientes_por_cedula = {
        fila["Cedula"]: fila for _, fila in clientes.iterrows()
    }

    # LISTA: aquí guardaremos un diccionario por cada póliza.
    resultados = []

    # BUCLE: recorremos todas las pólizas.
    for poliza in polizas:
        # VARIABLE: cliente encontrado en el maestro (o None).
        cliente = clientes_por_cedula.get(poliza["cedula"])

        # CONDICIONAL: sabremos si la cédula está en el maestro.
        en_maestro = cliente is not None

        # VARIABLE: correo del cliente (o None si no está en el maestro).
        correo = cliente["Correo"] if en_maestro else None

        # VARIABLE: fecha de vencimiento y días hasta vencer.
        hasta = poliza["hasta"]
        dias = (hasta - fecha_corte).days if hasta is not None else None

        # VARIABLE: estado calculado con la función de arriba.
        estado = estado_poliza(hasta, fecha_corte)

        # DICCIONARIO: copiamos los datos de la póliza y agregamos los nuevos.
        resultado = {
            **poliza,
            "correo": correo,
            "en_maestro": en_maestro,
            "dias": dias,
            "estado": estado,
        }
        resultados.append(resultado)

    # ORDEN: de menos a más días. Las pólizas sin fecha van al final.
    resultados.sort(
        key=lambda r: (r["dias"] is None, r["dias"] if r["dias"] is not None else 0)
    )

    return resultados


def contar_por_estado(resultados: list[dict]) -> dict:
    """Cuenta cuántas pólizas hay en cada estado."""
    # DICCIONARIO: contadores iniciados en cero.
    conteo = {
        "Vigente": 0,
        "Por vencer": 0,
        "Vencida": 0,
        "Sin fecha": 0,
    }

    # BUCLE: sumamos uno al estado de cada póliza.
    for poliza in resultados:
        estado = poliza["estado"]
        if estado in conteo:
            conteo[estado] += 1

    return conteo


def primas_por_aseguradora(resultados: list[dict]) -> dict:
    """Suma las primas no vencidas por aseguradora, de mayor a menor."""
    # DICCIONARIO: aseguradora -> suma de primas.
    sumas = {}

    # BUCLE: recorremos los resultados.
    for poliza in resultados:
        # CONDICIONAL: las pólizas vencidas no se suman.
        if poliza["estado"] == "Vencida":
            continue

        # VARIABLE: prima de la póliza (puede ser None).
        prima = poliza["prima"]

        # CONDICIONAL: si no hay prima, no se suma.
        if prima is None:
            continue

        # VARIABLE: nombre de la aseguradora.
        aseguradora = poliza["aseguradora"]

        # Sumamos la prima a la aseguradora correspondiente.
        sumas[aseguradora] = sumas.get(aseguradora, 0.0) + prima

    # ORDEN: convertimos a lista ordenada y la volvemos a convertir en diccionario.
    return dict(sorted(sumas.items(), key=lambda item: item[1], reverse=True))


def buscar_inconsistencias(resultados: list[dict]) -> list[str]:
    """Devuelve una lista de textos con los problemas encontrados."""
    # LISTA: aquí guardaremos los textos.
    textos = []

    # VARIABLE: clientes del maestro.
    clientes = cargar_clientes()

    # LISTA/DICCIONARIO: cédulas que sí tienen alguna póliza.
    cedulas_con_poliza = {poliza["cedula"] for poliza in resultados}

    # TIPO 1: cliente del maestro sin ninguna póliza.
    for _, cliente in clientes.iterrows():
        if cliente["Cedula"] not in cedulas_con_poliza:
            textos.append(
                f"Cliente sin póliza: {cliente['Nombre_Completo']} "
                f"({cliente['Cedula']})."
            )

    # TIPO 2: póliza cuya cédula no está en el maestro.
    for poliza in resultados:
        if not poliza["en_maestro"]:
            textos.append(
                f"Póliza sin cliente en el maestro: {poliza['numero']} "
                f"({poliza['nombre']}, cédula {poliza['cedula']})."
            )

    # TIPO 3: póliza sin prima o con fecha ilegible.
    for poliza in resultados:
        problemas = []

        if poliza["prima"] is None:
            problemas.append("sin prima")
        if poliza["desde"] is None:
            problemas.append("fecha desde ilegible")
        if poliza["hasta"] is None:
            problemas.append("fecha hasta ilegible")

        if problemas:
            textos.append(
                f"Póliza con datos incompletos: {poliza['numero']} "
                f"({poliza['nombre']}): {', '.join(problemas)}."
            )

    return textos


def buscar_por_numero(numero: str) -> dict | None:
    """Busca una póliza por su número. Devuelve el diccionario o None."""
    # CONDICIONAL: si no viene número, no hay nada que buscar.
    if not numero:
        return None

    # VARIABLE: limpiamos espacios.
    numero = numero.strip()

    # BUCLE: recorremos los resultados y comparamos el número.
    for poliza in calcular_resultados():
        if poliza["numero"] == numero:
            return poliza

    # Si el bucle termina sin encontrarla, devolvemos None.
    return None
