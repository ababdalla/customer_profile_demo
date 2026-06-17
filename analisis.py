import pandas as pd


def anomes_fix(df):
    df["yearmonth"] = pd.to_datetime(df["anomes"], format="%Y%m")

    df["year"] = df["yearmonth"].dt.year
    df["month"] = df["yearmonth"].dt.month

    return df


def quetzalizar_montos_agencias(df):

    df_tipo_cambio = pd.read_csv(r"static\cambio_dolar.csv")
    df_merge = df.merge(df_tipo_cambio, on="anomes", how="left")

    df_merge["factor"] = df_merge["tipocambio"].where(
        df_merge["monedacodigotx"] == "DOLAR AMERICANO", 1
    )

    df_merge["montocreditos_gtq"] = df_merge["montocreditos"] * df_merge["factor"]
    df_merge["montodebitos_gtq"] = df_merge["montodebitos"] * df_merge["factor"]

    df_consolidado = df_merge.groupby(["cuentaid", "oficina"], as_index=False).agg(
        {
            "montodebitos": "sum",
            "montocreditos": "sum",
            "montocreditos_gtq": "sum",
            "montodebitos_gtq": "sum",
            "txcreditos": "sum",
            "txdebitos": "sum",
            "monedacodigotx": "max",
        }
    )

    df_consolidado["pct_creditos"] = (
        df_consolidado["montocreditos_gtq"]
        / df_consolidado["montocreditos_gtq"].sum()
        * 100
    )
    df_consolidado["pct_debitos"] = (
        df_consolidado["montodebitos_gtq"]
        / df_consolidado["montodebitos_gtq"].sum()
        * 100
    )

    return df_consolidado


def quetzalizar_montos_causas(df):

    df_tipo_cambio = pd.read_csv(r"static\cambio_dolar.csv")
    df_merge = df.merge(df_tipo_cambio, on="anomes", how="left")

    df_merge["factor"] = df_merge["tipocambio"].where(
        df_merge["monedacodigotx"] == "DOLAR AMERICANO", 1
    )

    df_merge["montocreditos_gtq"] = df_merge["montocreditos"] * df_merge["factor"]
    df_merge["montodebitos_gtq"] = df_merge["montodebitos"] * df_merge["factor"]

    df_consolidado = df_merge.groupby(
        ["cuentaid", "causatransaccion"], as_index=False
    ).agg(
        {
            "montocreditos_gtq": "sum",
            "montodebitos_gtq": "sum",
            "txcreditos": "sum",
            "txdebitos": "sum",
            "montocreditos": "sum",
            "montodebitos": "sum",
            "monedacodigotx": "max",
        }
    )

    df_consolidado["pct_creditos"] = (
        df_consolidado["montocreditos_gtq"]
        / df_consolidado["montocreditos_gtq"].sum()
        * 100
    )
    df_consolidado["pct_debitos"] = (
        df_consolidado["montodebitos_gtq"]
        / df_consolidado["montodebitos_gtq"].sum()
        * 100
    )

    return df_consolidado


def tabla_consolidada(mensual):

    import pandas as pd

    df_tipo_cambio = pd.read_csv(r"static\cambio_dolar.csv")
    df_merge = mensual.merge(df_tipo_cambio, on="anomes", how="left")

    df_merge["factor"] = df_merge["tipocambio"].where(
        df_merge["monedacodigotx"] == "DOLAR AMERICANO", 1
    )

    df_merge["montocreditos_gtq"] = df_merge["montocreditos"] * df_merge["factor"]
    df_merge["montodebitos_gtq"] = df_merge["montodebitos"] * df_merge["factor"]

    df_consolidado = df_merge.groupby(["anomes"], as_index=False).agg(
        {
            "montocreditos_gtq": "sum",
            "montodebitos_gtq": "sum",
            "txcreditos": "sum",
            "txdebitos": "sum",
            "year": "max",
            "month": "max",
        }
    )

    df_consolidado["pct_creditos"] = (
        df_consolidado["montocreditos_gtq"]
        / df_consolidado["montocreditos_gtq"].sum()
        * 100
    )
    df_consolidado["pct_debitos"] = (
        df_consolidado["montodebitos_gtq"]
        / df_consolidado["montodebitos_gtq"].sum()
        * 100
    )
    return df_consolidado


def generar_grafica_consolidada(df_consolidado, ing_extra, ing_ofi, ing_estimado,ing_empresa):
    import io
    import matplotlib.pyplot as plt
    import matplotlib.ticker as mticker
    import numpy as np
    import pandas as pd

    if df_consolidado.empty:
        return None

    df_prueba = df_consolidado.copy()
    df_prueba["anio"] = df_prueba["anomes"] // 100
    df_prueba["mes"] = df_prueba["anomes"] % 100

    df_prueba["fecha"] = pd.to_datetime(
        df_prueba["anio"].astype(str) + "-" + df_prueba["mes"].astype(str) + "-01",
        format="%Y-%m-%d",
    )

    # creacion grafica
    df_prueba["flujo_total"] = df_prueba["montocreditos_gtq"]

    promedio = df_prueba["flujo_total"].mean()
    # std = df_prueba["flujo_total"].std()

    ingresos_registrados = ing_extra + ing_ofi + ing_empresa
    limite = (ing_extra + ing_ofi+ing_empresa) if ingresos_registrados > 0 else ing_estimado # This is a great one liner by copilot chat

    # limite_inferior = promedio - 1.5 * std

    fig, ax = plt.subplots(figsize=(20, 10))
# ---1. Linea principal -----------
    ax.plot(df_prueba["fecha"], df_prueba["flujo_total"], marker="o", color="green")
#----2. Lineas de referencia ---------------
    ax.axhline(promedio, linestyle="--", color="orange", label="Promedio")
    ax.axhline(limite, linestyle=":", color="red", label="Limite Anomalia")
    # ax.axhline(limite_inferior, linestyle=":", color="red", label="Limite Anomalia Inferior")

#-- Nuevo 1. Etiquetas al extremo derecho de las líneas de referencia -----
    x_max = df_prueba["fecha"].max()
    x_label = x_max + pd.DateOffset(days = 20)

    ax.set_xlim(right = x_label + pd.DateOffset(days = 10))

    ax.annotate(
        f"----------Q{promedio:,.0f}",
        xy = (x_label,promedio),
        xytext=(8,0),   
        textcoords = "offset points",
        va = "center",ha="left",
        fontsize = 11, color = "orange",
        annotation_clip=False,
    )
    ax.annotate(
        f"----------Q{limite:,.0f}",
        xy=(x_label,limite),
        xytext=(8,0),
        textcoords="offset points",
        va="center",ha="left",
        fontsize = 11,color="red",
        annotation_clip=False,
    )

    #----NUEVO 2. Escala de eje Y con separador de Miles -----
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x,_: f"Q{x:,.0f}"))

    #---- NUEVO 3. Etiquetas de monto en cada punto de la línea -----------
    for _, row in df_prueba.iterrows():
        ax.annotate(
            f"Q{row['flujo_total']:,.0f}",
            xy = (row["fecha"],row["flujo_total"]),
            xytext=(0,10),
            textcoords = "offset points",
            ha = "center", va="bottom",
            fontsize = 9,
            bbox = dict(
                boxstyle="round, pad =0.2",
                fc = "white",ec ="none",alpha = 0.6
            ),
        )

    ax.set_xlabel("Fecha", fontsize=16)
    ax.set_ylabel("Monto", fontsize=16)

    ax.tick_params(axis="both", which="major", labelsize=14)

    # Marcar meses que superan el limite:
    df_out = df_prueba[df_prueba["flujo_total"] > limite]
    ax.scatter(
        df_out["fecha"], df_out["flujo_total"], s=80, color="red", label="Anomalia"
    )
    ax.legend(
        ["Movimientos", "Promedio", "Ingresos Cliente"],
        loc="best",
        frameon=True,
        fontsize=20,
    )
    ax.set_title("Movimiento Promedio del cliente", fontsize=18, fontweight="semibold")

    ax.grid(True, alpha=0.3)

    buffer = io.BytesIO()
    fig.savefig(buffer, format="png", bbox_inches="tight")
    buffer.seek(0)
    plt.close(fig)

    return buffer


def generar_grafica_outliers_compacta(df_transacciones):
    import io

    import matplotlib.pyplot as plt
    import numpy as np
    import pandas as pd

    fig, axes = plt.subplots(1, 2, figsize=(12, 4))

    df_transacciones["fechatransaccion"] = pd.to_datetime(
        df_transacciones["fechatransaccion"], format="%Y-%m-%d"
    )

    df_transacciones["anomes"] = (
        df_transacciones["fechatransaccion"].dt.strftime("%Y%m").astype(int)
    )

    df_tipo_cambio = pd.read_csv(r"static\cambio_dolar.csv")
    df_merge = df_transacciones.merge(df_tipo_cambio, on="anomes", how="left")

    df_merge["factor"] = df_merge["tipocambio"].where(
        df_merge["monedatransaccion"] == "DOLAR AMERICANO", 1
    )

    df_merge["montotransacciongtq"] = df_merge["montotransaccion"] * df_merge["factor"]
    # Creditos
    creditos = df_merge[df_merge["tipooperacion"] == "CREDITO"]["montotransacciongtq"]
    debitos = df_merge[df_merge["tipooperacion"] == "DEBITO"]["montotransacciongtq"]
    fig, axes = plt.subplots(1, 2, figsize=(15, 4))

    creditos = creditos.replace([float("inf"), float("-inf")], None)
    creditos = creditos.dropna()
    debitos = debitos.replace([float("inf"), float("-inf")], None)
    debitos = debitos.dropna()

    creditos = creditos.round(2)
    debitos = debitos.round(2)

    axes[0].boxplot(creditos.values, vert=False)
    # axes[0].set_xscale("log")
    limite_cre = creditos.quantile(0.99)
    axes[0].set_xlim(0, limite_cre)
    axes[0].set_title("Outliers Creditos")

    axes[1].boxplot(debitos.values, vert=False)
    # axes[1].set_xscale("log")
    limite_de = creditos.quantile(0.99)
    axes[1].set_xlim(0, limite_de)
    axes[1].set_title("Outliers Debitos")

    buffer = io.BytesIO()
    fig.savefig(buffer, format="png", bbox_inches="tight")
    buffer.seek(0)
    plt.close(fig)
    return buffer
