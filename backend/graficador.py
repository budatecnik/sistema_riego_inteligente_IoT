import sqlite3
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import os

# ==========================================
# BACKEND NATIVO
# ==========================================
plt.switch_backend('TkAgg')

# ==========================================
# DB PATH
# ==========================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(BASE_DIR, "iot.db")

# ==========================================
# FIGURA GLOBAL
# ==========================================
fig, ax1 = plt.subplots(figsize=(13, 7))
ax2 = ax1.twinx()


def actualizar(frame):

    try:

        conexion = sqlite3.connect(db_path)
        cursor = conexion.cursor()

        cursor.execute("""
            SELECT temperatura, humedad, humedad_suelo
            FROM lecturas
            ORDER BY id DESC
            LIMIT 20
        """)

        filas = cursor.fetchall()
        conexion.close()

        if not filas:
            return

        filas.reverse()

        temperaturas = [f[0] for f in filas]
        humedades = [f[1] for f in filas]

        # SENSOR SUELO %
        suelos = [f[2] for f in filas]

        tiempos = list(range(len(filas)))

        # ==========================================
        # LIMPIAR EJES
        # ==========================================
        ax1.clear()
        ax2.clear()

        # ==========================================
        # DARK MODE
        # ==========================================
        fig.patch.set_facecolor('#111111')
        ax1.set_facecolor('#1b1b1b')

        # ==========================================
        # TEMPERATURA
        # ==========================================
        ax1.plot(
            tiempos,
            temperaturas,
            color='#ff5733',
            marker='o',
            linewidth=3,
            markersize=7,
            label='Temperatura °C'
        )

        ax1.set_ylabel(
            'Temperatura °C',
            color='#ff5733',
            fontsize=12,
            fontweight='bold'
        )

        ax1.tick_params(axis='y', colors='#ff5733')
        ax1.tick_params(axis='x', colors='white')

        ax1.set_ylim(0, 50)

        # ==========================================
        # HUMEDAD
        # ==========================================
        ax2.plot(
            tiempos,
            humedades,
            color='#00d4ff',
            marker='s',
            linewidth=3,
            markersize=6,
            label='Humedad Ambiente %'
        )

        ax2.plot(
            tiempos,
            suelos,
            color='#39ff14',
            marker='^',
            linewidth=3,
            markersize=6,
            label='Humedad Suelo %'
        )

        ax2.set_ylabel(
            'Humedad %',
            color='white',
            fontsize=12,
            fontweight='bold'
        )

        ax2.tick_params(axis='y', colors='white')
        ax2.set_ylim(0, 100)

        # ==========================================
        # GRID
        # ==========================================
        ax1.grid(
            True,
            linestyle='--',
            alpha=0.3
        )

        # ==========================================
        # TÍTULO
        # ==========================================
        plt.title(
            "🌿 Smart Garden - Telemetría en Tiempo Real",
            fontsize=18,
            color='white',
            fontweight='bold'
        )

        # ==========================================
        # LEYENDAS
        # ==========================================
        lineas_1, etiquetas_1 = ax1.get_legend_handles_labels()
        lineas_2, etiquetas_2 = ax2.get_legend_handles_labels()

        legend = ax1.legend(
            lineas_1 + lineas_2,
            etiquetas_1 + etiquetas_2,
            loc='upper left'
        )

        legend.get_frame().set_facecolor('#222222')
        legend.get_frame().set_edgecolor('white')

        fig.tight_layout()

    except Exception as e:
        print(f"\n❌ Error: {e}")


# ==========================================
# ANIMACIÓN
# ==========================================
ani = FuncAnimation(
    fig,
    actualizar,
    interval=2000
)

# ==========================================
# MOSTRAR
# ==========================================
plt.show()
