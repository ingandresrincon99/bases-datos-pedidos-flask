"""
Aplicación web Flask para el sistema de análisis de pedidos.
Proporciona rutas para visualización de datos, estadísticas y preprocesamiento.

Esta aplicación sirve como interfaz web para consultar y visualizar datos
de la base de datos pedidos11, incluyendo análisis estadísticos y
herramientas de preprocesamiento de datos.

Autor: Fabian Andrés Rincón
Fecha: Febrero 2026
"""

import os
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

from flask import Flask, render_template, jsonify, request
from dotenv import load_dotenv

# Importar configuración centralizada
from config import config_by_name
from database import db

# Importar módulo de preprocesamiento
from fpreprocesamiento import preprocesamiento

# Cargar variables de entorno desde archivo .env
load_dotenv()

# Configuración del sistema de logging
# Se establece el nivel INFO para registrar eventos importantes
# El formato incluye timestamp, nombre del módulo, nivel y mensaje
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Crear instancia de la aplicación Flask
app = Flask(__name__)

# Determinar el entorno de ejecución (development, production, etc.)
# Por defecto se usa 'development' si no se especifica
env = os.getenv('FLASK_ENV', 'development')
# Cargar configuración específica para el entorno
app.config.from_object(config_by_name[env])

# Verificar la conexión a la base de datos al iniciar la aplicación
# Esto permite detectar problemas de configuración tempranamente
try:
    if db.test_connection():
        logger.info("Conexión a base de datos establecida correctamente")
    else:
        logger.error("No se pudo conectar a la base de datos")
        logger.error("Verifica que el archivo .env existe y tiene las credenciales correctas")
except Exception as e:
    logger.error(f"Error conectando a base de datos: {e}")
    logger.error("Verifica que el archivo .env existe y tiene las credenciales correctas")


# ============================================================================
# CLASES AUXILIARES
# ============================================================================

class DataFormatter:
    """
    Clase auxiliar para formatear datos para las respuestas JSON.
    
    Proporciona métodos estáticos para convertir DataFrames de pandas
    a formatos compatibles con bibliotecas de visualización como Chart.js.
    """
    
    @staticmethod
    def dataframe_to_chart(df, label_col: str, data_col: str, titulo: str) -> Dict:
        """
        Convierte un DataFrame a formato para Chart.js.
        
        Args:
            df: DataFrame con los datos
            label_col: Nombre de columna para las etiquetas del eje X
            data_col: Nombre de columna para los valores del eje Y
            titulo: Título del gráfico
            
        Returns:
            Diccionario con formato compatible con Chart.js
            Incluye las claves 'labels', 'data' y 'titulo'
        """
        if df is None or df.empty:
            return {"error": "No hay datos disponibles", "titulo": titulo}
        
        return {
            "labels": df[label_col].tolist() if label_col in df.columns else [],
            "data": df[data_col].tolist() if data_col in df.columns else [],
            "titulo": titulo
        }
    
    @staticmethod
    def safe_float_conversion(value, default: float = 0.0) -> float:
        """
        Convierte un valor a float de forma segura.
        
        Args:
            value: Valor a convertir
            default: Valor por defecto si la conversión falla
            
        Returns:
            Valor convertido a float o el valor por defecto
        """
        try:
            return float(value)
        except (TypeError, ValueError):
            return default


class AppData:
    """
    Maneja los datos cacheados de la aplicación.
    
    Esta clase implementa un caché simple para datos que se consultan
    frecuentemente, evitando múltiples consultas a la base de datos.
    Los datos se refrescan automáticamente cuando se accede a ellos
    por primera vez.
    """
    
    def __init__(self):
        """Inicializa el caché vacío."""
        self._df_emp = None
        self._cantidad_emp = 0
        self._last_refresh = None
    
    @property
    def df_emp(self):
        """
        DataFrame de empleados (cargado una sola vez).
        
        Returns:
            DataFrame con datos de empleados o None si hay error
        """
        if self._df_emp is None:
            self._refresh_data()
        return self._df_emp
    
    @property
    def cantidad_emp(self):
        """
        Cantidad de empleados.
        
        Returns:
            Número de empleados en la base de datos
        """
        if self._df_emp is None:
            self._refresh_data()
        return self._cantidad_emp
    
    def _refresh_data(self):
        """Refresca los datos desde la base de datos."""
        try:
            self._df_emp = preprocesamiento.lee_archivo()
            self._cantidad_emp = len(self._df_emp) if self._df_emp is not None and not self._df_emp.empty else 0
            self._last_refresh = datetime.now()
            logger.info(f"Datos refrescados: {self._cantidad_emp} empleados")
        except Exception as e:
            logger.error(f"Error refrescando datos: {e}")
            self._df_emp = None
            self._cantidad_emp = 0


# Instancia global de datos para toda la aplicación
app_data = AppData()


# ============================================================================
# ENDPOINTS DE API - GRÁFICOS Y VISUALIZACIONES
# ============================================================================

@app.route("/api/datos-grafico")
def datos_grafico():
    """
    Endpoint para datos del gráfico principal.
    
    Retorna los datos de productos por categoría en formato
    compatible con Chart.js para el dashboard principal.
    
    Returns:
        JSON con labels, datos y título del gráfico
    """
    try:
        df = app_data.df_emp
        if df is None or df.empty:
            return jsonify({"error": "No hay datos disponibles"}), 404
        
        logger.debug(f"Columnas disponibles: {df.columns.tolist()}")
        
        # Verificar que las columnas necesarias existen
        if 'Categoria' not in df.columns or 'Cantidad' not in df.columns:
            return jsonify({"error": "Estructura de datos incorrecta"}), 500
        
        return jsonify({
            'labels': df['Categoria'].tolist(),
            'data': df['Cantidad'].tolist(),
            'titulo': "Cantidad de productos por categoría"
        })
    except Exception as e:
        logger.error(f"Error en datos_grafico: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/pedidos-forma-pago")
def pedidos_forma_pago():
    """
    Endpoint para pedidos por forma de pago.
    
    Retorna la distribución de pedidos según su forma de pago
    (efectivo, crédito, etc.) para gráficos circulares.
    
    Returns:
        JSON con datos formateados para Chart.js
    """
    try:
        df = preprocesamiento.pedidos_por_forma_pago()
        if df is None:
            return jsonify({"error": "Error al obtener datos"}), 500
            
        return jsonify(
            DataFormatter.dataframe_to_chart(
                df, "forma_pago", "porcentaje",
                "Porcentaje de pedidos por forma de pago"
            )
        )
    except Exception as e:
        logger.error(f"Error en pedidos_forma_pago: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/pedidos-por-anio")
def pedidos_por_anio():
    """
    Endpoint para pedidos por año.
    
    Retorna la cantidad de pedidos agrupados por año para
    visualizar tendencias temporales.
    
    Returns:
        JSON con datos formateados para gráfico de barras
    """
    try:
        df = preprocesamiento.pedidos_por_anio()
        if df is None:
            return jsonify({"error": "Error al obtener datos"}), 500
            
        return jsonify(
            DataFormatter.dataframe_to_chart(
                df, "anio", "cantidad_pedidos",
                "Cantidad de pedidos por año"
            )
        )
    except Exception as e:
        logger.error(f"Error en pedidos_por_anio: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/empleados-burbuja")
def empleados_departamento():
    """
    Endpoint para empleados por departamento.
    
    Retorna la distribución de empleados según su departamento
    para visualización en gráficos de burbujas o barras.
    
    Returns:
        JSON con datos formateados para Chart.js
    """
    try:
        df = preprocesamiento.empleados_por_departamento()
        if df is None:
            return jsonify({"error": "Error al obtener datos"}), 500
            
        return jsonify(
            DataFormatter.dataframe_to_chart(
                df, "departamento", "cantidad",
                "Empleados por departamento"
            )
        )
    except Exception as e:
        logger.error(f"Error en empleados_departamento: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/pedidos-empleado")
def pedidos_empleado():
    """
    Endpoint para pedidos atendidos por empleado.
    
    Retorna el ranking de empleados según la cantidad de pedidos
    que han atendido.
    
    Returns:
        JSON con datos formateados para Chart.js
    """
    try:
        df = preprocesamiento.pedidos_atendidos_por_empleado()
        if df is None:
            return jsonify({"error": "Error al obtener datos"}), 500
            
        return jsonify(
            DataFormatter.dataframe_to_chart(
                df, "empleado", "cantidad_pedidos",
                "Pedidos atendidos por empleado"
            )
        )
    except Exception as e:
        logger.error(f"Error en pedidos_empleado: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/producto-mas-vendido")
def api_producto_mas_vendido():
    """
    Endpoint para producto más vendido.
    
    Retorna el producto con mayor cantidad total vendida.
    
    Returns:
        JSON con nombre del producto y cantidad vendida
    """
    try:
        df = preprocesamiento.producto_mas_vendido()
        if df is None or df.empty:
            return jsonify({"error": "No se encontraron datos"}), 404
        
        return jsonify({
            "producto": df["producto"].iloc[0],
            "cantidad": int(df["total_vendido"].iloc[0])
        })
    except Exception as e:
        logger.error(f"Error en producto_mas_vendido: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/producto-mas-solicitado")
def api_producto_mas_solicitado():
    """
    Endpoint para producto más solicitado.
    
    Retorna el producto que aparece en más pedidos distintos.
    
    Returns:
        JSON con nombre del producto y número de pedidos
    """
    try:
        df = preprocesamiento.producto_mas_solicitado()
        if df is None or df.empty:
            return jsonify({"error": "No se encontraron datos"}), 404
        
        return jsonify({
            "producto": df["producto"].iloc[0],
            "veces_solicitado": int(df["veces_solicitado"].iloc[0])
        })
    except Exception as e:
        logger.error(f"Error en producto_mas_solicitado: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/top-clientes")
def api_top_clientes():
    """
    Endpoint para top clientes por valor facturado.
    
    Retorna los 5 clientes con mayor valor en facturación.
    
    Returns:
        JSON con datos formateados para Chart.js
    """
    try:
        df = preprocesamiento.top_clientes_por_valor()
        if df is None:
            return jsonify({"error": "Error al obtener datos"}), 500
            
        return jsonify(
            DataFormatter.dataframe_to_chart(
                df, "cliente", "valor_facturado",
                "Top 5 clientes por valor facturado"
            )
        )
    except Exception as e:
        logger.error(f"Error en top_clientes: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/top-productos")
def api_top_productos():
    """
    Endpoint para top productos más vendidos.
    
    Retorna los 5 productos con mayor cantidad vendida,
    incluyendo valor total facturado.
    
    Returns:
        JSON con lista de productos y sus métricas
    """
    try:
        df = preprocesamiento.top_productos_mas_vendidos()
        if df is None or df.empty:
            return jsonify({"error": "No se encontraron datos"}), 404
        
        return jsonify({"productos": df.to_dict(orient="records")})
    except Exception as e:
        logger.error(f"Error en top_productos: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/top-productos-solicitados")
def api_top_productos_solicitados():
    """
    Endpoint para top productos más solicitados.
    
    Retorna los 5 productos que aparecen en más pedidos distintos.
    
    Returns:
        JSON con lista de productos y sus métricas
    """
    try:
        df = preprocesamiento.top_productos_mas_solicitados()
        if df is None or df.empty:
            return jsonify({"error": "No se encontraron datos"}), 404
        
        return jsonify({"productos": df.to_dict(orient="records")})
    except Exception as e:
        logger.error(f"Error en top_productos_solicitados: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/empleados-lugar-coincide")
def api_empleados_lugar_coincide():
    """
    Endpoint para empleados con lugar coincide.
    
    Retorna la cantidad de empleados que tienen el mismo lugar
    de nacimiento, residencia y trabajo.
    
    Returns:
        JSON con cantidad de empleados y título descriptivo
    """
    try:
        df = preprocesamiento.empleados_lugar_coincide()
        if df is None or df.empty:
            return jsonify({"error": "No se encontraron datos"}), 404
        
        return jsonify({
            "cantidad": int(df["empleados_coinciden"].iloc[0]),
            "titulo": "Empleados con lugar de nacimiento, residencia y trabajo coincidente"
        })
    except Exception as e:
        logger.error(f"Error en empleados_lugar_coincide: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/pedidos-por-mes")
def api_pedidos_por_mes():
    """
    Endpoint para pedidos por mes (formato especial para gráfico de líneas).
    
    Retorna datos de pedidos agrupados por mes y año para
    visualización en gráfico de líneas múltiples.
    
    Returns:
        JSON con estructura para gráfico de líneas de Chart.js
    """
    try:
        df = preprocesamiento.pedidos_por_mes()
        if df is None or df.empty:
            return jsonify({"error": "No se encontraron datos"}), 404
        
        # Procesar datos para gráfico de líneas
        meses = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", 
                 "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
        
        datos_por_anio = {}
        for _, fila in df.iterrows():
            anio = str(fila["anio"])
            mes = int(fila["mes"])
            cantidad = int(fila["cantidad_pedidos"])
            
            if anio not in datos_por_anio:
                datos_por_anio[anio] = [0] * 12
            datos_por_anio[anio][mes - 1] = cantidad
        
        datasets = []
        for anio in sorted(datos_por_anio.keys()):
            datasets.append({
                "label": anio,
                "data": datos_por_anio[anio],
                "borderColor": f"hsl({hash(anio) % 360}, 70%, 50%)",
                "fill": False
            })
        
        return jsonify({
            "labels": meses,
            "datasets": datasets
        })
    except Exception as e:
        logger.error(f"Error en pedidos_por_mes: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/empleados-mejor-pagados")
def empleados_mejor_pagados():
    """
    Endpoint para empleados mejor pagados.
    
    Retorna los 5 empleados con los salarios más altos.
    
    Returns:
        JSON con columnas y valores para tabla
    """
    try:
        df = preprocesamiento.top_empleados_mejor_pagados()
        if df is None or df.empty:
            return jsonify({"error": "No se encontraron datos"}), 404
        
        return jsonify({
            "titulo": "Top 5 Empleados con los Salarios Más Altos",
            "columnas": df.columns.tolist(),
            "valores": df.values.tolist()
        })
    except Exception as e:
        logger.error(f"Error en empleados_mejor_pagados: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/valor-nomina")
def api_valor_nomina():
    """
    Endpoint para valor total de nómina.
    
    Retorna la suma total de salarios de todos los empleados.
    
    Returns:
        JSON con título y valor formateado
    """
    try:
        df = preprocesamiento.valor_nomina_total()
        if df is None or df.empty:
            return jsonify({"error": "No se encontraron datos"}), 404
        
        valor = float(df["Valor_Nomina_Total"].iloc[0])
        return jsonify({
            "titulo": "Valor total de la nómina",
            "valor": f"${valor:,.2f}"
        })
    except Exception as e:
        logger.error(f"Error en valor_nomina: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/nomina-departamento")
def api_nomina_departamento():
    """
    Endpoint para nómina por departamento.
    
    Retorna la distribución de la nómina total por departamento.
    
    Returns:
        JSON con datos formateados para Chart.js
    """
    try:
        df = preprocesamiento.nomina_por_departamento()
        if df is None:
            return jsonify({"error": "Error al obtener datos"}), 500
            
        return jsonify(
            DataFormatter.dataframe_to_chart(
                df, "departamento", "valor_nomina",
                "Valor de la Nómina por Departamento"
            )
        )
    except Exception as e:
        logger.error(f"Error en nomina_departamento: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/comision-empleados")
def api_comision_empleados():
    """
    Endpoint para porcentaje de comisión por empleado.
    
    Retorna los 5 empleados con mayor porcentaje de comisión.
    
    Returns:
        JSON con datos formateados para Chart.js
    """
    try:
        df = preprocesamiento.porcentaje_comision_empleado_top5()
        
        if df is None:
            return jsonify({"error": "Error en el servidor al obtener datos"}), 500
        if df.empty:
            return jsonify({"error": "No hay empleados con comisión registrada"}), 404
        
        return jsonify({
            "labels": df["empleado"].tolist(),
            "data": [round(float(x), 2) for x in df["porcentaje_comision"].tolist()],
            "titulo": "Top 5 - Porcentaje de comisión por empleado"
        })
    except Exception as e:
        logger.error(f"Error en comision_empleados: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/empleados-lugar-igual")
def empleados_lugar_igual():
    """
    Endpoint para empleados con mismo lugar.
    
    Retorna los empleados que tienen el mismo lugar de nacimiento,
    residencia y trabajo, con los detalles de cada uno.
    
    Returns:
        JSON con listas de empleados y lugares
    """
    try:
        df = preprocesamiento.empleados_lugar_igual()
        
        if df is None or df.empty:
            return jsonify({"error": "No se encontraron empleados con coincidencia de lugar"}), 404
        
        return jsonify({
            "empleados": df["nombre_completo"].tolist(),
            "lugares": df["lugar"].tolist(),
            "titulo": "Empleados cuyo lugar de nacimiento, residencia y trabajo es el mismo"
        })
    except Exception as e:
        logger.error(f"Error en empleados_lugar_igual: {e}")
        return jsonify({"error": f"Error del servidor: {str(e)}"}), 500


# ============================================================================
# ENDPOINTS DE API - SISTEMA Y USUARIO
# ============================================================================

@app.route("/api/user-info")
def user_info():
    """
    Información del usuario actual.
    
    Retorna datos básicos del usuario para la interfaz.
    
    Returns:
        JSON con nombre, avatar, rol y último acceso
    """
    return jsonify({
        "name": "Administrador PEDIDOS",
        "avatar": "../static/img/undraw_profile.svg",
        "role": "Administrador",
        "last_login": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })


@app.route("/api/alerts")
def get_alerts():
    """
    Alertas del sistema.
    
    Retorna una lista de alertas para mostrar en el panel de notificaciones.
    
    Returns:
        JSON con lista de alertas
    """
    alerts = [
        {
            "id": 1,
            "type": "bg-warning",
            "icon": "fa-exclamation-triangle",
            "message": "Stock bajo en producto 'Widget X'",
            "time": "Hace 5 minutos",
            "read": False,
            "link": "/tables/productos"
        },
        {
            "id": 2,
            "type": "bg-success",
            "icon": "fa-chart-line",
            "message": "Reporte mensual generado exitosamente",
            "time": "Hace 1 hora",
            "read": True,
            "link": "/reports"
        },
        {
            "id": 3,
            "type": "bg-info",
            "icon": "fa-database",
            "message": "Backup de base de datos completado",
            "time": "Ayer, 02:30 AM",
            "read": True,
            "link": "#"
        }
    ]
    return jsonify(alerts)


@app.route("/api/messages")
def get_messages():
    """
    Mensajes del sistema.
    
    Retorna una lista de mensajes para el panel de comunicaciones.
    
    Returns:
        JSON con lista de mensajes
    """
    messages = [
        {
            "id": 1,
            "sender": "Sistema de Pedidos",
            "avatar": "../static/img/undraw_profile_1.svg",
            "content": "Nuevo pedido recibido #12345",
            "time": "Hace 15 minutos",
            "status": "bg-success",
            "read": False,
            "link": "/tables/pedidos"
        },
        {
            "id": 2,
            "sender": "Departamento Financiero",
            "avatar": "../static/img/undraw_profile_2.svg",
            "content": "Recordatorio: Cierre mensual próximo viernes",
            "time": "Hace 2 horas",
            "status": "bg-warning",
            "read": True,
            "link": "#"
        },
        {
            "id": 3,
            "sender": "Soporte Técnico",
            "avatar": "../static/img/undraw_profile_3.svg",
            "content": "Mantenimiento programado para este fin de semana",
            "time": "Ayer, 10:00 AM",
            "status": "bg-info",
            "read": True,
            "link": "#"
        }
    ]
    return jsonify(messages)


@app.route("/api/user-profile")
def user_profile_api():
    """
    API para obtener datos del perfil.
    
    Retorna información detallada del usuario para la página de perfil.
    
    Returns:
        JSON con datos completos del perfil
    """
    return jsonify({
        'name': 'Fabian Rincon',
        'email': 'fabian.rincon@empresa.com',
        'role': 'Administrador del Sistema',
        'department': 'TI',
        'phone': '+57 300 123 4567',
        'join_date': '2023-01-15',
        'avatar': '../static/img/undraw_profile.svg',
        'bio': 'Especialista en análisis de datos y desarrollo de sistemas de gestión.'
    })


@app.route("/api/user-stats")
def user_stats():
    """
    Estadísticas del usuario.
    
    Retorna métricas resumidas para el dashboard.
    
    Returns:
        JSON con estadísticas de pedidos, clientes y productos
    """
    return jsonify({
        "orders": 1248,
        "clients": 89,
        "products": 456
    })


# ============================================================================
# RUTAS DE PÁGINAS HTML
# ============================================================================

@app.route('/')
def index():
    """
    Página principal (dashboard).
    
    Renderiza la plantilla del dashboard con la cantidad de empleados.
    
    Returns:
        Plantilla HTML renderizada
    """
    return render_template('index.html', cantidad_emp=app_data.cantidad_emp)


@app.route('/tables')
def tables():
    """
    Página de listado de tablas.
    
    Muestra todas las tablas disponibles en la base de datos.
    
    Returns:
        Plantilla HTML con lista de tablas
    """
    try:
        tablas = preprocesamiento.obtener_tablas_bd()
        return render_template('tables.html', tablas=tablas)
    except Exception as e:
        logger.error(f"Error en tables: {e}")
        return render_template('error.html', error=str(e)), 500


@app.route('/tables/<nombre_tabla>')
def ver_tabla(nombre_tabla):
    """
    Muestra los datos de una tabla específica.
    
    Args:
        nombre_tabla: Nombre de la tabla a visualizar
        
    Returns:
        Plantilla HTML con los datos de la tabla
    """
    try:
        datos_tabla = preprocesamiento.obtener_datos_tabla(nombre_tabla)
        tablas = preprocesamiento.obtener_tablas_bd()
        
        return render_template(
            'tabla_detalle.html',
            nombre_tabla=nombre_tabla,
            datos_tabla=datos_tabla,
            columnas=datos_tabla.columns.tolist() if datos_tabla is not None and not datos_tabla.empty else [],
            tablas=tablas
        )
    except Exception as e:
        logger.error(f"Error en ver_tabla {nombre_tabla}: {e}")
        return render_template('error.html', error=str(e)), 500


@app.route('/profile')
def profile():
    """
    Página de perfil del usuario.
    
    Renderiza la página de perfil con datos del usuario.
    
    Returns:
        Plantilla HTML con datos del perfil
    """
    user_data = {
        'name': 'Fabian Rincon',
        'email': 'fabian.rincon@empresa.com',
        'role': 'Administrador del Sistema',
        'department': 'TI',
        'phone': '+57 300 123 4567',
        'join_date': '2023-01-15',
        'avatar': '../static/img/undraw_profile.svg',
        'bio': 'Especialista en análisis de datos y desarrollo de sistemas de gestión.'
    }
    return render_template('profile.html', user=user_data)


@app.route('/estadisticas')
def estadisticas():
    """
    Página de análisis estadístico avanzado.
    
    Renderiza la interfaz para análisis estadístico de variables.
    
    Returns:
        Plantilla HTML de estadísticas
    """
    return render_template('estadisticas.html')


@app.route('/tratamiento')
def tratamiento():
    """
    Página de tratamiento y preprocesamiento de datos.
    
    Renderiza la interfaz para limpieza y transformación de datos.
    
    Returns:
        Plantilla HTML de tratamiento de datos
    """
    return render_template('tratamiento.html')


# ============================================================================
# ENDPOINTS DE API - ESTADÍSTICAS AVANZADAS
# ============================================================================

@app.route("/api/estadisticas/variables-cuantitativas")
def api_estadisticas_cuantitativas():
    """
    Estadísticas para variables cuantitativas.
    
    Retorna medidas estadísticas para variables numéricas como precios.
    
    Returns:
        JSON con estadísticas de precios
    """
    try:
        logger.info("Obteniendo estadísticas de precios...")
        stats_precios = preprocesamiento.obtener_estadisticas_precios()
        
        if stats_precios is None:
            return jsonify({"error": "No se pudieron obtener estadísticas de precios"}), 404
        
        logger.info(f"Estadísticas obtenidas exitosamente")
        return jsonify({"precios": stats_precios})
        
    except Exception as e:
        logger.error(f"Error en variables cuantitativas: {e}")
        return jsonify({"error": f"Error del servidor: {str(e)}"}), 500


@app.route("/api/estadisticas/variables-cualitativas")
def api_estadisticas_cualitativas():
    """
    Tablas de frecuencia usando funciones existentes.
    
    Retorna frecuencias y porcentajes para variables categóricas.
    
    Returns:
        JSON con datos de categorías y formas de pago
    """
    try:
        logger.info("Obteniendo datos cualitativos...")
        
        df_categorias = preprocesamiento.lee_archivo()
        df_formas_pago = preprocesamiento.pedidos_por_forma_pago()
        
        # Verificar DataFrames
        if df_categorias is None:
            df_categorias = pd.DataFrame()
        if df_formas_pago is None:
            df_formas_pago = pd.DataFrame()
        
        # Procesar categorías
        categorias_data = []
        if not df_categorias.empty and 'Cantidad' in df_categorias.columns:
            total_categorias = df_categorias['Cantidad'].sum()
            for _, row in df_categorias.iterrows():
                categorias_data.append({
                    "categoria": row.get('Categoria', 'Desconocido'),
                    "frecuencia": int(row['Cantidad']) if 'Cantidad' in row else 0,
                    "porcentaje": round((row['Cantidad'] / total_categorias) * 100, 2) if total_categorias > 0 else 0
                })
        
        # Procesar formas de pago
        formas_pago_data = []
        if not df_formas_pago.empty:
            for _, row in df_formas_pago.iterrows():
                formas_pago_data.append({
                    "forma_pago": row.get('forma_pago', 'Desconocido'),
                    "frecuencia": int(row['cantidad_pedidos']) if 'cantidad_pedidos' in row else 0,
                    "porcentaje": float(row['porcentaje']) if 'porcentaje' in row else 0
                })
        
        logger.info("Datos cualitativos obtenidos exitosamente")
        return jsonify({
            "categorias": categorias_data,
            "formas_pago": formas_pago_data
        })
        
    except Exception as e:
        logger.error(f"Error en variables cualitativas: {e}")
        return jsonify({"error": f"Error del servidor: {str(e)}"}), 500


@app.route("/api/estadisticas/medidas-dispersion")
def api_estadisticas_dispersion():
    """
    Medidas de dispersión.
    
    Retorna estadísticas de dispersión para salarios y cantidades.
    
    Returns:
        JSON con medidas de dispersión
    """
    try:
        logger.info("Obteniendo medidas de dispersión...")
        
        stats_salarios = preprocesamiento.obtener_estadisticas_salarios() or {}
        stats_cantidades = preprocesamiento.obtener_estadisticas_cantidades_pedidos() or {}
        
        logger.info("Medidas de dispersión obtenidas exitosamente")
        return jsonify({
            "salarios": stats_salarios,
            "cantidades_pedidos": stats_cantidades
        })
        
    except Exception as e:
        logger.error(f"Error en medidas de dispersión: {e}")
        return jsonify({"error": f"Error del servidor: {str(e)}"}), 500


@app.route("/api/estadisticas/test-conexion")
def test_conexion_estadisticas():
    """
    Prueba de conexión para estadísticas.
    
    Verifica que los endpoints de estadísticas respondan correctamente.
    
    Returns:
        JSON con estado de la conexión
    """
    try:
        stats_precios = preprocesamiento.obtener_estadisticas_precios()
        stats_salarios = preprocesamiento.obtener_estadisticas_salarios()
        
        return jsonify({
            "status": "success",
            "precios": "OK" if stats_precios else "ERROR",
            "salarios": "OK" if stats_salarios else "ERROR",
            "mensaje": "Conexión a estadísticas funcionando"
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "mensaje": f"Error en conexión: {str(e)}"
        }), 500


# ============================================================================
# ENDPOINTS DE API - TRATAMIENTO DE DATOS
# ============================================================================

@app.route("/api/tratamiento/valores-nulos")
def api_valores_nulos():
    """
    API para detectar valores nulos.
    
    Retorna información sobre valores nulos en todas las tablas.
    
    Returns:
        JSON con detección de valores nulos por tabla
    """
    try:
        resultados = preprocesamiento.detectar_valores_nulos()
        return jsonify(resultados)
    except Exception as e:
        logger.error(f"Error en valores_nulos: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/tratamiento/tratar-nulos", methods=["POST"])
def api_tratar_nulos():
    """
    API para tratar valores nulos.
    
    Aplica estrategias de tratamiento para valores nulos.
    
    Returns:
        JSON con resultados del tratamiento
    """
    try:
        resultados = preprocesamiento.tratar_valores_nulos()
        return jsonify({
            "success": True,
            "message": "Valores nulos tratados exitosamente",
            "resultados": resultados
        })
    except Exception as e:
        logger.error(f"Error en tratar_nulos: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/tratamiento/outliers")
def api_outliers():
    """
    API para detectar outliers.
    
    Retorna valores atípicos detectados en variables numéricas.
    
    Returns:
        JSON con outliers por variable
    """
    try:
        resultados = preprocesamiento.detectar_outliers()
        return jsonify(resultados)
    except Exception as e:
        logger.error(f"Error en outliers: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/tratamiento/codificar-categoricas")
def api_codificar_categoricas():
    """
    API para codificar variables categóricas.
    
    Aplica Label Encoding a variables categóricas.
    
    Returns:
        JSON con codificaciones aplicadas
    """
    try:
        resultados = preprocesamiento.codificar_variables_categoricas()
        return jsonify(resultados)
    except Exception as e:
        logger.error(f"Error en codificar_categoricas: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/tratamiento/normalizar")
def api_normalizar():
    """
    API para normalizar variables numéricas.
    
    Aplica StandardScaler y MinMaxScaler a variables numéricas.
    
    Returns:
        JSON con resultados de normalización
    """
    try:
        resultados = preprocesamiento.normalizar_variables_numericas()
        return jsonify(resultados)
    except Exception as e:
        logger.error(f"Error en normalizar: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/tratamiento/analisis-distribucion")
def api_analisis_distribucion():
    """
    API para análisis de distribución.
    
    Retorna análisis de distribución de variables importantes.
    
    Returns:
        JSON con análisis de distribución
    """
    try:
        resultados = preprocesamiento.analizar_distribucion()
        return jsonify(resultados)
    except Exception as e:
        logger.error(f"Error en analisis_distribucion: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/tratamiento/matriz-correlacion")
def api_matriz_correlacion():
    """
    API para matriz de correlación.
    
    Genera matriz de correlación entre variables numéricas.
    
    Returns:
        JSON con matriz de correlación
    """
    try:
        resultados = preprocesamiento.generar_matriz_correlacion()
        return jsonify(resultados)
    except Exception as e:
        logger.error(f"Error en matriz_correlacion: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/tratamiento/preprocesamiento-completo", methods=["POST"])
def api_preprocesamiento_completo():
    """
    API para preprocesamiento completo.
    
    Ejecuta todas las operaciones de preprocesamiento en una sola llamada.
    
    Returns:
        JSON con resultados completos
    """
    try:
        resultados = {
            "valores_nulos": preprocesamiento.detectar_valores_nulos(),
            "outliers": preprocesamiento.detectar_outliers(),
            "codificacion": preprocesamiento.codificar_variables_categoricas(),
            "normalizacion": preprocesamiento.normalizar_variables_numericas(),
            "distribucion": preprocesamiento.analizar_distribucion(),
            "correlacion": preprocesamiento.generar_matriz_correlacion()
        }
        
        return jsonify({
            "success": True,
            "message": "Preprocesamiento completo ejecutado",
            "resultados": resultados
        })
    except Exception as e:
        logger.error(f"Error en preprocesamiento_completo: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


# ============================================================================
# REPORTES
# ============================================================================

@app.route("/api/generar-reporte", methods=["POST"])
def generar_reporte():
    """
    Genera reporte con datos actuales.
    
    Compila un reporte con las métricas más importantes del sistema.
    
    Returns:
        JSON con datos del reporte
    """
    try:
        # Obtener datos
        producto_mas_vendido = preprocesamiento.producto_mas_vendido()
        valor_nomina = preprocesamiento.valor_nomina_total()
        top_clientes = preprocesamiento.top_clientes_por_valor()
        pedidos_mes = preprocesamiento.pedidos_por_mes()
        
        datos_reporte = {
            "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "total_empleados": app_data.cantidad_emp,
            "producto_mas_vendido": producto_mas_vendido.to_dict('records') if producto_mas_vendido is not None and not producto_mas_vendido.empty else [],
            "valor_nomina": valor_nomina.to_dict('records') if valor_nomina is not None and not valor_nomina.empty else [],
            "top_clientes": top_clientes.to_dict('records') if top_clientes is not None and not top_clientes.empty else [],
            "pedidos_por_mes": pedidos_mes.to_dict('records') if pedidos_mes is not None and not pedidos_mes.empty else []
        }
        
        return jsonify({
            "success": True,
            "message": "Reporte generado exitosamente",
            "datos": datos_reporte
        })
        
    except Exception as e:
        logger.error(f"Error generando reporte: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/descargar-reporte")
def descargar_reporte():
    """
    Endpoint para descargar reporte (placeholder).
    
    Función reservada para futura implementación de descarga de reportes.
    
    Returns:
        JSON con mensaje informativo
    """
    return jsonify({"message": "Funcionalidad en desarrollo"})


# ============================================================================
# INICIO DEL SERVIDOR
# ============================================================================

if __name__ == '__main__':
    """
    Punto de entrada principal de la aplicación.
    
    Inicia el servidor Flask con la configuración especificada.
    """
    logger.info("Iniciando servidor Flask en puerto 5000...")
    logger.info(f"Entorno: {env}")
    logger.info(f"Base de datos: {os.getenv('DB_HOST', 'localhost')}/{os.getenv('DB_NAME', 'pedidos11')}")
    
    # Obtener puerto del entorno o usar 5000 por defecto
    port = int(os.getenv('FLASK_PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
    
    app.run(host='0.0.0.0', port=port, debug=debug)