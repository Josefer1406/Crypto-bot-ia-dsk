import config

capital = float(config.CAPITAL_INICIAL)
posiciones = {}

STOP_LOSS = config.STOP_LOSS
TAKE_PROFIT = config.TAKE_PROFIT

# =========================
# ABRIR POSICIÓN (PRO)
# =========================
def abrir_posicion(symbol, precio, size):
    global capital

    costo = precio * size

    # =========================
    # SI YA EXISTE → REENTRADA
    # =========================
    if symbol in posiciones:

        pos = posiciones[symbol]

        # promedio de precio (position scaling)
        nuevo_size = pos["size"] + size
        nuevo_precio = (
            (pos["precio"] * pos["size"]) + (precio * size)
        ) / nuevo_size

        posiciones[symbol] = {
            "precio": nuevo_precio,
            "size": nuevo_size
        }

        capital -= costo
        return True

    # =========================
    # CONTROL DE POSICIONES
    # =========================
    if len(posiciones) >= config.MAX_POSICIONES:

        # 🔥 ROTACIÓN: eliminar peor posición
        peor_symbol = None
        peor_pnl = 0

        for s, p in posiciones.items():
            pnl = (precio - p["precio"]) / p["precio"]

            if pnl < peor_pnl:
                peor_pnl = pnl
                peor_symbol = s

        if peor_symbol:
            cerrar_posicion(peor_symbol, precio)

        else:
            return False

    # =========================
    # VALIDAR CAPITAL
    # =========================
    if costo > capital:
        return False

    capital -= costo

    posiciones[symbol] = {
        "precio": precio,
        "size": size
    }

    return True


# =========================
# CERRAR POSICIÓN
# =========================
def cerrar_posicion(symbol, precio):
    global capital

    pos = posiciones[symbol]

    pnl = (precio - pos["precio"]) * pos["size"]

    capital += pos["size"] * precio

    del posiciones[symbol]

    return pnl


# =========================
# SALIDA
# =========================
def evaluar_salida(symbol, precio):
    pos = posiciones[symbol]

    pnl = (precio - pos["precio"]) / pos["precio"]

    return pnl <= STOP_LOSS or pnl >= TAKE_PROFIT


# =========================
# ESTADO
# =========================
def cargar_estado():
    global capital
    print("🆕 Iniciando nuevo portfolio")