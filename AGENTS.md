# AGENTS.md

## Propósito del repositorio

Esta es una **carpeta de datos de entrada** para un proyecto de control de pólizas, no una aplicación. Actualmente no hay código, manifiesto de paquetes, compilación, pruebas, lint ni configuración de CI, y la carpeta no es un repositorio git. No busques un punto de entrada de aplicación; el trabajo consiste en ingerir, validar y reportar los datos descritos abajo.

Todos los datos son ficticios (ejercicio académico, Universidad Fundepos). No los trates como datos personales reales ni intentes verificar identidades externamente.

## Estructura

- `Insumos_Control_Polizas/Maestro_Clientes.xlsx` — maestro de clientes, hoja única `Clientes`.
- `Insumos_Control_Polizas/polizas/Poliza_<numero-poliza>.pdf` — 20 pólizas PDF de una página.
- Trata `Insumos_Control_Polizas/` como datos fuente de solo lectura; escribe la salida derivada en otra ubicación.

## Esquemas

Maestro de clientes (`Clientes`): fila de encabezado + 20 clientes.

`Cedula | Nombre_Completo | Correo | Telefono | Asesor`

PDFs de pólizas (misma plantilla para las 20):

`Numero de poliza | Ramo | Tomador / Asegurado | Cedula | Vigencia desde | Vigencia hasta | Prima anual | Forma de pago | Suma asegurada | Intermediario | Asesor | Coberturas principales`

- Formato del número de póliza: `<PREFIJO>-<AAAA>-<NNNN>`; el nombre del archivo es `Poliza_<numero-poliza>.pdf`.
- Prefijo a aseguradora: `AIS` = Aseguradora del Istmo S.A. (5), `PCS` = Proteccion Caribe S.A. (9), `SPC` = Seguros Pacifico Central S.A. (6).
- Valores de `Ramo`: `Automovil`, `Salud`, `Vida`, `Responsabilidad Civil`, `Hogar`. `Forma de pago`: `Anual`, `Semestral`, `Mensual`.
- La moneda es CRC (`CRC 1,234,567.00`), las fechas son `DD/MM/AAAA` y el texto es ASCII sin acentos (`Cedula`, `Umana`, `dano`). Conserva estos formatos en la salida.

## Trampas de datos verificadas

- `Poliza_AIS-2026-0002.pdf` tiene la **`Prima anual` vacía** (el PDF no renderiza ningún valor entre `Prima anual:` y `Forma de pago:`). Márcala como faltante; no la conviertas silenciosamente a 0.
- `PCS-2026-0009` (`Roberto Fantasma Perez`, cédula `9-0000-0001`) **no está en `Maestro_Clientes.xlsx`**.
- El cliente del maestro `Javier Espinoza Leon` (`1-0321-0654`) **no tiene póliza**.
- Cruce esperado póliza→cliente: 20 pólizas = 19 coincidencias + 1 póliza sin cliente; 20 clientes = 19 coincidencias + 1 cliente sin póliza.
- `Vigencia hasta` abarca 2026–2027 e incluye pólizas ya vencidas (p. ej. `AIS-2026-0005`, `PCS-2026-0001`, `PCS-2026-0009` a 2026-11). Calcula el estado a partir de las fechas; no asumas que todas están activas.

## Lectura de los insumos

- Los PDFs son de texto (no escaneados), pero son archivos ReportLab cuyos flujos de contenido usan `ASCII85Decode` + `FlateDecode`. `Select-String`/grep sobre bytes crudos no encontrará el texto de los campos; usa un extractor de texto PDF.
- Para decodificar manualmente: decodifica ASCII85, omite el encabezado zlib de 2 bytes, infla y luego lee los operadores `(...) Tj`.
- Entorno actual: no hay Python ni Node; sí hay PowerShell 5.1/.NET y Excel COM. Excel COM lee el xlsx de forma fiable; Word COM falló al abrir estos PDFs.
