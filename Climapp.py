import sys
import sqlite3
import requests
import json
from datetime import datetime
import pytz
from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout,
QWidget, QLineEdit, QPushButton, QCompleter, QListWidget, QListWidgetItem,
QMessageBox, QLabel, QComboBox, QFrame, QScrollArea)
from PyQt5.QtCore import Qt, QStringListModel
from PyQt5.QtGui import QFont, QIcon
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from PyQt5.QtCore import Qt, QStringListModel, QTimer

API_KEY = "43a8ddcac3f6d147859d707bac743ab2"

class MarcoClima(QFrame):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border-radius: 10px;
                padding: 15px;
            }
            QLabel {
                color: #333333;
                font-size: 14px;
            }
            QLabel#temperatura {
                font-size: 36px;
                font-weight: bold;
            }
        """)
        self.diseño = QVBoxLayout()
        self.setLayout(self.diseño)

        self.etiqueta_ciudad = QLabel()
        self.etiqueta_temperatura = QLabel()
        self.etiqueta_temperatura.setObjectName("temperaturo")
        self.etiqueta_humedad = QLabel()
        self.etiqueta_viento = QLabel()
        self.etiqueta_presion = QLabel()
        self.etiqueta_visibilidad = QLabel()
        self.etiqueta_prob_lluvia = QLabel()


        self.diseño.addWidget(self.etiqueta_ciudad)
        self.diseño.setSpacing(3)
        self.diseño.addWidget(self.etiqueta_temperatura)
        self.diseño.setSpacing(3)
        self.diseño.addWidget(self.etiqueta_humedad)
        self.diseño.setSpacing(3)
        self.diseño.addWidget(self.etiqueta_viento)
        self.diseño.setSpacing(3)
        self.diseño.addWidget(self.etiqueta_presion)
        self.diseño.setSpacing(3)
        self.diseño.addWidget(self.etiqueta_visibilidad)
        self.diseño.setSpacing(3)
        self.diseño.addWidget(self.etiqueta_prob_lluvia)


class AplicacionClima(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Pronóstico del Tiempo")
        self.setGeometry(100, 100, 1200, 800)
        self.setStyleSheet(
            """
            QMainWindow {
                background-color: #f0f2f5;
            }
            QPushButton {
                background-color: #4a90e2;
                color: white;
                border: none;
                padding: 8px 15px;
                border-radius: 5px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #357abd;
            }
            QLineEdit {
                padding: 8px;
                border: 1px solid #ddd;
                border-radius: 5px;
                font-size: 14px;
            }
            QComboBox {
                padding: 8px;
                border: 1px solid #ddd;
                border-radius: 5px;
            }
        """
        )

        contenedor_principal = QWidget()
        self.setCentralWidget(contenedor_principal)
        diseño_contenedor = QVBoxLayout()
        contenedor_principal.setLayout(diseño_contenedor)

        area_desplazamiento = QScrollArea()
        area_desplazamiento.setWidgetResizable(True)
        area_desplazamiento.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        area_desplazamiento.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        diseño_contenedor.addWidget(area_desplazamiento)

        widget_contenido = QWidget()
        area_desplazamiento.setWidget(widget_contenido)
        diseño_principal = QHBoxLayout()
        widget_contenido.setLayout(diseño_principal)

        widget_contenido.setMinimumHeight(900)

        widget_izquierdo = QWidget()
        diseño_izquierdo = QVBoxLayout()
        widget_izquierdo.setLayout(diseño_izquierdo)

        widget_busqueda = QWidget()
        diseño_busqueda = QHBoxLayout()
        widget_busqueda.setLayout(diseño_busqueda)

        self.entrada_ubicacion = QLineEdit()
        self.entrada_ubicacion.setPlaceholderText("Buscar ubicación...")
        diseño_busqueda.addWidget(self.entrada_ubicacion)

        boton_buscar = QPushButton("Buscar")
        boton_buscar.clicked.connect(self.buscar_ubicacion)
        diseño_busqueda.addWidget(boton_buscar)

        boton_ubicacion_actual = QPushButton("Usar Ubicación Actual")
        boton_ubicacion_actual.clicked.connect(self.obtener_clima_ubicacion_actual)
        diseño_busqueda.addWidget(boton_ubicacion_actual)

        diseño_izquierdo.addWidget(widget_busqueda)

        widget_unidades = QWidget()
        diseño_unidades = QHBoxLayout()
        widget_unidades.setLayout(diseño_unidades)

        self.unidad_temperatura = QComboBox()
        self.unidad_temperatura.addItems(["Celsius", "Fahrenheit"])
        self.unidad_temperatura.currentTextChanged.connect(
            lambda: self.actualizar_visualizacion_clima(self.datos_clima_actual)
        )
        diseño_unidades.addWidget(QLabel("Temperatura:"))
        diseño_unidades.addWidget(self.unidad_temperatura)

        self.unidad_viento = QComboBox()
        self.unidad_viento.addItems(["km/h", "m/s"])
        self.unidad_viento.currentTextChanged.connect(
            lambda: self.actualizar_visualizacion_clima(self.datos_clima_actual)
        )
        diseño_unidades.addWidget(QLabel("Viento:"))
        diseño_unidades.addWidget(self.unidad_viento)

        diseño_izquierdo.addWidget(widget_unidades)

        self.widget_clima = MarcoClima()
        diseño_izquierdo.addWidget(self.widget_clima)

        self.figura, self.eje = plt.subplots(figsize=(10, 6))
        self.lienzo = FigureCanvas(self.figura)
        self.lienzo.setMinimumHeight(400)
        diseño_izquierdo.addWidget(self.lienzo)

        diseño_izquierdo.addStretch()
        diseño_principal.addWidget(widget_izquierdo, stretch=2)

        widget_derecho = QWidget()
        diseño_derecho = QVBoxLayout()
        widget_derecho.setLayout(diseño_derecho)

        etiqueta_ubicaciones_guardadas = QLabel("Ubicaciones Guardadas")
        etiqueta_ubicaciones_guardadas.setStyleSheet("font-size: 16px; font-weight: bold;")
        diseño_derecho.addWidget(etiqueta_ubicaciones_guardadas)

        self.lista_ubicaciones_guardadas = QListWidget()
        self.lista_ubicaciones_guardadas.itemClicked.connect(self.cargar_ubicacion_guardada)
        diseño_derecho.addWidget(self.lista_ubicaciones_guardadas)

        boton_guardar = QPushButton("Guardar Ubicación Actual")
        boton_guardar.clicked.connect(self.guardar_ubicacion_actual)
        diseño_derecho.addWidget(boton_guardar)

        boton_eliminar = QPushButton("Eliminar Ubicación")
        boton_eliminar.clicked.connect(self.eliminar_ubicacion_seleccionada)
        diseño_derecho.addWidget(boton_eliminar)

        diseño_principal.addWidget(widget_derecho, stretch=1)

        self.crear_base_datos()
        self.cargar_ubicaciones_guardadas()

        self.datos_clima_actual = None


        self.completer = QCompleter()
        self.completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.completer.activated.connect(self.on_completer_activated)
        self.entrada_ubicacion.setCompleter(self.completer)
        self.model = QStringListModel()
        self.completer.setModel(self.model)

        self.timer = QTimer()
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.fetch_autocomplete_suggestions)


        self.entrada_ubicacion.textChanged.connect(self.start_timer)

    def calcular_probabilidad_lluvia(self, datos):
        """Calcula la probabilidad de lluvia basada en los datos meteorológicos."""
        humedad = datos["main"]["humidity"]
        presion = datos["main"]["pressure"]

        prob_humedad = humedad / 100
        prob_presion = (1013 - presion) / 100


        prob_lluvia = prob_humedad * (1 - prob_presion)

        return min(max(prob_lluvia, 0), 1)

    def crear_base_datos(self):
        conexion = sqlite3.connect("clima.db")
        cursor = conexion.cursor()
        cursor.execute(
            """CREATE TABLE IF NOT EXISTS ubicaciones
                (id INTEGER PRIMARY KEY, nombre TEXT, latitud REAL, longitud REAL)"""
        )
        conexion.commit()
        conexion.close()

    def buscar_ubicacion(self):
        ubicacion = self.entrada_ubicacion.text()
        url = (
            f"http://api.openweathermap.org/geo/1.0/direct?q={ubicacion}&limit=1&appid={API_KEY}"
        )
        try:
            respuesta = requests.get(url)
            datos = respuesta.json()
            if datos:
                latitud = datos[0]["lat"]
                longitud = datos[0]["lon"]
                self.obtener_datos_clima(latitud, longitud)
            else:
                QMessageBox.warning(self, "Error", "Ubicación no encontrada")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al buscar ubicación: {str(e)}")

    def obtener_datos_clima(self, latitud, longitud):
        url_clima = f"http://api.openweathermap.org/data/2.5/weather?lat={latitud}&lon={longitud}&appid={API_KEY}&units=metric"
        url_pronostico = f"http://api.openweathermap.org/data/2.5/forecast?lat={latitud}&lon={longitud}&appid={API_KEY}&units=metric"
        try:
            respuesta_clima = requests.get(url_clima)
            respuesta_pronostico = requests.get(url_pronostico)
            datos_clima = respuesta_clima.json()
            datos_pronostico = respuesta_pronostico.json()
            self.datos_clima_actual = datos_clima
            self.actualizar_visualizacion_clima(datos_clima)
            self.actualizar_grafico_pronostico(datos_pronostico)
        except Exception as e:
            QMessageBox.critical(
                self, "Error", f"Error al obtener datos del clima: {str(e)}"
            )

    def actualizar_visualizacion_clima(self, datos):
        if not datos or not isinstance(datos, dict):
            return
        temperatura = datos["main"]["temp"]
        if self.unidad_temperatura.currentText() == "Fahrenheit":
            temperatura = (temperatura * 9 / 5) + 32
            unidad_temp = "°F"
        else:
            unidad_temp = "°C"

        velocidad_viento = datos["wind"]["speed"]
        if self.unidad_viento.currentText() == "km/h":
            velocidad_viento *= 3.6
            unidad_viento_str = "km/h"
        else:
            unidad_viento_str = "m/s"

        self.widget_clima.etiqueta_ciudad.setText(f"Ciudad: {datos['name']}")
        self.widget_clima.etiqueta_temperatura.setText(
            f"Temperatura: {temperatura:.1f}{unidad_temp}"
        )
        self.widget_clima.etiqueta_humedad.setText(f"Humedad: {datos['main']['humidity']}%")
        self.widget_clima.etiqueta_viento.setText(
            f"Viento: {velocidad_viento:.1f} {unidad_viento_str}"
        )
        self.widget_clima.etiqueta_presion.setText(f"Presión: {datos['main']['pressure']} hPa")
        self.widget_clima.etiqueta_visibilidad.setText(
            f"Visibilidad: {datos['visibility']/1000:.1f} km"
        )


        prob_lluvia = self.calcular_probabilidad_lluvia(datos)
        self.widget_clima.etiqueta_prob_lluvia.setText(
            f"Probabilidad de Lluvia: {prob_lluvia * 100:.1f}%"
        )

    def actualizar_grafico_pronostico(self, datos_pronostico):
        self.eje.clear()
        tiempos = []
        temperaturas = []
        for elemento in datos_pronostico["list"][:8]:
            fecha_hora = datetime.fromtimestamp(elemento["dt"])
            tiempos.append(fecha_hora.strftime("%H:%M"))
            temperaturas.append(elemento["main"]["temp"])
        self.eje.plot(tiempos, temperaturas, marker="o")
        self.eje.set_xlabel("Hora")
        self.eje.set_ylabel("Temperatura (°C)")
        self.eje.set_title("Pronóstico de temperatura para las próximas 24 horas")
        plt.xticks(rotation=45)
        self.eje.grid(True)
        self.figura.tight_layout()
        self.lienzo.draw()

    def guardar_ubicacion_actual(self):
        ubicacion = self.entrada_ubicacion.text()
        if not ubicacion:
            QMessageBox.warning(self, "Error", "Por favor ingrese una ubicación")
            return
        try:
            conexion = sqlite3.connect("clima.db")
            cursor = conexion.cursor()
            cursor.execute("INSERT INTO ubicaciones (nombre) VALUES (?)", (ubicacion,))
            conexion.commit()
            conexion.close()
            self.cargar_ubicaciones_guardadas()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al guardar ubicación: {str(e)}")

    def cargar_ubicaciones_guardadas(self):
        self.lista_ubicaciones_guardadas.clear()
        conexion = sqlite3.connect("clima.db")
        cursor = conexion.cursor()
        cursor.execute("SELECT nombre FROM ubicaciones")
        ubicaciones = cursor.fetchall()
        conexion.close()
        for ubicacion in ubicaciones:
            self.lista_ubicaciones_guardadas.addItem(ubicacion[0])

    def cargar_ubicacion_guardada(self, elemento):
        self.entrada_ubicacion.setText(elemento.text())
        self.buscar_ubicacion()

    def eliminar_ubicacion_seleccionada(self):
        elemento_actual = self.lista_ubicaciones_guardadas.currentItem()
        if not elemento_actual:
            return
        try:
            conexion = sqlite3.connect("clima.db")
            cursor = conexion.cursor()
            cursor.execute(
                "DELETE FROM ubicaciones WHERE nombre = ?", (elemento_actual.text(),)
            )
            conexion.commit()
            conexion.close()
            self.cargar_ubicaciones_guardadas()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al eliminar ubicación: {str(e)}")

    def obtener_clima_ubicacion_actual(self):
        try:
            respuesta_ip = requests.get("http://ip-api.com/json/")
            respuesta_ip.raise_for_status()
            datos_ip = respuesta_ip.json()
            if datos_ip["status"] != "success":
                raise Exception("No se pudo obtener la información de la ubicación.")
            latitud = datos_ip["lat"]
            longitud = datos_ip["lon"]
            self.obtener_datos_clima(latitud, longitud)
        except requests.exceptions.HTTPError as error_http:
            QMessageBox.warning(self, "Error", f"Ocurrió un error HTTP: {error_http}")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Error al obtener la ubicación: {e}")

    def start_timer(self):

        self.timer.start(1)

    def fetch_autocomplete_suggestions(self):

        query = self.entrada_ubicacion.text()
        if not query:
            return
        url = (
            f"http://api.openweathermap.org/geo/1.0/direct?q={query}&limit=5&appid={API_KEY}"
        )
        try:
            response = requests.get(url)
            data = response.json()
            if isinstance(data, list):
                suggestions = [item["name"] for item in data]
                self.model.setStringList(suggestions)
            else:
                self.model.setStringList([])
        except Exception as e:
            print(f"Error fetching autocomplete suggestions: {e}")
            self.model.setStringList([])

    def on_completer_activated(self, text):

        self.entrada_ubicacion.setText(text)
        self.buscar_ubicacion()

if __name__ == "__main__":
    aplicacion = QApplication(sys.argv)
    ventana = AplicacionClima()
    ventana.show()
    sys.exit(aplicacion.exec_())