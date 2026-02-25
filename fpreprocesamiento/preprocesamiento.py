"""
Módulo de preprocesamiento y análisis de datos para la base de datos pedidos11.

Este módulo proporciona una capa de abstracción para consultas SQL, análisis estadístico
y transformación de datos. Incluye funciones para obtener métricas de negocio como
productos más vendidos, análisis de empleados, estadísticas de pedidos, y herramientas
de preprocesamiento como detección de valores nulos, outliers, codificación de variables
categóricas y normalización de datos numéricos.

La arquitectura está diseñada para ser utilizada por una aplicación Flask, con manejo
centralizado de conexiones a base de datos mediante SQLAlchemy y compatibilidad total
con pandas DataFrame.

Autor: Fabian Andrés Rincón
Fecha: Noviembre 2025
"""

import os
from typing import Dict, List, Optional, Tuple, Any, Union
from functools import wraps
import logging

import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder, StandardScaler, MinMaxScaler

# Importar configuración centralizada
from database import DatabaseConnection, db
from config import DatabaseConfig

# Configuración del sistema de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================================================
# DECORADOR PARA MANEJO DE CONEXIONES
# ============================================================================

def with_db_connection(func):
    """
    Decorador que maneja automáticamente la conexión a base de datos.
    
    Este decorador inyecta una conexión SQLAlchemy como primer argumento
    de la función decorada, gestionando automáticamente la apertura y cierre
    de la conexión. Soporta configuración personalizada opcional.
    
    Args:
        func: Función a decorar que recibirá la conexión como primer argumento
        
    Returns:
        Función wrapper que maneja el ciclo de vida de la conexión
        
    Example:
        @with_db_connection
        def mi_consulta(conn, parametro1, parametro2):
            return pd.read_sql("SELECT * FROM tabla", conn)
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Usar configuración personalizada si se proporciona
        config = kwargs.pop('db_config', None)
        
        # Crear conexión (nueva instancia o usar la global)
        db_conn = DatabaseConnection(config) if config else db
        
        with db_conn as conn:
            return func(conn, *args, **kwargs)
    return wrapper


# ============================================================================
# FUNCIONES DE UTILIDAD
# ============================================================================

def execute_query(query: str, params: Optional[Tuple] = None) -> pd.DataFrame:
    """
    Ejecuta una consulta SQL y retorna los resultados como DataFrame.
    
    Esta función proporciona una interfaz simplificada para ejecutar consultas
    SQL sin necesidad de manejar explícitamente la conexión. Soporta consultas
    parametrizadas para prevenir inyección SQL.
    
    Args:
        query: Consulta SQL a ejecutar
        params: Parámetros para consultas parametrizadas (como tupla)
                Ejemplo: ("SELECT * FROM tabla WHERE id = %s", (123,))
        
    Returns:
        DataFrame con los resultados de la consulta.
        Retorna DataFrame vacío si ocurre un error.
        
    Example:
        df = execute_query("SELECT * FROM productos WHERE precio > %s", (1000,))
    """
    try:
        with db as conn:
            if params:
                return pd.read_sql(query, conn, params=params)
            return pd.read_sql(query, conn)
    except Exception as e:
        logger.error(f"Error ejecutando consulta: {e}\n{query[:100]}...")
        return pd.DataFrame()


def get_table_names() -> List[str]:
    """
    Obtiene lista de todas las tablas en la base de datos.
    
    Realiza una consulta SHOW TABLES y retorna los nombres de todas
    las tablas disponibles en la base de datos actual.
    
    Returns:
        Lista con nombres de todas las tablas en la base de datos.
        Retorna lista vacía si no hay tablas o si ocurre un error.
        
    Example:
        tablas = get_table_names()
        for tabla in tablas:
            print(f"Tabla encontrada: {tabla}")
    """
    try:
        with db as conn:
            query = "SHOW TABLES;"
            df = pd.read_sql(query, conn)
            if df.empty:
                return []
            # La primera columna contiene los nombres de las tablas
            return df.iloc[:, 0].tolist()
    except Exception as e:
        logger.error(f"Error obteniendo tablas: {e}")
        return []


def get_table_data(table_name: str, limit: Optional[int] = None) -> pd.DataFrame:
    """
    Obtiene datos de una tabla específica.
    
    Recupera todos los registros de una tabla, con opción de limitar
    el número de filas retornadas. Incluye validación básica del nombre
    de la tabla para prevenir errores comunes.
    
    Args:
        table_name: Nombre de la tabla a consultar
        limit: Límite máximo de filas a retornar (opcional)
        
    Returns:
        DataFrame con los datos de la tabla.
        Retorna DataFrame vacío si la tabla no existe o hay error.
        
    Example:
        # Obtener todos los productos
        df_productos = get_table_data('productos')
        
        # Obtener solo los primeros 10 pedidos
        df_pedidos = get_table_data('pedidos', limit=10)
    """
    try:
        # Validar nombre de tabla (evitar nombres generados por SHOW TABLES)
        if table_name.startswith('Tables_in_'):
            logger.warning(f"Nombre de tabla inválido: {table_name}")
            return pd.DataFrame()
            
        query = f"SELECT * FROM {table_name}"
        if limit:
            query += f" LIMIT {limit}"
        
        with db as conn:
            return pd.read_sql(query, conn)
    except Exception as e:
        logger.error(f"Error obteniendo datos de {table_name}: {e}")
        return pd.DataFrame()


# ============================================================================
# CONSULTAS DE PRODUCTOS
# ============================================================================

class ProductoQueries:
    """
    Consultas relacionadas con productos y categorías.
    
    Esta clase agrupa todas las operaciones de consulta que involucran
    la tabla de productos y sus relaciones con categorías y detalles de pedidos.
    Todos los métodos son estáticos y manejan automáticamente la conexión
    mediante el decorador @with_db_connection.
    """
    
    @staticmethod
    @with_db_connection
    def por_categoria(conn) -> pd.DataFrame:
        """
        Obtiene la cantidad de productos por categoría.
        
        Realiza un LEFT JOIN entre categorías y productos para contar
        cuántos productos pertenecen a cada categoría, incluyendo
        categorías sin productos.
        
        Returns:
            DataFrame con columnas:
                - Categoria: Nombre de la categoría
                - Cantidad: Número de productos en esa categoría
                
        Example:
            df = ProductoQueries.por_categoria()
            # Resultado: [{'Categoria': 'Electrónica', 'Cantidad': 25}, ...]
        """
        query = """
        SELECT 
            c.Nombre_Categoria AS Categoria,
            COUNT(p.Id_Producto) AS Cantidad
        FROM categorias c
        LEFT JOIN productos p ON c.Id_Categoria = p.Id_Categoria
        GROUP BY c.Nombre_Categoria
        ORDER BY Cantidad DESC;
        """
        return pd.read_sql(query, conn)
    
    @staticmethod
    @with_db_connection
    def mas_vendido(conn) -> pd.DataFrame:
        """
        Obtiene el producto más vendido por cantidad total.
        
        Suma las cantidades vendidas de cada producto en todos los pedidos
        y retorna el producto con mayor cantidad total.
        
        Returns:
            DataFrame con una fila conteniendo:
                - producto: Nombre del producto más vendido
                - total_vendido: Cantidad total vendida
                
        Example:
            df = ProductoQueries.mas_vendido()
            # Resultado: [{'producto': 'Laptop Gamer', 'total_vendido': 150}]
        """
        query = """
        SELECT 
            p.Nombre_Producto AS producto,
            SUM(dp.Cantidad) AS total_vendido
        FROM productos p
        JOIN detalles_pedidos dp ON p.Id_Producto = dp.Id_Producto
        GROUP BY p.Id_Producto, p.Nombre_Producto
        ORDER BY total_vendido DESC
        LIMIT 1;
        """
        return pd.read_sql(query, conn)
    
    @staticmethod
    @with_db_connection
    def mas_solicitado(conn) -> pd.DataFrame:
        """
        Obtiene el producto más solicitado (mayor número de pedidos distintos).
        
        Cuenta en cuántos pedidos diferentes aparece cada producto,
        independientemente de la cantidad, y retorna el más frecuente.
        
        Returns:
            DataFrame con una fila conteniendo:
                - producto: Nombre del producto más solicitado
                - veces_solicitado: Número de pedidos donde aparece
                
        Example:
            df = ProductoQueries.mas_solicitado()
            # Resultado: [{'producto': 'Mouse Pad', 'veces_solicitado': 89}]
        """
        query = """
        SELECT 
            p.Nombre_Producto AS producto,
            COUNT(DISTINCT dp.Id_pedido) AS veces_solicitado
        FROM productos p
        JOIN detalles_pedidos dp ON p.Id_Producto = dp.Id_Producto
        GROUP BY p.Id_Producto, p.Nombre_Producto
        ORDER BY veces_solicitado DESC
        LIMIT 1;
        """
        return pd.read_sql(query, conn)
    
    @staticmethod
    @with_db_connection
    def top_ventas(conn, limite: int = 5) -> pd.DataFrame:
        """
        Obtiene los N productos más vendidos por cantidad y valor.
        
        Calcula para cada producto la cantidad total vendida y el valor
        total facturado (considerando descuentos), ordenando por cantidad
        descendente.
        
        Args:
            limite: Número de productos a retornar (por defecto 5)
            
        Returns:
            DataFrame con columnas:
                - Id_Producto: Identificador del producto
                - producto: Nombre del producto
                - total_vendido: Cantidad total vendida
                - valor_total: Valor total facturado (con descuentos)
                
        Example:
            df = ProductoQueries.top_ventas(limite=10)
        """
        query = """
        SELECT 
            p.Id_Producto,
            p.Nombre_Producto AS producto,
            SUM(dp.Cantidad) AS total_vendido,
            SUM(dp.Precio_Unidad * dp.Cantidad * (1 - dp.Descuento)) AS valor_total
        FROM productos p
        JOIN detalles_pedidos dp ON p.Id_Producto = dp.Id_Producto
        GROUP BY p.Id_Producto, p.Nombre_Producto
        ORDER BY total_vendido DESC
        LIMIT %s;
        """
        return pd.read_sql(query, conn, params=(limite,))
    
    @staticmethod
    @with_db_connection
    def top_solicitados(conn, limite: int = 5) -> pd.DataFrame:
        """
        Obtiene los N productos más solicitados por número de pedidos.
        
        Calcula para cada producto en cuántos pedidos diferentes aparece
        y la cantidad total vendida, ordenando por frecuencia de pedidos.
        
        Args:
            limite: Número de productos a retornar (por defecto 5)
            
        Returns:
            DataFrame con columnas:
                - Id_Producto: Identificador del producto
                - producto: Nombre del producto
                - veces_solicitado: Número de pedidos donde aparece
                - cantidad_total: Cantidad total vendida
                
        Example:
            df = ProductoQueries.top_solicitados(limite=10)
        """
        query = """
        SELECT 
            p.Id_Producto,
            p.Nombre_Producto AS producto,
            COUNT(DISTINCT dp.Id_pedido) AS veces_solicitado,
            SUM(dp.Cantidad) AS cantidad_total
        FROM productos p
        JOIN detalles_pedidos dp ON p.Id_Producto = dp.Id_Producto
        GROUP BY p.Id_Producto, p.Nombre_Producto
        ORDER BY veces_solicitado DESC
        LIMIT %s;
        """
        return pd.read_sql(query, conn, params=(limite,))


# ============================================================================
# CONSULTAS DE EMPLEADOS
# ============================================================================

class EmpleadoQueries:
    """
    Consultas relacionadas con empleados, departamentos y nómina.
    
    Agrupa operaciones sobre la tabla employees y sus relaciones con
    departments, pedidos y lugares. Incluye análisis de salarios,
    comisiones y ubicaciones.
    """
    
    @staticmethod
    @with_db_connection
    def por_departamento(conn) -> pd.DataFrame:
        """
        Obtiene la cantidad de empleados por departamento.
        
        Realiza un LEFT JOIN entre departments y employees para contar
        empleados en cada departamento, incluyendo departamentos sin personal.
        
        Returns:
            DataFrame con columnas:
                - departamento: Nombre del departamento
                - cantidad: Número de empleados
        """
        query = """
        SELECT 
            d.DEPARTMENT_NAME AS departamento,
            COUNT(e.EMPLOYEE_ID) AS cantidad
        FROM departments d
        LEFT JOIN employees e ON d.DEPARTMENT_ID = e.DEPARTMENT_ID
        GROUP BY d.DEPARTMENT_NAME
        ORDER BY cantidad DESC;
        """
        return pd.read_sql(query, conn)
    
    @staticmethod
    @with_db_connection
    def pedidos_atendidos(conn) -> pd.DataFrame:
        """
        Obtiene la cantidad de pedidos atendidos por cada empleado.
        
        Cuenta los pedidos asociados a cada empleado mediante la relación
        en la tabla pedidos.
        
        Returns:
            DataFrame con columnas:
                - empleado: Nombre completo del empleado
                - cantidad_pedidos: Número de pedidos atendidos
        """
        query = """
        SELECT 
            CONCAT(e.FIRST_NAME, ' ', e.LAST_NAME) AS empleado,
            COUNT(p.Id_Pedido) AS cantidad_pedidos
        FROM employees e
        JOIN pedidos p ON e.EMPLOYEE_ID = p.EMPLOYEE_ID
        GROUP BY e.EMPLOYEE_ID, e.FIRST_NAME, e.LAST_NAME
        ORDER BY cantidad_pedidos DESC;
        """
        return pd.read_sql(query, conn)
    
    @staticmethod
    @with_db_connection
    def mejor_pagados(conn, limite: int = 5) -> pd.DataFrame:
        """
        Obtiene los N empleados mejor pagados.
        
        Lista los empleados con los salarios más altos, incluyendo
        información básica de identificación y cargo.
        
        Args:
            limite: Número de empleados a retornar (por defecto 5)
            
        Returns:
            DataFrame con columnas:
                - Id_Empleado: Identificador del empleado
                - Nombre_Completo: Nombre completo
                - Cargo: Identificador del cargo (JOB_ID)
                - Salario: Salario del empleado
        """
        query = """
        SELECT 
            EMPLOYEE_ID AS Id_Empleado,
            CONCAT(FIRST_NAME, ' ', LAST_NAME) AS Nombre_Completo,
            JOB_ID AS Cargo,
            SALARY AS Salario
        FROM employees
        ORDER BY SALARY DESC
        LIMIT %s;
        """
        return pd.read_sql(query, conn, params=(limite,))
    
    @staticmethod
    @with_db_connection
    def top_comisiones(conn, limite: int = 5) -> pd.DataFrame:
        """
        Obtiene los N empleados con mayor porcentaje de comisión.
        
        Filtra empleados con comisión registrada y positiva, y los ordena
        por porcentaje descendente.
        
        Args:
            limite: Número de empleados a retornar (por defecto 5)
            
        Returns:
            DataFrame con columnas:
                - empleado: Nombre completo del empleado
                - porcentaje_comision: Porcentaje de comisión (0-100)
        """
        query = """
        SELECT 
            CONCAT(FIRST_NAME, ' ', LAST_NAME) AS empleado,
            IFNULL(COMMISSION_PCT, 0) * 100 AS porcentaje_comision
        FROM employees
        WHERE COMMISSION_PCT IS NOT NULL
          AND COMMISSION_PCT > 0
        ORDER BY porcentaje_comision DESC
        LIMIT %s;
        """
        return pd.read_sql(query, conn, params=(limite,))
    
    @staticmethod
    @with_db_connection
    def lugar_coincide(conn) -> pd.DataFrame:
        """
        Obtiene empleados que nacen, viven y trabajan en el mismo lugar.
        
        Encuentra empleados donde los códigos de lugar de nacimiento,
        residencia y trabajo son idénticos, e incluye el nombre del lugar.
        
        Returns:
            DataFrame con columnas:
                - EMPLOYEE_ID: Identificador del empleado
                - nombre_completo: Nombre completo
                - lugar: Nombre del lugar coincidente
        """
        query = """
        SELECT 
            e.EMPLOYEE_ID,
            CONCAT(e.FIRST_NAME, ' ', e.LAST_NAME) AS nombre_completo,
            l.Nombre_Lugar AS lugar
        FROM employees e
        JOIN lugares l 
          ON e.COD_LUGAR_NACE = l.Id_Lugar
         AND e.COD_LUGAR_VIVE = l.Id_Lugar
         AND e.COD_LUGAR_TRABAJA = l.Id_Lugar;
        """
        return pd.read_sql(query, conn)
    
    @staticmethod
    @with_db_connection
    def contar_lugar_coincide(conn) -> pd.DataFrame:
        """
        Cuenta empleados que nacen, viven y trabajan en el mismo lugar.
        
        Versión resumida de lugar_coincide que solo retorna el conteo.
        
        Returns:
            DataFrame con columna:
                - empleados_coinciden: Número de empleados con lugares coincidentes
        """
        query = """
        SELECT 
            COUNT(*) AS empleados_coinciden
        FROM employees
        WHERE COD_LUGAR_NACE = COD_LUGAR_VIVE
          AND COD_LUGAR_NACE = COD_LUGAR_TRABAJA;
        """
        return pd.read_sql(query, conn)
    
    @staticmethod
    @with_db_connection
    def nomina_total(conn) -> pd.DataFrame:
        """
        Calcula el valor total de la nómina.
        
        Suma todos los salarios de empleados activos.
        
        Returns:
            DataFrame con columna:
                - Valor_Nomina_Total: Suma total de salarios (redondeada a 2 decimales)
        """
        query = """
        SELECT 
            ROUND(SUM(SALARY), 2) AS Valor_Nomina_Total
        FROM employees;
        """
        return pd.read_sql(query, conn)
    
    @staticmethod
    @with_db_connection
    def nomina_por_departamento(conn) -> pd.DataFrame:
        """
        Calcula el valor total de nómina por departamento.
        
        Agrupa y suma salarios por departamento, ordenando por valor descendente.
        
        Returns:
            DataFrame con columnas:
                - departamento: Nombre del departamento
                - valor_nomina: Suma de salarios en ese departamento
        """
        query = """
        SELECT 
            d.DEPARTMENT_NAME AS departamento,
            SUM(e.SALARY) AS valor_nomina
        FROM employees e
        JOIN departments d ON e.DEPARTMENT_ID = d.DEPARTMENT_ID
        GROUP BY d.DEPARTMENT_NAME
        ORDER BY valor_nomina DESC;
        """
        return pd.read_sql(query, conn)


# ============================================================================
# CONSULTAS DE PEDIDOS Y CLIENTES
# ============================================================================

class PedidoQueries:
    """
    Consultas relacionadas con pedidos y clientes.
    
    Agrupa operaciones sobre las tablas pedidos, clientes y detalles_pedidos,
    incluyendo análisis temporales y de facturación.
    """
    
    @staticmethod
    @with_db_connection
    def por_forma_pago(conn) -> pd.DataFrame:
        """
        Agrupa pedidos por forma de pago con porcentajes.
        
        Clasifica los pedidos según su forma de pago (Efectivo, Crédito, Otro)
        y calcula el porcentaje que representa cada categoría.
        
        Returns:
            DataFrame con columnas:
                - forma_pago: Categoría de pago (Efectivo/Crédito/Otro)
                - cantidad_pedidos: Número de pedidos
                - porcentaje: Porcentaje del total
        """
        query = """
        SELECT 
            CASE 
                WHEN Forma_Pago = 'E' THEN 'Efectivo'
                WHEN Forma_Pago = 'C' THEN 'Crédito'
                ELSE 'Otro'
            END AS forma_pago,
            COUNT(*) AS cantidad_pedidos,
            ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM pedidos), 2) AS porcentaje
        FROM pedidos
        GROUP BY forma_pago;
        """
        return pd.read_sql(query, conn)
    
    @staticmethod
    @with_db_connection
    def por_anio(conn) -> pd.DataFrame:
        """
        Agrupa pedidos por año.
        
        Extrae el año de la fecha de pedido y cuenta pedidos por año,
        excluyendo registros con fecha nula.
        
        Returns:
            DataFrame con columnas:
                - anio: Año del pedido
                - cantidad_pedidos: Número de pedidos en ese año
        """
        query = """
        SELECT 
            YEAR(Fecha_Pedido) AS anio,
            COUNT(*) AS cantidad_pedidos
        FROM pedidos
        WHERE Fecha_Pedido IS NOT NULL
        GROUP BY anio
        ORDER BY anio ASC;
        """
        return pd.read_sql(query, conn)
    
    @staticmethod
    @with_db_connection
    def por_mes(conn) -> pd.DataFrame:
        """
        Agrupa pedidos por mes y año.
        
        Desglose mensual de pedidos para análisis de estacionalidad.
        
        Returns:
            DataFrame con columnas:
                - anio: Año del pedido
                - mes: Mes del pedido (1-12)
                - cantidad_pedidos: Número de pedidos
        """
        query = """
        SELECT 
            YEAR(Fecha_Pedido) AS anio,
            MONTH(Fecha_Pedido) AS mes,
            COUNT(*) AS cantidad_pedidos
        FROM pedidos
        WHERE Fecha_Pedido IS NOT NULL
        GROUP BY anio, mes
        ORDER BY anio ASC, mes ASC;
        """
        return pd.read_sql(query, conn)
    
    @staticmethod
    @with_db_connection
    def top_clientes_por_valor(conn, limite: int = 5) -> pd.DataFrame:
        """
        Obtiene los N clientes con mayor valor facturado.
        
        Calcula el valor total facturado por cliente considerando
        cantidad, precio unitario y descuentos aplicados.
        
        Args:
            limite: Número de clientes a retornar (por defecto 5)
            
        Returns:
            DataFrame con columnas:
                - cliente: Nombre de la compañía cliente
                - valor_facturado: Valor total facturado
        """
        query = """
        SELECT 
            c.Nombre_Compañía AS cliente,
            SUM(dp.Cantidad * dp.Precio_Unidad * (1 - dp.Descuento)) AS valor_facturado
        FROM clientes c
        JOIN pedidos p ON c.Id_Cliente = p.Id_Cliente
        JOIN detalles_pedidos dp ON p.Id_Pedido = dp.Id_Pedido
        GROUP BY c.Id_Cliente, c.Nombre_Compañía
        ORDER BY valor_facturado DESC
        LIMIT %s;
        """
        return pd.read_sql(query, conn, params=(limite,))


# ============================================================================
# FUNCIONES PARA ESTADÍSTICAS
# ============================================================================

class Estadisticas:
    """
    Clase para cálculos estadísticos avanzados sobre los datos.
    
    Proporciona métodos para obtener estadísticas descriptivas, análisis
    de distribución, matrices de correlación y otras métricas cuantitativas
    sobre las variables numéricas de la base de datos.
    """
    
    @staticmethod
    def _convertir_a_numerico(df: pd.DataFrame, columna: str) -> pd.DataFrame:
        """
        Convierte una columna a tipo numérico de forma segura.
        
        Método auxiliar que intenta convertir una columna de texto a numérico,
        reemplazando valores no convertibles por NaN.
        
        Args:
            df: DataFrame a procesar
            columna: Nombre de la columna a convertir
            
        Returns:
            DataFrame con la columna convertida (in-place)
        """
        if columna in df.columns and df[columna].dtype == 'object':
            df[columna] = pd.to_numeric(df[columna], errors='coerce')
        return df
    
    @staticmethod
    @with_db_connection
    def precios_productos(conn) -> Optional[Dict[str, Any]]:
        """
        Calcula estadísticas descriptivas de los precios de productos.
        
        Obtiene medidas de tendencia central, dispersión y posición
        para la variable Precio_por_Unidad de la tabla productos.
        
        Returns:
            Diccionario con las siguientes estadísticas:
                - media: Promedio aritmético
                - mediana: Valor central
                - moda: Valor más frecuente
                - minimo: Valor mínimo
                - maximo: Valor máximo
                - q1: Primer cuartil (25%)
                - q3: Tercer cuartil (75%)
                - iqr: Rango intercuartílico
                - desviacion_estandar: Desviación estándar
                - varianza: Varianza
                - total_registros: Número de productos considerados
                
            Retorna None si no hay datos suficientes.
        """
        query = """
        SELECT Precio_por_Unidad 
        FROM productos 
        WHERE Precio_por_Unidad IS NOT NULL 
          AND Precio_por_Unidad > 0
        """
        df = pd.read_sql(query, conn)
        
        if df.empty:
            logger.warning("No hay datos de precios para análisis")
            return None
        
        # Convertir a numérico si es necesario
        df = Estadisticas._convertir_a_numerico(df, 'Precio_por_Unidad')
        df = df.dropna(subset=['Precio_por_Unidad'])
        
        if df.empty:
            logger.warning("No hay datos numéricos válidos de precios")
            return None
        
        precios = df['Precio_por_Unidad']
        
        # Cálculos estadísticos básicos
        media = float(precios.mean())
        mediana = float(precios.median())
        minimo = float(precios.min())
        maximo = float(precios.max())
        
        # Moda (puede haber múltiples, tomamos la primera)
        moda_values = precios.mode()
        moda = float(moda_values[0]) if not moda_values.empty else media
        
        # Cuartiles
        q1 = float(precios.quantile(0.25))
        q3 = float(precios.quantile(0.75))
        iqr = q3 - q1
        
        desviacion = float(precios.std()) if len(precios) > 1 else 0.0
        varianza = float(precios.var()) if len(precios) > 1 else 0.0
        
        return {
            "media": round(media, 2),
            "mediana": round(mediana, 2),
            "moda": round(moda, 2),
            "minimo": round(minimo, 2),
            "maximo": round(maximo, 2),
            "q1": round(q1, 2),
            "q3": round(q3, 2),
            "iqr": round(iqr, 2),
            "desviacion_estandar": round(desviacion, 2),
            "varianza": round(varianza, 2),
            "total_registros": len(precios)
        }
    
    @staticmethod
    @with_db_connection
    def salarios_empleados(conn) -> Optional[Dict[str, Any]]:
        """
        Calcula estadísticas descriptivas de los salarios de empleados.
        
        Obtiene medidas de tendencia central y dispersión para la
        variable SALARY de la tabla employees.
        
        Returns:
            Diccionario con estadísticas similares a precios_productos,
            enfocado en salarios. None si no hay datos.
        """
        query = """
        SELECT SALARY 
        FROM employees 
        WHERE SALARY IS NOT NULL AND SALARY > 0
        """
        df = pd.read_sql(query, conn)
        
        if df.empty:
            logger.warning("No hay datos de salarios para análisis")
            return None
        
        # Convertir a numérico si es necesario
        df = Estadisticas._convertir_a_numerico(df, 'SALARY')
        df = df.dropna(subset=['SALARY'])
        
        if df.empty:
            logger.warning("No hay datos numéricos válidos de salarios")
            return None
        
        salarios = df['SALARY']
        
        return {
            "media": round(float(salarios.mean()), 2),
            "mediana": round(float(salarios.median()), 2),
            "minimo": round(float(salarios.min()), 2),
            "maximo": round(float(salarios.max()), 2),
            "q1": round(float(salarios.quantile(0.25)), 2),
            "q3": round(float(salarios.quantile(0.75)), 2),
            "iqr": round(float(salarios.quantile(0.75) - salarios.quantile(0.25)), 2),
            "desviacion_estandar": round(float(salarios.std()), 2) if len(salarios) > 1 else 0.0,
            "varianza": round(float(salarios.var()), 2) if len(salarios) > 1 else 0.0,
            "total_registros": len(salarios)
        }
    
    @staticmethod
    @with_db_connection
    def cantidades_pedidos(conn) -> Optional[Dict[str, Any]]:
        """
        Calcula estadísticas de las cantidades en detalles de pedidos.
        
        Analiza la distribución de la variable Cantidad en la tabla
        detalles_pedidos.
        
        Returns:
            Diccionario con estadísticas de cantidades. None si no hay datos.
        """
        query = """
        SELECT Cantidad 
        FROM detalles_pedidos 
        WHERE Cantidad IS NOT NULL AND Cantidad > 0
        """
        df = pd.read_sql(query, conn)
        
        if df.empty:
            logger.warning("No hay datos de cantidades para análisis")
            return None
        
        # Convertir a numérico si es necesario
        df = Estadisticas._convertir_a_numerico(df, 'Cantidad')
        df = df.dropna(subset=['Cantidad'])
        
        if df.empty:
            logger.warning("No hay datos numéricos válidos de cantidades")
            return None
        
        cantidades = df['Cantidad']
        
        return {
            "media": round(float(cantidades.mean()), 2),
            "mediana": round(float(cantidades.median()), 2),
            "minimo": int(cantidades.min()),
            "maximo": int(cantidades.max()),
            "desviacion_estandar": round(float(cantidades.std()), 2) if len(cantidades) > 1 else 0.0,
            "varianza": round(float(cantidades.var()), 2) if len(cantidades) > 1 else 0.0,
            "total_registros": len(cantidades)
        }
    
    @staticmethod
    @with_db_connection
    def analizar_distribucion(conn) -> Dict[str, Any]:
        """
        Realiza análisis de distribución para variables importantes.
        
        Calcula métricas avanzadas como asimetría (skewness) y curtosis
        para salarios y precios, además de las estadísticas básicas.
        
        Returns:
            Diccionario con dos claves principales:
                - salarios: Análisis detallado de salarios
                - precios: Análisis detallado de precios
                
            Cada sub-diccionario incluye media, mediana, moda,
            desviación, asimetría, curtosis, mínimo, máximo y rango.
        """
        analisis = {}
        
        # Análisis de salarios
        try:
            df_salarios = pd.read_sql("SELECT SALARY FROM employees WHERE SALARY IS NOT NULL", conn)
            if not df_salarios.empty:
                df_salarios = Estadisticas._convertir_a_numerico(df_salarios, 'SALARY')
                df_salarios = df_salarios.dropna(subset=['SALARY'])
                
                if not df_salarios.empty:
                    salarios = df_salarios['SALARY']
                    analisis['salarios'] = {
                        'media': round(salarios.mean(), 2),
                        'mediana': round(salarios.median(), 2),
                        'moda': round(salarios.mode()[0] if not salarios.mode().empty else 0, 2),
                        'desviacion_estandar': round(salarios.std(), 2),
                        'asimetria': round(salarios.skew(), 2),
                        'curtosis': round(salarios.kurtosis(), 2),
                        'minimo': round(salarios.min(), 2),
                        'maximo': round(salarios.max(), 2),
                        'rango': round(salarios.max() - salarios.min(), 2)
                    }
        except Exception as e:
            analisis['salarios'] = {'error': str(e)}
        
        # Análisis de precios
        try:
            df_precios = pd.read_sql("SELECT Precio_por_Unidad FROM productos WHERE Precio_por_Unidad IS NOT NULL", conn)
            if not df_precios.empty:
                df_precios = Estadisticas._convertir_a_numerico(df_precios, 'Precio_por_Unidad')
                df_precios = df_precios.dropna(subset=['Precio_por_Unidad'])
                
                if not df_precios.empty:
                    precios = df_precios['Precio_por_Unidad']
                    analisis['precios'] = {
                        'media': round(precios.mean(), 2),
                        'mediana': round(precios.median(), 2),
                        'desviacion_estandar': round(precios.std(), 2),
                        'asimetria': round(precios.skew(), 2),
                        'curtosis': round(precios.kurtosis(), 2)
                    }
        except Exception as e:
            analisis['precios'] = {'error': str(e)}
        
        return analisis
    
    @staticmethod
    @with_db_connection
    def generar_matriz_correlacion(conn) -> Dict[str, Any]:
        """
        Genera matriz de correlación entre variables numéricas.
        
        Combina datos de employees, productos y detalles_pedidos para
        calcular correlaciones entre salarios, precios, cantidades y descuentos.
        
        Returns:
            Diccionario con:
                - variables: Lista de nombres de variables analizadas
                - matriz: Matriz de correlación (como diccionario anidado)
                - correlaciones_fuertes: Lista de pares con |correlación| > 0.7
                
            Incluye clave 'error' si no hay datos suficientes.
        """
        try:
            # Consulta para obtener datos numéricos relevantes
            consulta = """
            SELECT 
                e.SALARY,
                p.Precio_por_Unidad,
                dp.Cantidad,
                dp.Precio_Unidad as Precio_Detalle,
                dp.Descuento
            FROM employees e
            JOIN pedidos ped ON e.EMPLOYEE_ID = ped.EMPLOYEE_ID
            JOIN detalles_pedidos dp ON ped.Id_Pedido = dp.Id_Pedido
            JOIN productos p ON dp.Id_Producto = p.Id_Producto
            WHERE e.SALARY IS NOT NULL 
              AND p.Precio_por_Unidad IS NOT NULL
            LIMIT 1000
            """
            
            df = pd.read_sql(consulta, conn)
            
            if df.empty:
                return {'error': 'No se encontraron datos para análisis de correlación'}
            
            # Convertir todas las columnas a numérico
            for col in df.columns:
                df = Estadisticas._convertir_a_numerico(df, col)
            
            # Eliminar filas con NaN
            df = df.dropna()
            
            if df.empty:
                return {'error': 'No hay datos válidos después de limpieza'}
            
            correlacion = df.corr()
            matriz = {
                'variables': correlacion.columns.tolist(),
                'matriz': correlacion.round(3).to_dict(),
                'correlaciones_fuertes': []
            }
            
            # Encontrar correlaciones fuertes (abs > 0.7)
            for i in range(len(correlacion.columns)):
                for j in range(i+1, len(correlacion.columns)):
                    corr_val = correlacion.iloc[i, j]
                    if abs(corr_val) > 0.7:
                        matriz['correlaciones_fuertes'].append({
                            'variable1': correlacion.columns[i],
                            'variable2': correlacion.columns[j],
                            'correlacion': round(corr_val, 3)
                        })
            
            return matriz
            
        except Exception as e:
            return {'error': str(e)}


# ============================================================================
# DETECCIÓN Y TRATAMIENTO DE VALORES NULOS
# ============================================================================

def detectar_valores_nulos() -> Dict[str, Any]:
    """
    Detecta valores nulos en todas las tablas de la base de datos.
    
    Itera sobre todas las tablas y calcula para cada una:
    - Total de valores nulos
    - Distribución por columna
    - Porcentaje de nulos sobre el total de celdas
    
    Returns:
        Diccionario con tablas como claves. Cada valor es otro diccionario con:
            - total_nulos: Número total de celdas nulas
            - columnas_nulos: Diccionario columna -> cantidad de nulos
            - total_registros: Número de filas en la tabla
            - porcentaje_nulos: Porcentaje de celdas nulas
            
        Incluye clave 'error' si hay problemas con alguna tabla.
    """
    tablas = get_table_names()
    resultados = {}
    
    for tabla in tablas:
        try:
            df = get_table_data(tabla)
            if df.empty:
                continue
                
            nulos = df.isnull().sum()
            nulos_totales = nulos.sum()
            
            if nulos_totales > 0:
                resultados[tabla] = {
                    'total_nulos': int(nulos_totales),
                    'columnas_nulos': nulos[nulos > 0].to_dict(),
                    'total_registros': len(df),
                    'porcentaje_nulos': round((nulos_totales / (len(df) * len(df.columns))) * 100, 2) if len(df) > 0 else 0
                }
        except Exception as e:
            resultados[tabla] = {'error': str(e)}
    
    return resultados


def tratar_valores_nulos() -> Dict[str, Any]:
    """
    Aplica estrategias de tratamiento para valores nulos.
    
    Para tablas y columnas específicas, aplica diferentes estrategias:
    - 'media': Rellena con la media de la columna
    - 'moda': Rellena con el valor más frecuente
    - 'mediana': Rellena con la mediana
    - 'eliminar': Elimina registros con nulos en esa columna
    
    Returns:
        Diccionario con resultados por tabla, incluyendo:
            - registros_originales: Filas antes del tratamiento
            - registros_finales: Filas después del tratamiento
            - nulos_originales: Total de nulos antes
            - nulos_tratados: Nulos que fueron tratados
            - columnas_tratadas: Lista de columnas procesadas
    """
    # Estrategias específicas por tabla/columna
    estrategias = {
        'employees': {
            'COMMISSION_PCT': 'media',  # Comisión - usar media
            'MANAGER_ID': 'moda',       # Manager - usar moda
            'DEPARTMENT_ID': 'moda'      # Departamento - usar moda
        },
        'productos': {
            'Precio_por_Unidad': 'media'  # Precio - usar media
        },
        'pedidos': {
            'Fecha_Pedido': 'eliminar'  # Fecha nula - eliminar registro
        }
    }
    
    resultados = {}
    
    for tabla, columnas in estrategias.items():
        try:
            df = get_table_data(tabla)
            if df.empty:
                continue
                
            original_shape = df.shape
            nulos_originales = df.isnull().sum().sum()
            columnas_tratadas = []
            
            for columna, estrategia in columnas.items():
                if columna in df.columns and df[columna].isnull().sum() > 0:
                    columnas_tratadas.append(columna)
                    
                    if estrategia == 'media':
                        # Convertir a numérico si es necesario
                        if df[columna].dtype == 'object':
                            df[columna] = pd.to_numeric(df[columna], errors='coerce')
                        df[columna].fillna(df[columna].mean(), inplace=True)
                    elif estrategia == 'moda':
                        moda = df[columna].mode()
                        valor_moda = moda[0] if not moda.empty else 0
                        df[columna].fillna(valor_moda, inplace=True)
                    elif estrategia == 'mediana':
                        if df[columna].dtype == 'object':
                            df[columna] = pd.to_numeric(df[columna], errors='coerce')
                        df[columna].fillna(df[columna].median(), inplace=True)
                    elif estrategia == 'eliminar':
                        df.dropna(subset=[columna], inplace=True)
            
            nulos_finales = df.isnull().sum().sum()
            
            resultados[tabla] = {
                'registros_originales': original_shape[0],
                'registros_finales': df.shape[0],
                'nulos_originales': int(nulos_originales),
                'nulos_tratados': int(nulos_originales - nulos_finales),
                'columnas_tratadas': columnas_tratadas
            }
            
        except Exception as e:
            resultados[tabla] = {'error': str(e)}
    
    return resultados


# ============================================================================
# DETECCIÓN DE OUTLIERS (VALORES ATÍPICOS)
# ============================================================================

def detectar_outliers() -> Dict[str, Any]:
    """
    Detecta valores atípicos usando el método del rango intercuartílico (IQR).
    
    Para cada variable numérica analizada, calcula:
    - Límites inferior y superior (Q1 - 1.5*IQR, Q3 + 1.5*IQR)
    - Cantidad y porcentaje de outliers
    - Muestra de valores outliers (primeros 10)
    
    Returns:
        Diccionario con análisis por variable:
            - empleados_salarios: Análisis de salarios
            - productos_precios: Análisis de precios
            - pedidos_cantidades: Análisis de cantidades
            
        Cada análisis incluye total_registros, outliers_encontrados,
        porcentaje_outliers, límites, valores mín/máx y muestra de outliers.
    """
    # Columnas numéricas a analizar
    consultas = {
        'empleados_salarios': "SELECT SALARY FROM employees WHERE SALARY IS NOT NULL",
        'productos_precios': "SELECT Precio_por_Unidad FROM productos WHERE Precio_por_Unidad IS NOT NULL",
        'pedidos_cantidades': "SELECT Cantidad FROM detalles_pedidos WHERE Cantidad IS NOT NULL"
    }
    
    outliers = {}
    
    for nombre, consulta in consultas.items():
        try:
            df = execute_query(consulta)
            if not df.empty:
                columna = df.columns[0]
                
                # Convertir a numérico si es necesario
                if df[columna].dtype == 'object':
                    df[columna] = pd.to_numeric(df[columna], errors='coerce')
                df = df.dropna(subset=[columna])
                
                if df.empty:
                    continue
                
                Q1 = df[columna].quantile(0.25)
                Q3 = df[columna].quantile(0.75)
                IQR = Q3 - Q1
                limite_inferior = Q1 - 1.5 * IQR
                limite_superior = Q3 + 1.5 * IQR
                
                outliers_df = df[(df[columna] < limite_inferior) | (df[columna] > limite_superior)]
                
                outliers[nombre] = {
                    'total_registros': len(df),
                    'outliers_encontrados': len(outliers_df),
                    'porcentaje_outliers': round((len(outliers_df) / len(df)) * 100, 2),
                    'limite_inferior': round(limite_inferior, 2),
                    'limite_superior': round(limite_superior, 2),
                    'min_valor': round(float(df[columna].min()), 2),
                    'max_valor': round(float(df[columna].max()), 2),
                    'outliers': [round(x, 2) for x in outliers_df[columna].tolist()[:10]]
                }
        except Exception as e:
            outliers[nombre] = {'error': str(e)}
    
    return outliers


# ============================================================================
# CODIFICACIÓN DE VARIABLES CATEGÓRICAS
# ============================================================================

def codificar_variables_categoricas() -> Dict[str, Any]:
    """
    Aplica Label Encoding a variables categóricas seleccionadas.
    
    Convierte valores categóricos a números enteros usando
    sklearn.preprocessing.LabelEncoder. Útil para preparar datos
    para modelos de machine learning.
    
    Returns:
        Diccionario con codificaciones para:
            - empleados_cargos: Codificación de JOB_ID
            - categorias_productos: Codificación de Nombre_Categoria
            - forma_pago: Codificación de Forma_Pago
            
        Cada entrada incluye:
            - categorias_originales: Lista de valores originales
            - categorias_codificadas: Lista de valores numéricos
            - mapeo: Diccionario original -> código
            - total_categorias: Número de categorías distintas
    """
    # Variables categóricas a codificar
    consultas = {
        'empleados_cargos': "SELECT DISTINCT JOB_ID FROM employees WHERE JOB_ID IS NOT NULL",
        'categorias_productos': "SELECT DISTINCT Nombre_Categoria FROM categorias WHERE Nombre_Categoria IS NOT NULL",
        'forma_pago': "SELECT DISTINCT Forma_Pago FROM pedidos WHERE Forma_Pago IS NOT NULL"
    }
    
    codificacion = {}
    
    for nombre, consulta in consultas.items():
        try:
            df = execute_query(consulta)
            if not df.empty:
                columna = df.columns[0]
                encoder = LabelEncoder()
                df_encoded = encoder.fit_transform(df[columna].astype(str))
                
                # Crear mapeo original -> codificado
                mapeo = {}
                for original, codificado in zip(df[columna], df_encoded):
                    mapeo[str(original)] = int(codificado)
                
                codificacion[nombre] = {
                    'categorias_originales': [str(x) for x in df[columna].tolist()],
                    'categorias_codificadas': df_encoded.tolist(),
                    'mapeo': mapeo,
                    'total_categorias': len(mapeo)
                }
        except Exception as e:
            codificacion[nombre] = {'error': str(e)}
    
    return codificacion


# ============================================================================
# NORMALIZACIÓN DE VARIABLES NUMÉRICAS
# ============================================================================

def normalizar_variables_numericas() -> Dict[str, Any]:
    """
    Aplica normalización a variables numéricas usando dos métodos.
    
    Para cada variable numérica, aplica:
    - StandardScaler: Estandarización (media=0, desviación=1)
    - MinMaxScaler: Escalamiento al rango [0, 1]
    
    Returns:
        Diccionario con resultados para:
            - salarios: Análisis de SALARY
            - precios: Análisis de Precio_por_Unidad
            - cantidades: Análisis de Cantidad
            
        Cada entrada incluye estadísticas de los datos originales y
        después de cada transformación, más una muestra de 5 valores.
    """
    # Datos para normalizar
    consultas = {
        'salarios': "SELECT SALARY FROM employees WHERE SALARY IS NOT NULL",
        'precios': "SELECT Precio_por_Unidad FROM productos WHERE Precio_por_Unidad IS NOT NULL",
        'cantidades': "SELECT Cantidad FROM detalles_pedidos WHERE Cantidad IS NOT NULL"
    }
    
    normalizacion = {}
    
    for nombre, consulta in consultas.items():
        try:
            df = execute_query(consulta)
            if not df.empty and len(df) > 1:
                columna = df.columns[0]
                
                # Convertir a numérico si es necesario
                if df[columna].dtype == 'object':
                    df[columna] = pd.to_numeric(df[columna], errors='coerce')
                df = df.dropna(subset=[columna])
                
                if df.empty or len(df) < 2:
                    continue
                
                datos = df[columna].values.reshape(-1, 1)
                
                # Standard Scaling (Z-score)
                scaler_standard = StandardScaler()
                standard_scaled = scaler_standard.fit_transform(datos)
                
                # Min-Max Scaling
                scaler_minmax = MinMaxScaler()
                minmax_scaled = scaler_minmax.fit_transform(datos)
                
                normalizacion[nombre] = {
                    'original': {
                        'media': round(float(df[columna].mean()), 2),
                        'desviacion': round(float(df[columna].std()), 2),
                        'min': round(float(df[columna].min()), 2),
                        'max': round(float(df[columna].max()), 2)
                    },
                    'standard_scaler': {
                        'media': round(float(standard_scaled.mean()), 2),
                        'desviacion': round(float(standard_scaled.std()), 2),
                        'min': round(float(standard_scaled.min()), 2),
                        'max': round(float(standard_scaled.max()), 2)
                    },
                    'minmax_scaler': {
                        'media': round(float(minmax_scaled.mean()), 2),
                        'desviacion': round(float(minmax_scaled.std()), 2),
                        'min': round(float(minmax_scaled.min()), 2),
                        'max': round(float(minmax_scaled.max()), 2)
                    },
                    'muestras': {
                        'originales': [round(x, 2) for x in df[columna].tolist()[:5]],
                        'standard': [round(x[0], 2) for x in standard_scaled[:5]],
                        'minmax': [round(x[0], 2) for x in minmax_scaled[:5]]
                    }
                }
        except Exception as e:
            normalizacion[nombre] = {'error': str(e)}
    
    return normalizacion


# ============================================================================
# FUNCIONES DE COMPATIBILIDAD
# ============================================================================
# Estas funciones mantienen la interfaz original para compatibilidad
# con código existente que pueda estar usando los nombres anteriores.

def lee_archivo():
    """Compatibilidad: retorna productos por categoría."""
    return ProductoQueries.por_categoria()

def pedidos_por_forma_pago():
    """Compatibilidad: retorna pedidos por forma de pago."""
    return PedidoQueries.por_forma_pago()

def pedidos_por_anio():
    """Compatibilidad: retorna pedidos por año."""
    return PedidoQueries.por_anio()

def empleados_por_departamento():
    """Compatibilidad: retorna empleados por departamento."""
    return EmpleadoQueries.por_departamento()

def pedidos_atendidos_por_empleado():
    """Compatibilidad: retorna pedidos atendidos por empleado."""
    return EmpleadoQueries.pedidos_atendidos()

def producto_mas_vendido():
    """Compatibilidad: retorna producto más vendido."""
    return ProductoQueries.mas_vendido()

def producto_mas_solicitado():
    """Compatibilidad: retorna producto más solicitado."""
    return ProductoQueries.mas_solicitado()

def top_clientes_por_valor(limite: int = 5):
    """Compatibilidad: retorna top clientes por valor."""
    return PedidoQueries.top_clientes_por_valor(limite=limite)

def top_productos_mas_vendidos(limite: int = 5):
    """Compatibilidad: retorna top productos más vendidos."""
    return ProductoQueries.top_ventas(limite=limite)

def top_productos_mas_solicitados(limite: int = 5):
    """Compatibilidad: retorna top productos más solicitados."""
    return ProductoQueries.top_solicitados(limite=limite)

def empleados_lugar_coincide():
    """Compatibilidad: retorna empleados con lugar coincide."""
    return EmpleadoQueries.contar_lugar_coincide()

def pedidos_por_mes():
    """Compatibilidad: retorna pedidos por mes."""
    return PedidoQueries.por_mes()

def top_empleados_mejor_pagados(limite: int = 5):
    """Compatibilidad: retorna top empleados mejor pagados."""
    return EmpleadoQueries.mejor_pagados(limite=limite)

def valor_nomina_total():
    """Compatibilidad: retorna valor total nómina."""
    return EmpleadoQueries.nomina_total()

def nomina_por_departamento():
    """Compatibilidad: retorna nómina por departamento."""
    return EmpleadoQueries.nomina_por_departamento()

def porcentaje_comision_empleado_top5(limite: int = 5):
    """Compatibilidad: retorna top empleados con mayor comisión."""
    return EmpleadoQueries.top_comisiones(limite=limite)

def empleados_lugar_igual():
    """Compatibilidad: retorna empleados con mismo lugar."""
    return EmpleadoQueries.lugar_coincide()

def obtener_tablas_bd():
    """Compatibilidad: retorna lista de tablas."""
    return get_table_names()

def obtener_datos_tabla(nombre_tabla):
    """Compatibilidad: retorna datos de tabla."""
    return get_table_data(nombre_tabla)

def obtener_estadisticas_precios():
    """Compatibilidad: retorna estadísticas de precios."""
    return Estadisticas.precios_productos()

def obtener_estadisticas_salarios():
    """Compatibilidad: retorna estadísticas de salarios."""
    return Estadisticas.salarios_empleados()

def obtener_estadisticas_cantidades_pedidos():
    """Compatibilidad: retorna estadísticas de cantidades."""
    return Estadisticas.cantidades_pedidos()

def analizar_distribucion():
    """Compatibilidad: retorna análisis de distribución."""
    return Estadisticas.analizar_distribucion()

def generar_matriz_correlacion():
    """Compatibilidad: retorna matriz de correlación."""
    return Estadisticas.generar_matriz_correlacion()