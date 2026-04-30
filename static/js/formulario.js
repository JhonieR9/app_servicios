// Script limpio para formulario de trabajadores
console.log('Formulario JS cargado correctamente');

// Funcion para actualizar codigo DANE y departamento
function actualizarDane() {
    const select = document.getElementById('ciudad_select');
    const daneInput = document.getElementById('codigo_dane');
    const deptoInput = document.getElementById('departamento_field');
    
    if (!select || !daneInput) return;
    
    const selectedOption = select.options[select.selectedIndex];
    const daneCode = selectedOption.getAttribute('data-dane');
    
    // Extraer departamento del texto: "CIUDAD - DEPARTAMENTO"
    const texto = selectedOption.text || '';
    const partes = texto.split(' - ');
    const depto = partes.length > 1 ? partes[partes.length - 1].trim() : '';

    if (daneCode && daneCode !== '') {
        daneInput.value = daneCode;
        if (deptoInput) deptoInput.value = depto;
    } else {
        daneInput.value = '';
        if (deptoInput) deptoInput.value = '';
    }
}

// Escuchar el evento change directamente en el select
document.addEventListener('DOMContentLoaded', function() {
    const ciudadSelect = document.getElementById('ciudad_select');
    if (ciudadSelect) {
        ciudadSelect.addEventListener('change', actualizarDane);
    }
});

// Contador de servicios
let contadorHabilidades = 1;

// Mostrar/ocultar boton agregar servicios
document.addEventListener('DOMContentLoaded', function() {
    const tipoHab = document.getElementById('tipoHabilidades');
    if (tipoHab) {
        tipoHab.addEventListener('change', function() {
            const texto = this.options[this.selectedIndex].text.toLowerCase();
            const btnContainer = document.getElementById('btnAgregarContainer');
            
            if (texto.includes('varias') || texto.includes('varios')) {
                btnContainer.style.display = 'block';
            } else {
                btnContainer.style.display = 'none';
            }
        });
    }
});

// Funcion para agregar servicio
function agregarHabilidad() {
    if (contadorHabilidades >= 10) {
        alert('Maximo 10 servicios');
        return;
    }
    
    contadorHabilidades++;
    const container = document.getElementById('habilidadesContainer');
    const div = document.createElement('div');
    div.className = 'habilidad-box';
    div.innerHTML = `
        <div class="d-flex justify-content-between align-items-center mb-3">
            <h5 class="mb-0"><i class="bi bi-tools"></i> Servicio ${contadorHabilidades}</h5>
            <button type="button" class="btn btn-sm btn-danger" onclick="this.closest('.habilidad-box').remove(); contadorHabilidades--;">
                <i class="bi bi-trash"></i> Eliminar
            </button>
        </div>
        <div class="row g-3">
            <div class="col-md-4">
                <label class="form-label required-label">Categoria del Servicio</label>
                <select class="form-control" name="servicio_categoria[]" required>
                    <option value="">Seleccionar categoria...</option>
                    <option value="Construccion">Construccion</option>
                    <option value="Electricidad">Electricidad</option>
                    <option value="Plomeria">Plomeria</option>
                    <option value="Carpinteria">Carpinteria</option>
                    <option value="Pintura">Pintura</option>
                    <option value="Jardineria">Jardineria</option>
                    <option value="Limpieza">Limpieza</option>
                    <option value="Mecanica">Mecanica</option>
                    <option value="Tecnologia">Tecnologia</option>
                    <option value="Educacion">Educacion</option>
                    <option value="Salud">Salud</option>
                    <option value="Belleza">Belleza</option>
                    <option value="Gastronomia">Gastronomia</option>
                    <option value="Transporte">Transporte</option>
                    <option value="Otro">Otro</option>
                </select>
            </div>
            <div class="col-md-8">
                <label class="form-label required-label">Descripcion del Servicio</label>
                <textarea class="form-control" name="habilidad_desc[]" rows="2" placeholder="Describa el servicio que ofrece" required></textarea>
            </div>
            <div class="col-md-6">
                <label class="form-label required-label">Anos de Experiencia</label>
                <input type="number" class="form-control" name="habilidad_exp[]" min="0" max="50" step="0.5" value="0" required>
            </div>
            <div class="col-md-6">
                <label class="form-label required-label">Tarifa/Hora (COP)</label>
                <input type="number" class="form-control" name="habilidad_valor[]" min="5000" max="1000000" step="1000" value="0" placeholder="Ej: 50000" required>
            </div>
            <div class="col-md-6">
                <label class="form-label">¿Trabaja con ayudante?</label>
                <select class="form-control ayudante-select" name="tiene_ayudante[]" onchange="toggleCostoAyudante(this)">
                    <option value="0">No</option>
                    <option value="1">Sí</option>
                </select>
            </div>
            <div class="col-md-6 costo-ayudante-container" style="display: none;">
                <label class="form-label">Costo Ayudante/Hora (COP)</label>
                <input type="number" class="form-control" name="costo_ayudante[]" min="0" max="500000" step="1000" value="" placeholder="Ej: 25000">
            </div>
        </div>
    `;
    
    container.appendChild(div);
}

// Funcion para toggle costo ayudante
function toggleCostoAyudante(select) {
    const container = select.closest('.row').querySelector('.costo-ayudante-container');
    if (select.value === '1') {
        container.style.display = 'block';
    } else {
        container.style.display = 'none';
    }
}
