/**
 * ============================================================================
 * DASHBOARD DE PEDIDOS - MÓDULO DE VISUALIZACIONES
 * ============================================================================
 * 
 * Este módulo maneja todas las visualizaciones del dashboard de pedidos,
 * incluyendo gráficos, tablas y métricas. Utiliza Chart.js para las
 * visualizaciones y proporciona una carga secuencial controlada para
 * evitar sobrecarga del servidor.
 * 
 * @author Fabian Andrés Rincón
 * @version 1.0.0
 * @since Febrero 2026
 */

// ============================================================================
// CONFIGURACIÓN GLOBAL DE CHART.JS
// ============================================================================

/**
 * Configuración por defecto para todos los gráficos Chart.js
 * Establece la fuente y colores consistentes con el tema de la aplicación
 */
Chart.defaults.global.defaultFontFamily = 'Nunito';
Chart.defaults.global.defaultFontColor = '#858796';

/**
 * Almacena instancias de gráficos para permitir su destrucción controlada
 * @type {Object}
 */
const chartInstances = {};

// ============================================================================
// INICIALIZACIÓN SECUENCIAL DE GRÁFICAS
// ============================================================================

/**
 * Inicializa todas las gráficas del dashboard de forma secuencial
 * con delays progresivos para evitar sobrecargar el servidor
 * 
 * @listens DOMContentLoaded
 */
document.addEventListener('DOMContentLoaded', function() {
    console.log("Inicializando gráficas de forma secuencial...");
    
    const graphInitializers = [
        { name: 'Categorías', delay: 100, fn: inicializarGraficaCategorias },
        { name: 'Forma de Pago', delay: 300, fn: inicializarGraficaFormaPago },
        { name: 'Pedidos por Año', delay: 500, fn: inicializarGraficaPedidosAnio },
        { name: 'Empleados por Departamento', delay: 700, fn: inicializarGraficaEmpleadosDepartamento },
        { name: 'Pedidos por Empleado', delay: 900, fn: inicializarPedidosEmpleado },
        { name: 'Producto más vendido', delay: 1100, fn: inicializarProductoMasVendido },
        { name: 'Producto más solicitado', delay: 1300, fn: inicializarProductoMasSolicitado },
        { name: 'Top 5 clientes', delay: 1500, fn: inicializarTopClientes },
        { name: 'Top 5 productos vendidos', delay: 1700, fn: inicializarTopProductos },
        { name: 'Top 5 productos solicitados', delay: 1900, fn: inicializarTopProductosSolicitados },
        { name: 'Empleados lugar coincide', delay: 2100, fn: inicializarEmpleadosLugarCoincide },
        { name: 'Pedidos por mes', delay: 2300, fn: inicializarPedidosPorMes },
        { name: 'Empleados mejor pagados', delay: 2500, fn: inicializarEmpleadosMejorPagados },
        { name: 'Valor nómina', delay: 2700, fn: inicializarValorNomina },
        { name: 'Nómina por departamento', delay: 2900, fn: inicializarNominaDepartamento },
        { name: 'Comisión por empleado', delay: 3100, fn: inicializarComisionEmpleados },
        { name: 'Empleados lugar igual', delay: 3300, fn: inicializarEmpleadosLugarIgual }
    ];

    graphInitializers.forEach(({ name, delay, fn }) => {
        setTimeout(() => {
            console.log(`Inicializando gráfico: ${name}`);
            fn();
        }, delay);
    });
});

// ============================================================================
// FUNCIONES DE VISUALIZACIÓN - GRÁFICOS PRINCIPALES
// ============================================================================

/**
 * Inicializa el gráfico de productos por categoría
 * Gráfico de barras que muestra la distribución de productos
 * 
 * @async
 * @function inicializarGraficaCategorias
 * @returns {Promise<void>}
 */
async function inicializarGraficaCategorias() {
    try {
        const response = await fetch('/api/datos-grafico');
        const datos = await response.json();
        
        console.log("Gráfico 1 - Productos por categoría cargado");
        
        const canvas = document.getElementById("myAreaChart");
        if (!canvas) {
            console.error("No se encontró el canvas 'myAreaChart'");
            return;
        }

        if (chartInstances.myAreaChart) {
            chartInstances.myAreaChart.destroy();
        }

        chartInstances.myAreaChart = new Chart(canvas, {
            type: 'bar',
            data: {
                labels: datos.labels,
                datasets: [{
                    label: datos.titulo,
                    data: datos.data,
                    backgroundColor: generarPaletaColores(datos.labels.length),
                    borderColor: 'rgba(78, 115, 223, 1)',
                    borderWidth: 1
                }]
            },
            options: obtenerConfiguracionBarra('Productos por categoría')
        });
    } catch (error) {
        manejarErrorGrafico(1, error);
    }
}

/**
 * Inicializa el gráfico de pedidos por forma de pago
 * Gráfico de dona que muestra la distribución de métodos de pago
 * 
 * @async
 * @function inicializarGraficaFormaPago
 * @returns {Promise<void>}
 */
async function inicializarGraficaFormaPago() {
    try {
        const response = await fetch('/api/pedidos-forma-pago');
        const datos = await response.json();
        
        console.log("Gráfico 2 - Forma de pago cargado");
        
        const canvas = document.getElementById("myPieChart");
        if (!canvas) {
            console.error("No se encontró el canvas 'myPieChart'");
            return;
        }

        if (chartInstances.myPieChart) {
            chartInstances.myPieChart.destroy();
        }

        const colores = ["#4e73df", "#1cc88a"];
        
        chartInstances.myPieChart = new Chart(canvas, {
            type: 'doughnut',
            data: {
                labels: datos.labels,
                datasets: [{
                    data: datos.data,
                    backgroundColor: colores,
                    hoverBackgroundColor: colores.map(c => ajustarBrillo(c, -20)),
                    hoverBorderColor: "rgba(234, 236, 244, 1)"
                }]
            },
            options: obtenerConfiguracionDona()
        });

        actualizarLeyendaFormasPago(datos.labels, colores);
    } catch (error) {
        manejarErrorGrafico(2, error);
    }
}

/**
 * Inicializa el gráfico de pedidos por año
 * Gráfico de barras con gradiente que muestra evolución anual
 * 
 * @async
 * @function inicializarGraficaPedidosAnio
 * @returns {Promise<void>}
 */
async function inicializarGraficaPedidosAnio() {
    try {
        const response = await fetch('/api/pedidos-por-anio');
        const datos = await response.json();
        
        console.log("Gráfico 3 - Pedidos por año cargado");
        
        const canvas = document.getElementById("pedidosPorAnioChart");
        if (!canvas) {
            console.error("No se encontró el canvas 'pedidosPorAnioChart'");
            return;
        }

        if (chartInstances.pedidosPorAnioChart) {
            chartInstances.pedidosPorAnioChart.destroy();
        }

        const ctx = canvas.getContext("2d");
        const gradient = ctx.createLinearGradient(0, 0, 0, 400);
        gradient.addColorStop(0, "#4e73df");
        gradient.addColorStop(1, "#36b9cc");

        chartInstances.pedidosPorAnioChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: datos.labels,
                datasets: [{
                    label: datos.titulo,
                    data: datos.data,
                    backgroundColor: gradient,
                    borderColor: "#2e59d9",
                    borderWidth: 2,
                    hoverBackgroundColor: "#17a673",
                    hoverBorderColor: "#1cc88a"
                }]
            },
            options: obtenerConfiguracionEvolucionAnual()
        });
    } catch (error) {
        manejarErrorGrafico(3, error);
    }
}

/**
 * Inicializa el gráfico de empleados por departamento
 * Gráfico de radar que muestra distribución de personal
 * 
 * @async
 * @function inicializarGraficaEmpleadosDepartamento
 * @returns {Promise<void>}
 */
async function inicializarGraficaEmpleadosDepartamento() {
    try {
        const response = await fetch('/api/empleados-burbuja');
        const datos = await response.json();
        
        console.log("Gráfico 4 - Empleados por departamento cargado");

        const MAX_DEPARTMENTS = 8;
        const limitedLabels = datos.labels.slice(0, MAX_DEPARTMENTS);
        const limitedData = datos.data.slice(0, MAX_DEPARTMENTS);

        console.log(`Mostrando ${limitedLabels.length} de ${datos.labels.length} departamentos`);

        const canvas = document.getElementById("empleadosPolarChart");
        if (!canvas) {
            console.error("No se encontró el canvas 'empleadosPolarChart'");
            return;
        }

        if (chartInstances.empleadosPolarChart) {
            chartInstances.empleadosPolarChart.destroy();
        }

        const ctx = canvas.getContext("2d");

        chartInstances.empleadosPolarChart = new Chart(ctx, {
            type: 'radar',
            data: {
                labels: limitedLabels,
                datasets: [{
                    label: 'Cantidad de empleados',
                    data: limitedData,
                    backgroundColor: 'rgba(78, 115, 223, 0.2)',
                    borderColor: 'rgba(78, 115, 223, 1)',
                    pointBackgroundColor: 'rgba(28, 200, 138, 1)',
                    pointBorderColor: '#fff',
                    pointHoverBackgroundColor: '#fff',
                    pointHoverBorderColor: 'rgba(78, 115, 223, 1)',
                    borderWidth: 2
                }]
            },
            options: obtenerConfiguracionRadar(MAX_DEPARTMENTS)
        });
    } catch (error) {
        manejarErrorGrafico(4, error);
    }
}

// ============================================================================
// FUNCIONES DE VISUALIZACIÓN - MÉTRICAS Y TABLAS
// ============================================================================

/**
 * Inicializa la visualización de pedidos por empleado
 * Muestra barras de progreso con el rendimiento relativo
 * 
 * @async
 * @function inicializarPedidosEmpleado
 * @returns {Promise<void>}
 */
async function inicializarPedidosEmpleado() {
    try {
        const response = await fetch('/api/pedidos-empleado');
        const datos = await response.json();
        
        console.log("Gráfico 5 - Pedidos por empleado cargado");

        const container = document.getElementById("empleadosPedidos");
        if (!container) {
            console.error("No existe el contenedor con id 'empleadosPedidos'");
            return;
        }

        container.innerHTML = "";

        if (!validarDatosGrafico(datos)) {
            container.innerHTML = '<p class="text-center text-muted">No hay datos disponibles</p>';
            return;
        }

        const maxPedidos = Math.max(...datos.data);
        
        datos.labels.forEach((empleado, index) => {
            const pedidos = datos.data[index];
            const porcentaje = (pedidos / maxPedidos) * 100;

            container.appendChild(crearBarraProgreso(empleado, pedidos, porcentaje));
        });
    } catch (error) {
        manejarErrorGrafico(5, error, "empleadosPedidos");
    }
}

/**
 * Inicializa la tarjeta de producto más vendido
 * 
 * @async
 * @function inicializarProductoMasVendido
 * @returns {Promise<void>}
 */
async function inicializarProductoMasVendido() {
    try {
        const response = await fetch('/api/producto-mas-vendido');
        const data = await response.json();
        
        console.log("Gráfico 6 - Producto más vendido cargado");
        
        const container = document.getElementById("productoMasVendido");
        if (!container) return;

        container.innerHTML = crearTarjetaMetrica(
            data.producto,
            `Cantidad vendida: ${data.cantidad}`,
            'producto'
        );
    } catch (error) {
        manejarErrorGrafico(6, error, "productoMasVendido");
    }
}

/**
 * Inicializa la tarjeta de producto más solicitado
 * 
 * @async
 * @function inicializarProductoMasSolicitado
 * @returns {Promise<void>}
 */
async function inicializarProductoMasSolicitado() {
    try {
        const response = await fetch('/api/producto-mas-solicitado');
        const data = await response.json();
        
        console.log("Gráfico 7 - Producto más solicitado cargado");
        
        const container = document.getElementById("productoMasSolicitado");
        if (!container) return;

        if (data.error) {
            container.innerHTML = `<p class="text-danger text-center">${data.error}</p>`;
            return;
        }

        container.innerHTML = crearTarjetaMetrica(
            data.producto,
            `Veces solicitado: ${data.veces_solicitado}`,
            'solicitado'
        );
    } catch (error) {
        manejarErrorGrafico(7, error, "productoMasSolicitado");
    }
}

/**
 * Inicializa el gráfico de top clientes
 * Gráfico de barras con los clientes más importantes
 * 
 * @async
 * @function inicializarTopClientes
 * @returns {Promise<void>}
 */
async function inicializarTopClientes() {
    try {
        const response = await fetch('/api/top-clientes');
        const data = await response.json();
        
        console.log("Gráfico 8 - Top clientes cargado");
        
        const canvas = document.getElementById("graficoTopClientes");
        if (!canvas) return;

        if (data.error) {
            manejarErrorEnCanvas(canvas, data.error);
            return;
        }

        if (chartInstances.graficoTopClientes) {
            chartInstances.graficoTopClientes.destroy();
        }

        chartInstances.graficoTopClientes = new Chart(canvas, {
            type: 'bar',
            data: {
                labels: data.labels,
                datasets: [{
                    label: "Valor Facturado ($)",
                    data: data.data,
                    backgroundColor: ['#0d43e4', '#1cc88a', '#36b9cc', '#f6c23e', '#e74a3b'],
                    borderWidth: 1
                }]
            },
            options: obtenerConfiguracionTopClientes(data.titulo)
        });
    } catch (error) {
        manejarErrorGrafico(8, error, "graficoTopClientes");
    }
}

// ============================================================================
// FUNCIONES DE VISUALIZACIÓN - TABLAS
// ============================================================================

/**
 * Inicializa la tabla de top productos más vendidos
 * 
 * @async
 * @function inicializarTopProductos
 * @returns {Promise<void>}
 */
async function inicializarTopProductos() {
    try {
        const response = await fetch('/api/top-productos');
        const data = await response.json();
        
        console.log("Gráfico 9 - Top productos cargado");
        
        const tbody = document.getElementById("bodyTopProductos");
        if (!tbody) return;

        if (data.error) {
            tbody.innerHTML = `<tr><td colspan="4" class="text-danger">${data.error}</td></tr>`;
            return;
        }

        tbody.innerHTML = data.productos.map(p => `
            <tr>
                <td>${p.Id_Producto}</td>
                <td>${p.producto}</td>
                <td><strong>${p.total_vendido.toLocaleString()}</strong></td>
                <td>$${formatearMoneda(p.valor_total)}</td>
            </tr>
        `).join('');
    } catch (error) {
        manejarErrorGrafico(9, error, "bodyTopProductos");
    }
}

/**
 * Inicializa la tabla de top productos más solicitados
 * 
 * @async
 * @function inicializarTopProductosSolicitados
 * @returns {Promise<void>}
 */
async function inicializarTopProductosSolicitados() {
    try {
        const response = await fetch('/api/top-productos-solicitados');
        const data = await response.json();
        
        console.log("Gráfico 10 - Top productos solicitados cargado");
        
        const tbody = document.getElementById("bodyTopSolicitados");
        if (!tbody) return;

        if (data.error) {
            tbody.innerHTML = `<tr><td colspan="4" class="text-danger">${data.error}</td></tr>`;
            return;
        }

        tbody.innerHTML = data.productos.map((p, i) => `
            <tr>
                <td>${p.Id_Producto}</td>
                <td>${p.producto}</td>
                <td><strong>${p.veces_solicitado.toLocaleString()}</strong></td>
                <td>${p.cantidad_total.toLocaleString()}</td>
            </tr>
        `).join('');
    } catch (error) {
        manejarErrorGrafico(10, error, "bodyTopSolicitados");
    }
}

// ============================================================================
// FUNCIONES DE VISUALIZACIÓN - MÉTRICAS AVANZADAS
// ============================================================================

/**
 * Inicializa la tarjeta de empleados con lugar coincidente
 * 
 * @async
 * @function inicializarEmpleadosLugarCoincide
 * @returns {Promise<void>}
 */
async function inicializarEmpleadosLugarCoincide() {
    try {
        const response = await fetch('/api/empleados-lugar-coincide');
        const data = await response.json();
        
        console.log("Gráfico 11 - Empleados lugar coincide cargado");
        
        const container = document.getElementById("empleadosLugarCoincide");
        if (!container) return;

        if (data.error) {
            container.innerHTML = `<p class="text-danger text-center">${data.error}</p>`;
            return;
        }

        container.innerHTML = crearTarjetaMetrica(
            data.cantidad.toString(),
            data.titulo,
            'lugar-coincide',
            true
        );
    } catch (error) {
        manejarErrorGrafico(11, error, "empleadosLugarCoincide");
    }
}

/**
 * Inicializa el gráfico de pedidos por mes
 * Gráfico de líneas que compara múltiples años
 * 
 * @async
 * @function inicializarPedidosPorMes
 * @returns {Promise<void>}
 */
async function inicializarPedidosPorMes() {
    try {
        const response = await fetch('/api/pedidos-por-mes');
        const data = await response.json();
        
        console.log("Gráfico 12 - Pedidos por mes cargado:", data);
        
        const canvas = document.getElementById("pedidosMesChart");
        if (!canvas) {
            console.error("No se encontró el canvas 'pedidosMesChart'");
            return;
        }

        if (data.error) {
            manejarErrorEnCanvas(canvas, data.error);
            return;
        }

        const ctx = canvas.getContext("2d");
        ctx.clearRect(0, 0, canvas.width, canvas.height);

        if (!data.datasets || data.datasets.length === 0) {
            canvas.outerHTML = '<p class="text-muted text-center">No hay datos para mostrar</p>';
            return;
        }

        if (chartInstances.pedidosMesChart) {
            chartInstances.pedidosMesChart.destroy();
        }

        const meses = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 
                      'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic'];
        const colores = ['#4e73df', '#1cc88a', '#36b9cc', '#f6c23e', '#e74a3b'];

        chartInstances.pedidosMesChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: meses,
                datasets: data.datasets.map((ds, i) => ({
                    label: ds.label,
                    data: ds.data,
                    fill: true,
                    tension: 0.4,
                    borderColor: colores[i % colores.length],
                    backgroundColor: colores[i % colores.length] + '40',
                    pointBackgroundColor: colores[i % colores.length],
                    pointBorderColor: '#fff',
                    pointBorderWidth: 2,
                    pointRadius: 5,
                    pointHoverRadius: 8,
                    borderWidth: 3
                }))
            },
            options: obtenerConfiguracionLineas()
        });

        console.log("Gráfica de pedidos por mes creada exitosamente");
    } catch (error) {
        manejarErrorGrafico(12, error, "pedidosMesChart");
    }
}

/**
 * Inicializa la tabla de empleados mejor pagados
 * 
 * @async
 * @function inicializarEmpleadosMejorPagados
 * @returns {Promise<void>}
 */
async function inicializarEmpleadosMejorPagados() {
    try {
        const response = await fetch('/api/empleados-mejor-pagados');
        const data = await response.json();
        
        console.log("Gráfico 13 - Empleados mejor pagados cargado");
        
        const tbody = document.getElementById("tablaEmpleadosPagadosBody");
        if (!tbody) return;

        tbody.innerHTML = "";

        if (!data.valores || data.valores.length === 0) {
            tbody.innerHTML = `<tr><td colspan="4" class="text-danger">No se encontraron datos</td></tr>`;
            return;
        }

        data.valores.forEach(fila => {
            const tr = document.createElement("tr");
            tr.innerHTML = `
                <td>${fila[0]}</td>
                <td>${fila[1]}</td>
                <td>${fila[2]}</td>
                <td><strong>$${formatearMoneda(parseFloat(fila[3]))}</strong></td>
            `;
            tbody.appendChild(tr);
        });
    } catch (error) {
        manejarErrorGrafico(13, error, "tablaEmpleadosPagadosBody");
    }
}

/**
 * Inicializa la tarjeta de valor total de nómina
 * 
 * @async
 * @function inicializarValorNomina
 * @returns {Promise<void>}
 */
async function inicializarValorNomina() {
    try {
        const response = await fetch('/api/valor-nomina');
        const data = await response.json();
        
        console.log("Gráfico 14 - Valor nómina cargado");
        
        const container = document.getElementById("valorNomina");
        if (!container) return;

        if (data.error) {
            container.innerHTML = `<p class="text-danger text-center">${data.error}</p>`;
            return;
        }

        container.innerHTML = crearTarjetaMetrica(
            data.valor,
            data.titulo,
            'nomina',
            true
        );
    } catch (error) {
        manejarErrorGrafico(14, error, "valorNomina");
    }
}

/**
 * Inicializa el gráfico de nómina por departamento
 * Gráfico de barras con distribución salarial
 * 
 * @async
 * @function inicializarNominaDepartamento
 * @returns {Promise<void>}
 */
async function inicializarNominaDepartamento() {
    try {
        const response = await fetch('/api/nomina-departamento');
        const datos = await response.json();
        
        console.log("Gráfico 15 - Nómina por departamento cargado");
        
        const canvas = document.getElementById('nominaDepartamentoChart');
        if (!canvas) return;

        if (datos.error) {
            manejarErrorEnCanvas(canvas, datos.error);
            return;
        }

        if (chartInstances.nominaDepartamentoChart) {
            chartInstances.nominaDepartamentoChart.destroy();
        }

        const ctx = canvas.getContext('2d');
        
        chartInstances.nominaDepartamentoChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: datos.labels,
                datasets: [{
                    label: 'Valor de Nómina ($)',
                    data: datos.data,
                    backgroundColor: generarPaletaColores(datos.labels.length),
                    borderRadius: 8,
                    hoverBackgroundColor: '#2e59d9'
                }]
            },
            options: obtenerConfiguracionNomina(datos.titulo)
        });
    } catch (error) {
        manejarErrorGrafico(15, error, "nominaDepartamentoChart");
    }
}

/**
 * Inicializa el gráfico de comisiones por empleado
 * Gráfico de dona con porcentajes de comisión
 * 
 * @async
 * @function inicializarComisionEmpleados
 * @returns {Promise<void>}
 */
async function inicializarComisionEmpleados() {
    try {
        const response = await fetch('/api/comision-empleados');
        const datos = await response.json();
        
        console.log("Gráfico 16 - Comisión por empleado cargado");

        const canvas = document.getElementById('comisionEmpleadosChart');
        if (!canvas) {
            console.error("No se encontró el canvas con id='comisionEmpleadosChart'");
            return;
        }

        if (datos.error) {
            manejarErrorEnCanvas(canvas, datos.error);
            return;
        }

        if (!datos.data || datos.data.length === 0) {
            canvas.outerHTML = '<p class="text-muted text-center">Sin datos para graficar</p>';
            return;
        }

        if (chartInstances.comisionEmpleadosChart) {
            chartInstances.comisionEmpleadosChart.destroy();
        }

        const ctx = canvas.getContext('2d');
        const colores = ['#4e73df', '#1cc88a', '#36b9cc', '#f6c23e', '#e74a3b'];

        chartInstances.comisionEmpleadosChart = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: datos.labels,
                datasets: [{
                    data: datos.data,
                    backgroundColor: colores,
                    borderColor: '#ffffff',
                    borderWidth: 2
                }]
            },
            options: obtenerConfiguracionComision(datos.titulo)
        });
    } catch (error) {
        manejarErrorGrafico(16, error, "comisionEmpleadosChart");
    }
}

/**
 * Inicializa la tarjeta de empleados con mismo lugar
 * Muestra lista detallada de empleados con ubicaciones coincidentes
 * 
 * @async
 * @function inicializarEmpleadosLugarIgual
 * @returns {Promise<void>}
 */
async function inicializarEmpleadosLugarIgual() {
    try {
        const response = await fetch('/api/empleados-lugar-igual');
        
        if (!response.ok) {
            throw new Error(`Error HTTP: ${response.status}`);
        }
        
        const datos = await response.json();
        
        console.log("Gráfico 17 - Empleados lugar igual cargado:", datos);
        
        const card = document.getElementById("empleadosLugarIgual");
        if (!card) return;

        if (datos.error) {
            card.innerHTML = `<p class="text-danger text-center">${datos.error}</p>`;
            return;
        }

        if (!datos.empleados || datos.empleados.length === 0) {
            card.innerHTML = crearMensajeSinDatos();
            return;
        }

        card.innerHTML = crearListaEmpleados(datos);
    } catch (error) {
        manejarErrorGrafico(17, error, "empleadosLugarIgual");
    }
}

// ============================================================================
// FUNCIONES AUXILIARES Y UTILITARIAS
// ============================================================================

/**
 * Genera una paleta de colores para gráficos
 * 
 * @param {number} cantidad - Número de colores necesarios
 * @returns {string[]} Array de colores en formato rgba
 */
function generarPaletaColores(cantidad) {
    const coloresBase = [
        'rgba(78, 115, 223, 0.6)',
        'rgba(28, 200, 138, 0.6)',
        'rgba(246, 194, 62, 0.6)',
        'rgba(231, 74, 59, 0.6)',
        'rgba(133, 135, 150, 0.6)',
        'rgba(54, 185, 204, 0.6)',
        'rgba(255, 193, 7, 0.6)',
        'rgba(40, 167, 69, 0.6)'
    ];
    
    return Array(cantidad).fill(0).map((_, i) => 
        coloresBase[i % coloresBase.length]
    );
}

/**
 * Ajusta el brillo de un color hexadecimal
 * 
 * @param {string} color - Color en formato hexadecimal (#RRGGBB)
 * @param {number} porcentaje - Porcentaje de ajuste (-100 a 100)
 * @returns {string} Color ajustado
 */
function ajustarBrillo(color, porcentaje) {
    return color;
}

/**
 * Valida que los datos del gráfico sean correctos
 * 
 * @param {Object} datos - Datos a validar
 * @returns {boolean} True si los datos son válidos
 */
function validarDatosGrafico(datos) {
    return datos && 
           datos.labels && 
           datos.data && 
           datos.labels.length > 0 && 
           datos.labels.length === datos.data.length;
}

/**
 * Formatea un número como moneda
 * 
 * @param {number} valor - Valor a formatear
 * @returns {string} Valor formateado
 */
function formatearMoneda(valor) {
    return valor.toLocaleString(undefined, { minimumFractionDigits: 2 });
}

/**
 * Maneja errores en gráficos de forma centralizada
 * 
 * @param {number} numeroGrafico - Número identificador del gráfico
 * @param {Error} error - Error ocurrido
 * @param {string} containerId - ID del contenedor (opcional)
 */
function manejarErrorGrafico(numeroGrafico, error, containerId) {
    console.error(`Error en gráfico ${numeroGrafico}:`, error);
    
    if (containerId) {
        const container = document.getElementById(containerId);
        if (container) {
            container.innerHTML = `
                <p class="text-danger text-center">
                    Error al cargar los datos: ${error.message}
                </p>
            `;
        }
    }
}

/**
 * Maneja error en canvas mostrando mensaje
 * 
 * @param {HTMLElement} canvas - Elemento canvas
 * @param {string} mensaje - Mensaje de error
 */
function manejarErrorEnCanvas(canvas, mensaje) {
    canvas.outerHTML = `<p class="text-danger text-center">${mensaje}</p>`;
}

/**
 * Crea una barra de progreso para visualización
 * 
 * @param {string} empleado - Nombre del empleado
 * @param {number} pedidos - Cantidad de pedidos
 * @param {number} porcentaje - Porcentaje relativo
 * @returns {HTMLElement} Elemento DOM creado
 */
function crearBarraProgreso(empleado, pedidos, porcentaje) {
    const div = document.createElement('div');
    div.className = 'mb-3';
    div.innerHTML = `
        <div class="d-flex justify-content-between">
            <span>${empleado}</span>
            <span><strong>${pedidos} pedidos</strong></span>
        </div>
        <div class="progress">
            <div class="progress-bar bg-info"
                 role="progressbar"
                 style="width: ${porcentaje}%;">
            </div>
        </div>
    `;
    return div;
}

/**
 * Crea una tarjeta de métrica estilizada
 * 
 * @param {string} valor - Valor principal
 * @param {string} descripcion - Descripción
 * @param {string} tipo - Tipo de métrica
 * @param {boolean} grande - Si es tamaño grande
 * @returns {string} HTML de la tarjeta
 */
function crearTarjetaMetrica(valor, descripcion, tipo, grande = false) {
    const estilos = {
        producto: 'linear-gradient(135deg, #4e73df, #36b9cc)',
        solicitado: 'linear-gradient(135deg, #1cc88a, #36b9cc)',
        'lugar-coincide': 'linear-gradient(135deg, #4e73df, #36b9cc)',
        nomina: 'linear-gradient(135deg, #4e73df, #36b9cc)'
    };

    const tamanoTitulo = grande ? '2.5rem' : '2rem';
    const tamanoTexto = grande ? '1.2rem' : '1.2rem';

    return `
        <div class="text-center p-4" 
             style="background: ${estilos[tipo] || estilos.producto}; 
                    border-radius: 20px; 
                    color: white; 
                    box-shadow: 0 4px 12px rgba(0,0,0,0.15);">
            <h2 style="font-weight: 800; font-size: ${tamanoTitulo}; margin-bottom: 0.5rem;">
                ${valor}
            </h2>
            <p style="font-size: ${tamanoTexto};">
                ${descripcion}
            </p>
        </div>
    `;
}

/**
 * Crea mensaje de "sin datos"
 * 
 * @returns {string} HTML del mensaje
 */
function crearMensajeSinDatos() {
    return `
        <div class="text-center p-4">
            <i class="fas fa-users fa-3x text-muted mb-3"></i>
            <p class="text-muted">No se encontraron empleados con coincidencia de lugar</p>
        </div>
    `;
}

/**
 * Crea lista de empleados para visualización
 * 
 * @param {Object} datos - Datos de empleados
 * @returns {string} HTML de la lista
 */
function crearListaEmpleados(datos) {
    let contenido = `
        <div class="p-4" 
             style="background: linear-gradient(135deg, #1cc88a, #36b9cc);
                    border-radius: 20px;
                    color: white;
                    box-shadow: 0 4px 12px rgba(0,0,0,0.15);">
            <h5 style="font-weight: bold; text-align: center;">${datos.titulo}</h5>
            <hr style="border-color: rgba(255,255,255,0.4); width: 80%; margin: 1rem auto;">
            <div class="text-center mb-3">
                <span style="font-size: 2rem; font-weight: bold;">${datos.empleados.length}</span>
                <p style="margin: 0;">empleados encontrados</p>
            </div>
            <ul style="list-style: none; padding: 0; font-size: 1.1rem; text-align: left;">
    `;

    datos.empleados.forEach((empleado, i) => {
        contenido += `
            <li class="mb-2">
                <strong>${empleado}</strong><br>
                <em>${datos.lugares[i] || 'Lugar no especificado'}</em>
            </li>
        `;
    });

    contenido += `</ul></div>`;
    return contenido;
}

// ============================================================================
// CONFIGURACIONES DE CHART.JS
// ============================================================================

/**
 * Obtiene configuración para gráfico de barras simple
 * 
 * @param {string} titulo - Título del gráfico
 * @returns {Object} Configuración de Chart.js
 */
function obtenerConfiguracionBarra(titulo) {
    return {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
            yAxes: [{
                ticks: { 
                    beginAtZero: true, 
                    precision: 0 
                }
            }]
        },
        legend: { 
            display: false 
        },
        plugins: {
            title: {
                display: true,
                text: titulo,
                color: '#4e73df',
                font: { size: 16, weight: 'bold' }
            }
        }
    };
}

/**
 * Obtiene configuración para gráfico de dona
 * 
 * @returns {Object} Configuración de Chart.js
 */
function obtenerConfiguracionDona() {
    return {
        maintainAspectRatio: false,
        tooltips: {
            backgroundColor: "rgb(255,255,255)",
            bodyFontColor: "#858796",
            borderColor: '#dddfeb',
            borderWidth: 1,
            xPadding: 15,
            yPadding: 15,
            displayColors: false,
            caretPadding: 10
        },
        legend: { 
            display: false 
        },
        cutoutPercentage: 70
    };
}

/**
 * Obtiene configuración para gráfico de evolución anual
 * 
 * @returns {Object} Configuración de Chart.js
 */
function obtenerConfiguracionEvolucionAnual() {
    return {
        responsive: true,
        maintainAspectRatio: false,
        animation: {
            duration: 2000,
            easing: 'easeOutBounce'
        },
        plugins: {
            title: {
                display: true,
                text: 'Evolución anual de pedidos',
                color: '#4e73df',
                font: { size: 16, weight: 'bold' }
            },
            tooltip: {
                backgroundColor: "rgb(255,255,255)",
                bodyColor: "#858796",
                titleColor: "#4e73df",
                borderColor: "#dddfeb",
                borderWidth: 1
            }
        },
        scales: {
            x: {
                grid: { display: false },
                title: {
                    display: true,
                    text: "Año",
                    color: "#4e73df"
                }
            },
            y: {
                beginAtZero: true,
                title: {
                    display: true,
                    text: "Cantidad de pedidos",
                    color: "#4e73df"
                },
                ticks: {
                    precision: 0
                }
            }
        }
    };
}

/**
 * Obtiene configuración para gráfico de radar
 * 
 * @param {number} maxDepartments - Máximo de departamentos a mostrar
 * @returns {Object} Configuración de Chart.js
 */
function obtenerConfiguracionRadar(maxDepartments) {
    return {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
            r: {
                beginAtZero: true,
                grid: { 
                    color: 'rgba(234, 236, 244, 0.5)',
                    circular: true
                },
                ticks: { 
                    color: '#4e73df',
                    backdropColor: 'transparent',
                    stepSize: 1
                },
                pointLabels: { 
                    color: '#4e73df',
                    font: { size: 11 }
                },
                angleLines: {
                    color: 'rgba(234, 236, 244, 0.8)'
                }
            }
        },
        plugins: {
            legend: { 
                position: 'bottom',
                labels: {
                    boxWidth: 12,
                    font: { size: 11 }
                }
            },
            title: {
                display: true,
                text: `Cantidad de empleados por departamento (Top ${maxDepartments})`,
                font: { size: 14, weight: 'bold' },
                color: '#4e73df',
                padding: 20
            },
            tooltip: {
                callbacks: {
                    label: function(context) {
                        return `Empleados: ${context.raw}`;
                    }
                }
            }
        },
        elements: {
            line: {
                tension: 0.1
            }
        }
    };
}

/**
 * Obtiene configuración para gráfico de top clientes
 * 
 * @param {string} titulo - Título del gráfico
 * @returns {Object} Configuración de Chart.js
 */
function obtenerConfiguracionTopClientes(titulo) {
    return {
        responsive: true,
        plugins: {
            legend: { display: false },
            title: {
                display: true,
                text: titulo,
                font: { size: 16 }
            }
        },
        scales: {
            y: {
                beginAtZero: true,
                title: {
                    display: true,
                    text: 'Valor Facturado ($)'
                }
            }
        }
    };
}

/**
 * Obtiene configuración para gráfico de líneas
 * 
 * @returns {Object} Configuración de Chart.js
 */
function obtenerConfiguracionLineas() {
    return {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: { 
                position: 'top',
                labels: {
                    font: {
                        size: 12,
                        weight: 'bold'
                    },
                    padding: 20
                }
            },
            title: {
                display: true,
                text: 'Pedidos por mes (Comparación años)',
                color: '#4e73df',
                font: { 
                    size: 16, 
                    weight: 'bold',
                    family: 'Nunito'
                },
                padding: 20
            },
            tooltip: {
                backgroundColor: 'rgba(0, 0, 0, 0.8)',
                titleFont: { 
                    size: 13, 
                    weight: 'bold',
                    family: 'Nunito'
                },
                bodyFont: { 
                    size: 12,
                    family: 'Nunito'
                },
                padding: 12,
                cornerRadius: 6,
                displayColors: true,
                mode: 'index',
                intersect: false
            }
        },
        scales: {
            x: {
                grid: {
                    display: true,
                    color: 'rgba(0, 0, 0, 0.1)'
                },
                title: {
                    display: true,
                    text: 'Meses',
                    color: '#4e73df',
                    font: {
                        size: 14,
                        weight: 'bold',
                        family: 'Nunito'
                    }
                },
                ticks: {
                    font: {
                        family: 'Nunito'
                    }
                }
            },
            y: {
                beginAtZero: true,
                grid: {
                    display: true,
                    color: 'rgba(0, 0, 0, 0.1)'
                },
                title: {
                    display: true,
                    text: 'Cantidad de Pedidos',
                    color: '#4e73df',
                    font: {
                        size: 14,
                        weight: 'bold',
                        family: 'Nunito'
                    }
                },
                ticks: {
                    font: {
                        family: 'Nunito'
                    },
                    precision: 0
                }
            }
        },
        interaction: {
            mode: 'nearest',
            axis: 'x',
            intersect: false
        },
        elements: {
            line: {
                tension: 0.4
            }
        },
        animation: {
            duration: 1000,
            easing: 'easeOutQuart'
        }
    };
}

/**
 * Obtiene configuración para gráfico de nómina por departamento
 * 
 * @param {string} titulo - Título del gráfico
 * @returns {Object} Configuración de Chart.js
 */
function obtenerConfiguracionNomina(titulo) {
    return {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                display: true,
                position: 'top'
            },
            title: {
                display: true,
                text: titulo,
                font: { size: 16, weight: 'bold' }
            },
            tooltip: {
                callbacks: {
                    label: (tooltipItem) => ` $${tooltipItem.raw.toLocaleString()}`
                }
            }
        },
        scales: {
            y: {
                beginAtZero: true,
                ticks: {
                    callback: (value) => `$${value.toLocaleString()}`
                }
            }
        },
        animation: {
            duration: 1200,
            easing: 'easeOutElastic'
        }
    };
}

/**
 * Obtiene configuración para gráfico de comisiones
 * 
 * @param {string} titulo - Título del gráfico
 * @returns {Object} Configuración de Chart.js
 */
function obtenerConfiguracionComision(titulo) {
    return {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            title: {
                display: true,
                text: titulo || 'Porcentaje de comisión por empleado (Top 5)',
                color: '#4e73df',
                font: {
                    size: 16,
                    weight: 'bold'
                }
            },
            legend: {
                position: 'bottom',
                labels: {
                    color: '#2e2e2e',
                    font: { size: 12 }
                }
            },
            tooltip: {
                callbacks: {
                    label: (context) => `${context.label}: ${context.raw.toFixed(2)}%`
                }
            }
        },
        cutout: '60%',
        animation: {
            animateRotate: true,
            animateScale: true,
            duration: 1500
        }
    };
}

/**
 * Actualiza la leyenda de formas de pago
 * 
 * @param {string[]} labels - Etiquetas de las formas de pago
 * @param {string[]} colores - Colores asociados
 */
function actualizarLeyendaFormasPago(labels, colores) {
    const leyendaDiv = document.getElementById("leyendaFormasPago");
    if (leyendaDiv) {
        leyendaDiv.innerHTML = labels.map((label, i) => `
            <span class="mr-2">
                <i class="fas fa-circle" style="color:${colores[i]}"></i> ${label}
            </span>
        `).join('');
    }
}

// ============================================================================
// FUNCIONALIDAD DE GENERACIÓN DE REPORTES PDF
// ============================================================================

/**
 * Genera un reporte completo en PDF con todos los datos del dashboard
 * 
 * @async
 * @function generarReporteCompleto
 * @returns {Promise<void>}
 */
async function generarReporteCompleto() {
    console.log("Generando reporte completo...");
    
    const btn = document.querySelector('.btn-success');
    const originalText = btn.innerHTML;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Generando...';
    btn.disabled = true;

    try {
        if (typeof jspdf === 'undefined') {
            throw new Error('Librería PDF no disponible');
        }

        const { jsPDF } = window.jspdf;
        const doc = new jsPDF();
        
        const fecha = new Date();
        const fechaStr = fecha.toLocaleDateString('es-ES');
        const horaStr = fecha.toLocaleTimeString('es-ES');

        generarPortadaPDF(doc, fechaStr, horaStr);
        generarResumenEjecutivoPDF(doc);
        generarEstadisticasDetalladasPDF(doc);
        agregarPieDePaginaPDF(doc);

        const nombreArchivo = `reporte-pedidos-${fechaStr.replace(/\//g, '-')}.pdf`;
        doc.save(nombreArchivo);

        console.log("Reporte completo generado:", nombreArchivo);
        mostrarNotificacionExito(`Reporte PDF "${nombreArchivo}" descargado exitosamente`);

    } catch (error) {
        console.error("Error:", error);
        mostrarNotificacionError(`Error al generar reporte: ${error.message}`);
    } finally {
        btn.innerHTML = originalText;
        btn.disabled = false;
    }
}

/**
 * Genera la portada del PDF
 * 
 * @param {Object} doc - Documento jsPDF
 * @param {string} fechaStr - Fecha formateada
 * @param {string} horaStr - Hora formateada
 */
function generarPortadaPDF(doc, fechaStr, horaStr) {
    doc.setFont('helvetica');
    doc.setFontSize(24);
    doc.setTextColor(78, 115, 223);
    doc.text('REPORTE DEL SISTEMA', 105, 50, { align: 'center' });
    doc.text('DE PEDIDOS', 105, 65, { align: 'center' });
    
    doc.setFontSize(16);
    doc.setTextColor(100, 100, 100);
    doc.text('Dashboard Administrativo', 105, 85, { align: 'center' });
    
    doc.setFontSize(12);
    doc.text(`Generado el: ${fechaStr}`, 105, 110, { align: 'center' });
    doc.text(`Hora: ${horaStr}`, 105, 120, { align: 'center' });
    
    doc.setFontSize(10);
    doc.setTextColor(150, 150, 150);
    doc.text('Sistema de Gestión Integral de Pedidos', 105, 140, { align: 'center' });
}

/**
 * Genera la página de resumen ejecutivo del PDF
 * 
 * @param {Object} doc - Documento jsPDF
 */
function generarResumenEjecutivoPDF(doc) {
    doc.addPage();
    let y = 30;
    
    doc.setFontSize(18);
    doc.setTextColor(78, 115, 223);
    doc.text('RESUMEN EJECUTIVO', 20, y);
    y += 20;
    
    doc.setFontSize(11);
    doc.setTextColor(60, 60, 60);
    
    const resumen = [
        `Sistema operativo: PEDIDOS Dashboard v1.0`,
        `Fecha de generación: ${new Date().toLocaleDateString('es-ES')} ${new Date().toLocaleTimeString('es-ES')}`,
        `Estado del sistema: OPERATIVO`,
        `Módulos activos: ${document.querySelectorAll('.card').length}`,
        `Gráficos renderizados: ${document.querySelectorAll('canvas').length}`,
        `Usuario: Administrador del Sistema`
    ];
    
    resumen.forEach(linea => {
        doc.text('• ' + linea, 25, y);
        y += 8;
    });
    
    y += 15;
    
    doc.setFontSize(16);
    doc.setTextColor(78, 115, 223);
    doc.text('MÉTRICAS PRINCIPALES', 20, y);
    y += 20;
    
    doc.setFontSize(10);
    
    const metricas = [
        { nombre: 'PEDIDOS POR AÑO', desc: 'Evolución anual de pedidos procesados' },
        { nombre: 'EMPLEADOS POR DEPARTAMENTO', desc: 'Distribución del personal por áreas' },
        { nombre: 'PRODUCTOS POR CATEGORÍA', desc: 'Inventario categorizado del sistema' },
        { nombre: 'FORMAS DE PAGO', desc: 'Métodos de pago más utilizados' },
        { nombre: 'PRODUCTOS MÁS VENDIDOS', desc: 'Top 5 productos con mayores ventas' },
        { nombre: 'TOP CLIENTES', desc: 'Clientes con mayor valor facturado' },
        { nombre: 'GESTIÓN DE NÓMINA', desc: 'Valor total y distribución por departamento' },
        { nombre: 'TENDENCIA MENSUAL', desc: 'Comparación de pedidos entre años' }
    ];
    
    metricas.forEach(metrica => {
        if (y > 270) {
            doc.addPage();
            y = 30;
        }
        
        doc.setFont(undefined, 'bold');
        doc.setTextColor(78, 115, 223);
        doc.text(metrica.nombre, 25, y);
        
        doc.setFont(undefined, 'normal');
        doc.setTextColor(100, 100, 100);
        doc.text(metrica.desc, 25, y + 5);
        
        y += 12;
    });
}

/**
 * Genera la página de estadísticas detalladas del PDF
 * 
 * @param {Object} doc - Documento jsPDF
 */
function generarEstadisticasDetalladasPDF(doc) {
    doc.addPage();
    let y = 30;
    
    doc.setFontSize(18);
    doc.setTextColor(78, 115, 223);
    doc.text('ESTADÍSTICAS DETALLADAS', 20, y);
    y += 20;
    
    doc.setFontSize(10);
    doc.setTextColor(60, 60, 60);
    
    const estadisticas = [
        `Total de componentes del dashboard: ${document.querySelectorAll('.card, canvas, table').length}`,
        `Tarjetas informativas: ${document.querySelectorAll('.card').length}`,
        `Gráficos interactivos: ${document.querySelectorAll('canvas').length}`,
        `Tablas de datos: ${document.querySelectorAll('table').length}`,
        `Métricas en tiempo real: ${document.querySelectorAll('[id*="MasVendido"], [id*="Nomina"], [id*="Lugar"]').length}`,
        `Secciones del dashboard: ${document.querySelectorAll('.row').length}`,
        `Elementos de navegación: ${document.querySelectorAll('.nav-item').length}`
    ];
    
    estadisticas.forEach(stat => {
        doc.text('• ' + stat, 25, y);
        y += 7;
    });
    
    y += 15;
    
    doc.setFontSize(14);
    doc.setTextColor(78, 115, 223);
    doc.text('INFORMACIÓN TÉCNICA', 20, y);
    y += 15;
    
    doc.setFontSize(9);
    doc.setTextColor(100, 100, 100);
    
    const infoTecnica = [
        `Navegador: ${navigator.userAgent.split(' ')[0]}`,
        `Resolución: ${screen.width}x${screen.height}`,
        `Timestamp: ${new Date().toISOString()}`,
        `User Agent: ${navigator.userAgent.substring(0, 50)}...`
    ];
    
    infoTecnica.forEach(info => {
        doc.text('› ' + info, 25, y);
        y += 6;
    });
}

/**
 * Agrega pie de página a todas las páginas del PDF
 * 
 * @param {Object} doc - Documento jsPDF
 */
function agregarPieDePaginaPDF(doc) {
    const totalPages = doc.getNumberOfPages();
    for (let i = 1; i <= totalPages; i++) {
        doc.setPage(i);
        
        doc.setDrawColor(200, 200, 200);
        doc.line(20, 280, 190, 280);
        
        doc.setFontSize(8);
        doc.setTextColor(150, 150, 150);
        doc.text('Sistema de Pedidos - Reporte generado automáticamente', 20, 285);
        doc.text(`Página ${i} de ${totalPages}`, 190, 285, { align: 'right' });
        
        if (i === 1) {
            doc.setFontSize(40);
            doc.setTextColor(240, 240, 240);
            doc.text('PEDIDOS', 105, 150, { align: 'center' });
        }
    }
}

// ============================================================================
// FUNCIONALIDAD DE NOTIFICACIONES
// ============================================================================

/**
 * Muestra una notificación de éxito
 * 
 * @param {string} mensaje - Mensaje a mostrar
 */
function mostrarNotificacionExito(mensaje) {
    const toast = document.createElement('div');
    toast.className = 'alert alert-success alert-dismissible fade show';
    toast.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        z-index: 9999;
        min-width: 400px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    `;
    
    toast.innerHTML = `
        <div class="d-flex align-items-center">
            <i class="fas fa-check-circle fa-lg text-success me-3"></i>
            <div>
                <strong class="d-block">Reporte Generado</strong>
                <small>${mensaje}</small>
            </div>
        </div>
        <button type="button" class="close" data-dismiss="alert">
            <span>&times;</span>
        </button>
    `;
    
    document.body.appendChild(toast);
    
    setTimeout(() => {
        if (toast.parentNode) {
            $(toast).alert('close');
        }
    }, 5000);
}

/**
 * Muestra una notificación de error
 * 
 * @param {string} mensaje - Mensaje de error a mostrar
 */
function mostrarNotificacionError(mensaje) {
    const toast = document.createElement('div');
    toast.className = 'alert alert-danger alert-dismissible fade show';
    toast.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        z-index: 9999;
        min-width: 400px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    `;
    
    toast.innerHTML = `
        <div class="d-flex align-items-center">
            <i class="fas fa-exclamation-triangle fa-lg text-danger me-3"></i>
            <div>
                <strong class="d-block">Error en Reporte</strong>
                <small>${mensaje}</small>
            </div>
        </div>
        <button type="button" class="close" data-dismiss="alert">
            <span>&times;</span>
        </button>
    `;
    
    document.body.appendChild(toast);
    
    setTimeout(() => {
        if (toast.parentNode) {
            $(toast).alert('close');
        }
    }, 5000);
}

// ============================================================================
// FUNCIONALIDAD DE BÚSQUEDA
// ============================================================================

/**
 * Inicializa la funcionalidad de búsqueda en el navbar
 */
function inicializarBusqueda() {
    const searchInput = document.querySelector('.navbar-search input');
    const searchButton = document.querySelector('.navbar-search button');
    
    if (!searchInput || !searchButton) {
        console.log('Elementos de búsqueda no encontrados');
        return;
    }

    console.log('Inicializando funcionalidad de búsqueda...');

    searchButton.addEventListener('click', function() {
        realizarBusqueda(searchInput.value);
    });

    searchInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            realizarBusqueda(searchInput.value);
        }
    });

    searchInput.addEventListener('input', function() {
        if (this.value.length >= 3) {
            realizarBusquedaEnTiempoReal(this.value);
        }
    });

    searchInput.addEventListener('focus', function() {
        mostrarSugerencias();
    });
}

/**
 * Realiza una búsqueda con el término proporcionado
 * 
 * @param {string} termino - Término de búsqueda
 */
function realizarBusqueda(termino) {
    if (!termino.trim()) {
        mostrarResultadosBusqueda('Por favor, ingresa un término de búsqueda');
        return;
    }

    console.log(`Buscando: "${termino}"`);
    
    const searchButton = document.querySelector('.navbar-search button');
    const originalHtml = searchButton.innerHTML;
    searchButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
    
    setTimeout(() => {
        const resultados = buscarEnDashboard(termino);
        mostrarResultadosBusqueda(resultados);
        searchButton.innerHTML = originalHtml;
    }, 1000);
}

/**
 * Realiza búsqueda en tiempo real
 * 
 * @param {string} termino - Término de búsqueda
 */
function realizarBusquedaEnTiempoReal(termino) {
    console.log(`Búsqueda en tiempo real: "${termino}"`);
}

/**
 * Busca el término en el dashboard
 * 
 * @param {string} termino - Término a buscar
 * @returns {Object} Resultados de la búsqueda
 */
function buscarEnDashboard(termino) {
    const terminoLower = termino.toLowerCase();
    const resultados = [];
    
    const titulos = document.querySelectorAll('.card-header h6, .card-header .font-weight-bold');
    titulos.forEach(titulo => {
        if (titulo.textContent.toLowerCase().includes(terminoLower)) {
            resultados.push({
                tipo: 'Métrica',
                titulo: titulo.textContent.trim(),
                elemento: titulo.closest('.card')
            });
        }
    });
    
    const textos = document.querySelectorAll('.card-body');
    textos.forEach(texto => {
        if (texto.textContent.toLowerCase().includes(terminoLower)) {
            const card = texto.closest('.card');
            const titulo = card.querySelector('.card-header h6')?.textContent || 'Sin título';
            resultados.push({
                tipo: 'Contenido',
                titulo: titulo.trim(),
                elemento: card
            });
        }
    });
    
    const tablas = document.querySelectorAll('table');
    tablas.forEach(tabla => {
        if (tabla.textContent.toLowerCase().includes(terminoLower)) {
            const titulo = tabla.closest('.card')?.querySelector('.card-header h6')?.textContent || 'Tabla';
            resultados.push({
                tipo: 'Tabla',
                titulo: titulo.trim(),
                elemento: tabla.closest('.card')
            });
        }
    });
    
    return {
        termino: termino,
        cantidad: resultados.length,
        resultados: resultados.slice(0, 10)
    };
}

/**
 * Muestra los resultados de búsqueda
 * 
 * @param {Object|string} data - Datos de resultados o mensaje de error
 */
function mostrarResultadosBusqueda(data) {
    const resultadosAnteriores = document.getElementById('resultados-busqueda');
    if (resultadosAnteriores) {
        resultadosAnteriores.remove();
    }
    
    const resultadosDiv = document.createElement('div');
    resultadosDiv.id = 'resultados-busqueda';
    resultadosDiv.className = 'card shadow-lg';
    resultadosDiv.style.cssText = `
        position: absolute;
        top: 60px;
        left: 50%;
        transform: translateX(-50%);
        width: 90%;
        max-width: 600px;
        max-height: 400px;
        overflow-y: auto;
        z-index: 9999;
        display: block;
    `;
    
    let contenidoHTML = `
        <div class="card-header py-3">
            <div class="d-flex justify-content-between align-items-center">
                <h6 class="m-0 font-weight-bold text-primary">
                    <i class="fas fa-search me-2"></i>Resultados de búsqueda
                </h6>
                <button type="button" class="close" onclick="cerrarResultadosBusqueda()">
                    <span>&times;</span>
                </button>
            </div>
        </div>
        <div class="card-body">
    `;
    
    if (typeof data === 'string') {
        contenidoHTML += `<p class="text-muted text-center">${data}</p>`;
    } else if (data.cantidad === 0) {
        contenidoHTML += `
            <div class="text-center py-4">
                <i class="fas fa-search fa-2x text-muted mb-3"></i>
                <p class="text-muted">No se encontraron resultados para "<strong>${data.termino}</strong>"</p>
                <small class="text-info">Intenta con otros términos como: pedidos, empleados, nómina, productos</small>
            </div>
        `;
    } else {
        contenidoHTML += `
            <p class="text-muted mb-3">Se encontraron <strong>${data.cantidad}</strong> resultados para "<strong>${data.termino}</strong>"</p>
            <div class="list-group">
        `;
        
        data.resultados.forEach((resultado, index) => {
            contenidoHTML += `
                <a href="#" class="list-group-item list-group-item-action" onclick="navegarAElemento(this)" data-element-id="${index}">
                    <div class="d-flex w-100 justify-content-between">
                        <h6 class="mb-1">
                            <span class="badge badge-${getBadgeColor(resultado.tipo)} me-2">${resultado.tipo}</span>
                            ${resultado.titulo}
                        </h6>
                    </div>
                    <p class="mb-1 text-muted">Haz clic para ir a esta sección</p>
                </a>
            `;
        });
        
        contenidoHTML += `</div>`;
    }
    
    contenidoHTML += `</div>`;
    resultadosDiv.innerHTML = contenidoHTML;
    
    document.body.appendChild(resultadosDiv);
    
    window.busquedaActual = data;
}

/**
 * Obtiene el color de badge según el tipo
 * 
 * @param {string} tipo - Tipo de resultado
 * @returns {string} Clase de color
 */
function getBadgeColor(tipo) {
    const colores = {
        'Métrica': 'primary',
        'Contenido': 'info',
        'Tabla': 'success',
        'Gráfico': 'warning'
    };
    return colores[tipo] || 'secondary';
}

/**
 * Navega al elemento seleccionado en los resultados
 * 
 * @param {HTMLElement} elemento - Elemento clickeado
 */
function navegarAElemento(elemento) {
    const index = elemento.getAttribute('data-element-id');
    const resultado = window.busquedaActual?.resultados[index];
    
    if (resultado && resultado.elemento) {
        cerrarResultadosBusqueda();
        
        resultado.elemento.scrollIntoView({ 
            behavior: 'smooth',
            block: 'center'
        });
        
        resultado.elemento.style.transition = 'all 0.3s ease';
        resultado.elemento.style.boxShadow = '0 0 0 3px rgba(78, 115, 223, 0.3)';
        
        setTimeout(() => {
            resultado.elemento.style.boxShadow = '';
        }, 2000);
    }
}

/**
 * Cierra el panel de resultados de búsqueda
 */
function cerrarResultadosBusqueda() {
    const resultados = document.getElementById('resultados-busqueda');
    if (resultados) {
        resultados.remove();
    }
}

/**
 * Muestra sugerencias de búsqueda
 */
function mostrarSugerencias() {
    const sugerencias = [
        'pedidos',
        'empleados',
        'productos',
        'nómina',
        'clientes',
        'ventas',
        'gráficos',
        'tablas'
    ];
    
    console.log('Sugerencias de búsqueda:', sugerencias);
}

// Cerrar resultados al hacer clic fuera
document.addEventListener('click', function(e) {
    const resultados = document.getElementById('resultados-busqueda');
    const searchInput = document.querySelector('.navbar-search input');
    
    if (resultados && 
        !resultados.contains(e.target) && 
        !searchInput.contains(e.target)) {
        cerrarResultadosBusqueda();
    }
});

// ============================================================================
// ESTILOS ADICIONALES
// ============================================================================

const style = document.createElement('style');
style.textContent = `
    .chart-area, .chart-pie {
        position: relative;
        width: 100%;
        overflow: hidden;
    }
    
    canvas {
        display: block;
        max-width: 100%;
        height: auto;
    }
    
    .card-body {
        position: relative;
        z-index: 1;
    }
    
    .progress {
        height: 20px;
        margin-top: 5px;
    }
    
    .progress-bar {
        transition: width 0.6s ease;
    }
`;
document.head.appendChild(style);

// ============================================================================
// INICIALIZACIÓN FINAL
// ============================================================================

window.addEventListener('load', function() {
    setTimeout(() => {
        const charts = document.querySelectorAll('canvas');
        charts.forEach((canvas, index) => {
            canvas.style.position = 'relative';
            canvas.style.zIndex = (index + 1);
        });
        console.log(`${charts.length} gráficas inicializadas correctamente`);
    }, 3500);
    
    inicializarBusqueda();
});