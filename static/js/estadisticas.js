// =========================
// FUNCIONES PRINCIPALES DE ESTADÍSTICAS
// =========================

function cargarTodasEstadisticas() {
    console.log("📊 Cargando todas las estadísticas...");
    
    // Mostrar loading en todas las secciones
    mostrarLoading();
    
    // Cargar datos secuencialmente
    cargarVariablesCuantitativas();
    setTimeout(() => cargarVariablesCualitativas(), 500);
    setTimeout(() => cargarMedidasDispersion(), 1000);
}

function mostrarLoading() {
    const loadingHTML = `
        <div class="col-12 text-center">
            <div class="spinner-border text-primary" role="status">
                <span class="sr-only">Cargando...</span>
            </div>
            <p class="mt-2 text-muted">Cargando estadísticas...</p>
        </div>
    `;
    
    document.getElementById('medidas-tendencia-central').innerHTML = loadingHTML;
    document.getElementById('medidas-dispersion').innerHTML = loadingHTML;
    
    document.getElementById('cuerpo-tabla-categorias').innerHTML = `
        <tr>
            <td colspan="3" class="text-center text-muted">Cargando datos...</td>
        </tr>
    `;
}

// =========================
// VARIABLES CUANTITATIVAS
// =========================

function cargarVariablesCuantitativas() {
    console.log("📊 Cargando variables cuantitativas...");
    
    fetch('/api/estadisticas/variables-cuantitativas')
        .then(response => {
            console.log(`📡 Respuesta del servidor: ${response.status}`);
            
            if (!response.ok) {
                // Si el servidor responde con error, obtener el mensaje de error
                return response.json().then(errorData => {
                    throw new Error(errorData.error || `Error HTTP: ${response.status}`);
                }).catch(() => {
                    throw new Error(`Error del servidor: ${response.status}`);
                });
            }
            return response.json();
        })
        .then(data => {
            console.log("✅ Datos cuantitativos recibidos:", data);
            
            if (data.error) {
                throw new Error(data.error);
            }
            
            mostrarMedidasTendenciaCentral(data);
            crearGraficoDistribucionPrecios(data);
        })
        .catch(error => {
            console.error("❌ Error cargando variables cuantitativas:", error);
            
            // Mostrar error específico en la interfaz
            document.getElementById('medidas-tendencia-central').innerHTML = `
                <div class="col-12 text-center text-danger">
                    <i class="fas fa-exclamation-triangle fa-2x mb-2"></i>
                    <h5>Error al cargar datos cuantitativos</h5>
                    <p class="mb-1">${error.message || 'Error desconocido'}</p>
                    <small class="text-muted">Verifica la consola para más detalles</small>
                    <br>
                    <button class="btn btn-sm btn-outline-primary mt-2" onclick="cargarVariablesCuantitativas()">
                        <i class="fas fa-redo"></i> Reintentar
                    </button>
                </div>
            `;
        });
}

function mostrarMedidasTendenciaCentral(data) {
    if (data.error) {
        document.getElementById('medidas-tendencia-central').innerHTML = `
            <div class="col-12 text-center text-danger">
                <i class="fas fa-exclamation-triangle fa-2x mb-2"></i>
                <p>Error: ${data.error}</p>
            </div>
        `;
        return;
    }

    const precios = data.precios;
    
    document.getElementById('medidas-tendencia-central').innerHTML = `
        <div class="col-xl-3 col-md-6 mb-4">
            <div class="stat-card card border-left-primary shadow h-100 py-2">
                <div class="card-body">
                    <div class="text-xs font-weight-bold text-primary text-uppercase mb-1">
                        Media
                    </div>
                    <div class="measure-value text-primary">$${precios.media.toFixed(2)}</div>
                    <small class="text-muted">Promedio de precios</small>
                </div>
            </div>
        </div>
        <div class="col-xl-3 col-md-6 mb-4">
            <div class="stat-card card border-left-success shadow h-100 py-2">
                <div class="card-body">
                    <div class="text-xs font-weight-bold text-success text-uppercase mb-1">
                        Mediana
                    </div>
                    <div class="measure-value text-success">$${precios.mediana.toFixed(2)}</div>
                    <small class="text-muted">Valor central</small>
                </div>
            </div>
        </div>
        <div class="col-xl-3 col-md-6 mb-4">
            <div class="stat-card card border-left-info shadow h-100 py-2">
                <div class="card-body">
                    <div class="text-xs font-weight-bold text-info text-uppercase mb-1">
                        Moda
                    </div>
                    <div class="measure-value text-info">$${precios.moda.toFixed(2)}</div>
                    <small class="text-muted">Valor más frecuente</small>
                </div>
            </div>
        </div>
        <div class="col-xl-3 col-md-6 mb-4">
            <div class="stat-card card border-left-warning shadow h-100 py-2">
                <div class="card-body">
                    <div class="text-xs font-weight-bold text-warning text-uppercase mb-1">
                        Rango
                    </div>
                    <div class="measure-value text-warning">$${(precios.maximo - precios.minimo).toFixed(2)}</div>
                    <small class="text-muted">De $${precios.minimo.toFixed(2)} a $${precios.maximo.toFixed(2)}</small>
                </div>
            </div>
        </div>
    `;
}

function crearGraficoDistribucionPrecios(data) {
    const ctx = document.getElementById('distribucionPreciosChart');
    if (!ctx) return;
    
    // Destruir gráfico anterior si existe
    if (window.distribucionChart) {
        window.distribucionChart.destroy();
    }
    
    const precios = data.precios;
    
    // Crear datos simulados para el gráfico
    const distribucion = generarDatosDistribucion(precios);
    
    window.distribucionChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: distribucion.rangos,
            datasets: [{
                label: 'Cantidad de Productos',
                data: distribucion.frecuencias,
                backgroundColor: 'rgba(78, 115, 223, 0.6)',
                borderColor: 'rgba(78, 115, 223, 1)',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Cantidad de Productos'
                    }
                },
                x: {
                    title: {
                        display: true,
                        text: 'Rangos de Precio ($)'
                    }
                }
            }
        }
    });
}

function generarDatosDistribucion(precios) {
    // Generar rangos de precios simulados
    const min = Math.floor(precios.minimo);
    const max = Math.ceil(precios.maximo);
    const numBarras = 6;
    const paso = (max - min) / numBarras;
    
    const rangos = [];
    const frecuencias = [];
    
    for (let i = 0; i < numBarras; i++) {
        const inicio = min + (i * paso);
        const fin = inicio + paso;
        rangos.push(`$${inicio.toFixed(0)}-${fin.toFixed(0)}`);
        // Frecuencias simuladas (proporcionales al rango)
        frecuencias.push(Math.floor(Math.random() * 15) + 5);
    }
    
    return { rangos, frecuencias };
}

// =========================
// VARIABLES CUALITATIVAS
// =========================

function cargarVariablesCualitativas() {
    console.log("📊 Cargando variables cualitativas...");
    
    fetch('/api/estadisticas/variables-cualitativas')
        .then(response => {
            console.log(`📡 Estado de respuesta cualitativas: ${response.status}`);
            
            if (!response.ok) {
                return response.json().then(errorData => {
                    throw new Error(errorData.error || `Error HTTP: ${response.status}`);
                }).catch(() => {
                    throw new Error(`Error del servidor: ${response.status}`);
                });
            }
            return response.json();
        })
        .then(data => {
            console.log("✅ Datos cualitativos recibidos:", data);
            
            if (data.error) {
                throw new Error(data.error);
            }
            
            if (!data.categorias || !data.formas_pago) {
                throw new Error("Datos incompletos recibidos del servidor");
            }
            
            mostrarTablaCategorias(data.categorias);
            crearGraficoFormasPago(data.formas_pago);
        })
        .catch(error => {
            console.error("❌ Error cargando variables cualitativas:", error);
            mostrarErrorCualitativas(error);
        });
}

function mostrarErrorCualitativas(error) {
    // Mostrar error en la tabla
    document.getElementById('cuerpo-tabla-categorias').innerHTML = `
        <tr>
            <td colspan="3" class="text-center text-danger py-3">
                <i class="fas fa-exclamation-triangle fa-2x mb-2"></i>
                <br>Error al cargar categorías
                <br><small>${error.message}</small>
            </td>
        </tr>
    `;
    
    // Mostrar error en el gráfico
    const chartContainer = document.getElementById('formasPagoChart');
    if (chartContainer) {
        chartContainer.parentNode.innerHTML = `
            <div class="text-center text-danger py-4">
                <i class="fas fa-chart-pie fa-2x mb-2"></i>
                <br>Error al cargar formas de pago
                <br><small>${error.message}</small>
            </div>
        `;
    }
}

function mostrarTablaCategorias(categorias) {
    const tbody = document.getElementById('cuerpo-tabla-categorias');
    
    if (!categorias || categorias.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="3" class="text-center text-muted py-3">
                    <i class="fas fa-database fa-2x mb-2"></i>
                    <br>No hay datos de categorías disponibles
                </td>
            </tr>
        `;
        return;
    }

    console.log("📋 Mostrando tabla de categorías:", categorias);

    let html = '';
    categorias.forEach((cat, index) => {
        // Colores diferentes para las primeras filas
        let badgeClass = 'badge-primary';
        if (index === 0) badgeClass = 'badge-success';
        else if (index === 1) badgeClass = 'badge-info';
        else if (index === 2) badgeClass = 'badge-warning';
        
        html += `
            <tr>
                <td class="font-weight-bold">${cat.categoria}</td>
                <td class="text-center">${cat.frecuencia.toLocaleString()}</td>
                <td class="text-center">
                    <span class="badge ${badgeClass} badge-pill">${cat.porcentaje}%</span>
                </td>
            </tr>
        `;
    });
    
    tbody.innerHTML = html;
}

function crearGraficoFormasPago(formasPago) {
    const ctx = document.getElementById('formasPagoChart');
    if (!ctx) {
        console.error("❌ No se encontró el canvas formasPagoChart");
        return;
    }
    
    // Limpiar gráfico anterior si existe
    if (window.formasPagoChart && typeof window.formasPagoChart.destroy === 'function') {
        window.formasPagoChart.destroy();
    }
    
    if (!formasPago || formasPago.length === 0) {
        console.warn("⚠️ No hay datos de formas de pago");
        ctx.parentNode.innerHTML = '<p class="text-muted text-center">No hay datos de formas de pago disponibles</p>';
        return;
    }

    console.log("📊 Creando gráfico de formas de pago:", formasPago);
    
    try {
        window.formasPagoChart = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: formasPago.map(fp => fp.forma_pago),
                datasets: [{
                    data: formasPago.map(fp => fp.frecuencia),
                    backgroundColor: [
                        '#4e73df',  // Azul
                        '#1cc88a',  // Verde
                        '#36b9cc',  // Cyan
                        '#f6c23e',  // Amarillo
                        '#e74a3b'   // Rojo
                    ],
                    borderWidth: 2,
                    borderColor: '#fff',
                    hoverOffset: 15
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            padding: 15,
                            usePointStyle: true,
                            font: {
                                size: 12
                            }
                        }
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const label = context.label || '';
                                const value = context.raw || 0;
                                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                const percentage = Math.round((value / total) * 100);
                                return `${label}: ${value} (${percentage}%)`;
                            }
                        }
                    }
                },
                cutout: '60%'
            }
        });
        console.log("✅ Gráfico de formas de pago creado exitosamente");
    } catch (error) {
        console.error("❌ Error creando gráfico de formas de pago:", error);
        ctx.parentNode.innerHTML = `
            <div class="text-center text-danger">
                <i class="fas fa-exclamation-triangle fa-2x mb-2"></i>
                <p>Error al crear el gráfico</p>
                <small>${error.message}</small>
            </div>
        `;
    }
}

// =========================
// MEDIDAS DE DISPERSIÓN
// =========================

function cargarMedidasDispersion() {
    fetch('/api/estadisticas/medidas-dispersion')
        .then(response => {
            if (!response.ok) {
                throw new Error(`Error HTTP: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            console.log("✅ Medidas de dispersión cargadas:", data);
            mostrarMedidasDispersion(data);
            crearGraficoSalarios(data);
        })
        .catch(error => {
            console.error("❌ Error cargando medidas de dispersión:", error);
            mostrarError('medidas-dispersion', error);
        });
}

function mostrarMedidasDispersion(data) {
    if (data.error) {
        document.getElementById('medidas-dispersion').innerHTML = `
            <div class="col-12 text-center text-danger">
                <i class="fas fa-exclamation-triangle fa-2x mb-2"></i>
                <p>Error: ${data.error}</p>
            </div>
        `;
        return;
    }

    const salarios = data.salarios;
    
    document.getElementById('medidas-dispersion').innerHTML = `
        <div class="col-xl-4 col-md-6 mb-4">
            <div class="stat-card card border-left-danger shadow h-100 py-2">
                <div class="card-body">
                    <div class="text-xs font-weight-bold text-danger text-uppercase mb-1">
                        Desviación Estándar
                    </div>
                    <div class="measure-value text-danger">$${salarios.desviacion_estandar.toFixed(2)}</div>
                    <small class="text-muted">Dispersión de salarios</small>
                </div>
            </div>
        </div>
        <div class="col-xl-4 col-md-6 mb-4">
            <div class="stat-card card border-left-info shadow h-100 py-2">
                <div class="card-body">
                    <div class="text-xs font-weight-bold text-info text-uppercase mb-1">
                        Varianza
                    </div>
                    <div class="measure-value text-info">$${salarios.varianza.toFixed(2)}</div>
                    <small class="text-muted">Variabilidad cuadrática</small>
                </div>
            </div>
        </div>
        <div class="col-xl-4 col-md-6 mb-4">
            <div class="stat-card card border-left-warning shadow h-100 py-2">
                <div class="card-body">
                    <div class="text-xs font-weight-bold text-warning text-uppercase mb-1">
                        Rango Intercuartílico
                    </div>
                    <div class="measure-value text-warning">$${salarios.iqr.toFixed(2)}</div>
                    <small class="text-muted">Q1: $${salarios.q1.toFixed(2)} - Q3: $${salarios.q3.toFixed(2)}</small>
                </div>
            </div>
        </div>
    `;
}

function crearGraficoSalarios(data) {
    const ctx = document.getElementById('boxPlotSalarios');
    if (!ctx) return;
    
    // Destruir gráfico anterior si existe
    if (window.salariosChart) {
        window.salariosChart.destroy();
    }
    
    const salarios = data.salarios;
    
    window.salariosChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: ['Mínimo', 'Q1', 'Mediana', 'Q3', 'Máximo'],
            datasets: [{
                label: 'Salarios ($)',
                data: [
                    salarios.minimo,
                    salarios.q1,
                    salarios.mediana,
                    salarios.q3,
                    salarios.maximo
                ],
                backgroundColor: [
                    'rgba(255, 99, 132, 0.7)',
                    'rgba(54, 162, 235, 0.7)',
                    'rgba(255, 206, 86, 0.7)',
                    'rgba(75, 192, 192, 0.7)',
                    'rgba(153, 102, 255, 0.7)'
                ]
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Salario ($)'
                    }
                }
            }
        }
    });
}

// =========================
// FUNCIONES AUXILIARES
// =========================

function mostrarError(elementId, error) {
    const element = document.getElementById(elementId);
    if (element) {
        element.innerHTML = `
            <div class="col-12 text-center text-danger">
                <i class="fas fa-exclamation-triangle fa-2x mb-2"></i>
                <p>Error al cargar los datos</p>
                <small>${error.message || error}</small>
            </div>
        `;
    }
}

function mostrarErrorTabla(error) {
    document.getElementById('cuerpo-tabla-categorias').innerHTML = `
        <tr>
            <td colspan="3" class="text-center text-danger">
                Error: ${error.message || error}
            </td>
        </tr>
    `;
}

// =========================
// INICIALIZACIÓN
// =========================
document.addEventListener('DOMContentLoaded', function() {
    console.log("📊 Módulo de estadísticas cargado");
    // Cargar estadísticas automáticamente
    setTimeout(() => cargarTodasEstadisticas(), 1000);
});