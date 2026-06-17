def generar_grafica_por_cuentas(
        df, ing_extra,ing_ofi,ing_estimado,ing_empresa
        ):
    import io
    import matplotlib.pyplot as plt
    import pandas as pd
    import matplotlib.ticker as mticker
    import numpy as np

    graficas_buffer = {}

    if not df.empty:
        for cuenta_id, df_cuenta in df.groupby("cuentaid"):
            df_cuenta["anio"] = df_cuenta["anomes"] // 100
            df_cuenta["mes"] = df_cuenta["anomes"] % 100
            df_cuenta["fecha"] = pd.to_datetime(
                df_cuenta["anio"].astype(str)
                + "-"
                + df_cuenta["mes"].astype(str)
                + "-01",
                format="%Y-%m-%d",
            )

            #agregando cambios de grafica general:
            ## Esto es para ver los promedios de cada uno de los movimientos que tienen
            promedio_creditos = df_cuenta["montocreditos"].mean()
            promedio_debitos = df_cuenta["montodebitos"].mean()

            ingresos_registrados = ing_extra + ing_ofi + ing_empresa
            limite = (ing_extra + ing_ofi + ing_empresa) if ingresos_registrados>0 else ing_estimado

            fig, ax = plt.subplots(figsize=(16, 10))
            #----1. Lineas principales--------
            ax.plot(df_cuenta["fecha"], df_cuenta["montocreditos"],marker = "o", color="green")  # pyright: ignore[reportAttributeAccessIssue]
            ax.plot(df_cuenta["fecha"], df_cuenta["montodebitos"], marker = "x", color ="red")

            #-----2. Lineas de referencia-----
            ax.axhline(promedio_creditos,linestyle="--",color="green",label = "P_creditos")
            ax.axhline(promedio_debitos,linestyle="--",color="red",label = "P_debitos")
            ax.axhline(limite,linestyle=":",color="yellow",label = "Limite")
            
            #-- 3. Agregando etiquetas al extremo derecho----

            x_max = df_cuenta["fecha"].max()
            x_label = x_max + pd.DateOffset(days = 30)

            ax.set_xlim(right=x_label +pd.DateOffset(days = 10))
            ax.annotate(
                f"--------------Q{promedio_creditos:,.0f}",
                xy = (x_label,promedio_creditos),
                xytext = (8,0),
                textcoords="offset points",
                va="center",ha="left",
                fontsize = 11, color = "green",
                annotation_clip=False,
            )
            ax.annotate(
                f"--------------Q{promedio_debitos:,.0f}",
                xy = (x_label,promedio_creditos),
                xytext = (8,0),
                textcoords="offset points",
                va="center",ha="left",
                fontsize = 11, color = "red",
                annotation_clip=False,
            )

           # --------Nuevo 2. Escala de eje Y con separador de miles ------
            ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x,_:f"Q{x:,.0f}"))

            # -------Nuevo 3. Etiquetas de monto en cada punto de la lineas------
            for _, row in df_cuenta.iterrows():
                ax.annotate(
                        f"Q{row['montodebitos']:,.0f}",
                        xy = (row["fecha"],row["montodebitos"]),
                        xytext=(0,10),
                        textcoords = "offset points",
                        ha = "center", va="bottom",
                        fontsize = 9,
                        bbox = dict(
                            boxstyle="round, pad =0.2",
                            fc = "white",ec ="none",alpha = 0.6
                            ),
                        )


            ax.set_title(
                f"Cuenta {cuenta_id} {df_cuenta['monedacodigotx'].iloc[0]}- Creditos vs Debitos",
                fontsize=18,
                fontweight="semibold",
            )
            ax.set_xlabel("Fecha", fontsize=14)
            ax.set_ylabel("Monto", fontsize=14)

            ax.tick_params(axis="both", which="major", labelsize=12)

            ax.legend(["Creditos", "Debitos","P.Creditos","P.Debitos","Ingresos Cliente"], loc="best", frameon=True, fontsize=15)
            ax.grid(True, linestyle="--", alpha=0.4)

            buffer = io.BytesIO()
            fig.savefig(buffer, format="png", bbox_inches="tight")
            buffer.seek(0)

            graficas_buffer[str(cuenta_id).strip()] = buffer

            plt.close(fig)

        return graficas_buffer

    else:
        return None
