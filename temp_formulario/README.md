# 🏢 TalentHub - Sistema de Registro de Profesionales

Sistema web para el registro y gestión de profesionales independientes y sus servicios.

---

## 📋 Descripción

TalentHub es una plataforma que permite a trabajadores independientes registrar sus servicios profesionales con tarifas individuales, disponibilidad y documentación. Los administradores pueden visualizar y gestionar todos los registros desde un panel centralizado.

---

## ✨ Características Principales

- ✅ **Registro de Profesionales** - Formulario completo con validaciones
- ✅ **Múltiples Servicios** - Cada profesional puede registrar hasta 10 servicios
- ✅ **Tarifas Individuales** - Cada servicio tiene su propia tarifa por hora
- ✅ **15 Categorías** - Construcción, Electricidad, Plomería, Carpintería, etc.
- ✅ **Sistema de Ayudantes** - Registro de costos de ayudantes
- ✅ **Validaciones Exhaustivas** - 12 validaciones pre-envío con mensajes claros
- ✅ **Panel de Administración** - Visualización y gestión de registros
- ✅ **Búsqueda y Filtros Avanzados** - Buscar por nombre, documento, ciudad, categoría y rango de tarifas
- ✅ **Exportar a Excel** - Descarga de todos los registros en formato profesional
- ✅ **Estadísticas en Tiempo Real** - Dashboard con métricas clave
- ✅ **Validación de Duplicados** - Previene registros con documentos duplicados
- ✅ **Seguridad Mejorada** - Contraseñas con hash bcrypt y sesiones con timeout
- ✅ **Carga de Documentos** - Fotos de identificación, antecedentes, recomendaciones
- ✅ **Selector de Ciudades** - 32 ciudades colombianas con códigos DANE
- ✅ **Auditoría Completa** - Registro de quién y cuándo se registró

---

## 🛠️ Tecnologías

**Backend:**
- Python 3.x
- Flask 2.3.0
- MySQL 8.0+

**Frontend:**
- HTML5
- CSS3
- JavaScript ES6+
- Bootstrap 5.1.3

---

## 📦 Instalación

### 1. Clonar el repositorio
```bash
git clone <url-del-repositorio>
cd formulario_flask
```

### 2. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 3. Configurar la base de datos

**Crear la base de datos:**
```bash
mysql -u root -p < init_database_complete.sql
```

**Configurar credenciales en `app.py`:**
```python
connection = mysql.connector.connect(
    host="localhost",
    user="root",
    password="TU_PASSWORD",
    database="profiles_cv_db"
)
```

### 4. Ejecutar la aplicación
```bash
python app.py
```

La aplicación estará disponible en: `http://localhost:5000`

---

## 📊 Estructura de la Base de Datos

### Tablas Principales:

**1. personas** - Información personal de profesionales
- Documento, nombre, ciudad, código DANE
- Auditoría: registrado_por, fecha_registro

**2. servicios_persona** - Servicios ofrecidos (⭐ Tabla clave)
- Categoría, descripción, años de experiencia
- Tarifa por hora, ayudante, costo ayudante

**3. telefono_persona** - Teléfonos de contacto

**4. correo_persona** - Correos electrónicos (opcional)

**5. disponibilidad** - Horarios y días disponibles

**6. detalles_persona** - Documentos y archivos

**7. experiencia_persona** - Resumen de experiencia

**8. parametros_generales** - Catálogos del sistema

**9. detalle_parametro** - Valores de parámetros

**10. vista_profesionales** - Vista para consultas

---

## 🎯 Uso

### Para Profesionales:

1. Acceder a `http://localhost:5000`
2. Completar el formulario de registro:
   - Información personal
   - Contacto
   - Servicios y tarifas
   - Disponibilidad
   - Documentos
3. Aceptar términos y enviar

### Para Administradores:

1. Acceder a `http://localhost:5000/admin/login`
2. Ingresar contraseña: `admin123`
3. **Panel de Administración con:**
   - Dashboard con estadísticas en tiempo real
   - Búsqueda por nombre, documento o ciudad
   - Filtros por categoría de servicio
   - Filtros por rango de tarifas
   - Exportar todos los registros a Excel
   - Ver detalles completos de cada profesional
   - Eliminar registros
4. **Funcionalidades Avanzadas:**
   - Contador de resultados en tiempo real
   - Estadísticas: total profesionales, categorías activas, tarifa promedio, ciudades
   - Exportación profesional a Excel con formato
   - Sesión segura con timeout de 30 minutos

---

## 🎨 Características del Formulario

### Validaciones en Tiempo Real:
- ✅ Teléfono: solo números, 10 dígitos
- ✅ Documento: solo números, 6-15 dígitos
- ✅ Nombre: solo letras y espacios
- ✅ Correo: formato válido con @
- ✅ Validación de duplicados: verifica si el documento ya existe

### Validaciones Pre-Envío:
- ✅ 12 validaciones con mensajes descriptivos
- ✅ Ejemplos de formato correcto
- ✅ Scroll automático al campo con error
- ✅ Animación en campos inválidos

### Indicadores Visuales:
- 🟢 Verde: campo válido
- 🔴 Rojo: campo inválido
- 🔵 Azul: campo enfocado

## 🔍 Panel de Administración Avanzado

### Búsqueda y Filtros:
- 🔎 Búsqueda en tiempo real por nombre, documento o ciudad
- 🏷️ Filtro por categoría de servicio (15 categorías)
- 💰 Filtro por rango de tarifas (mínimo y máximo)
- 📊 Contador de resultados dinámico
- 🧹 Botón para limpiar todos los filtros

### Estadísticas:
- 👥 Total de profesionales registrados
- 🏷️ Número de categorías activas
- 💵 Tarifa promedio del sistema
- 🌎 Número de ciudades representadas

### Exportación:
- 📥 Exportar a Excel con un clic
- 📋 Formato profesional con encabezados
- 📊 Incluye todos los datos: servicios, tarifas, ayudantes
- 📅 Nombre de archivo con fecha y hora

---

## 📁 Estructura del Proyecto

```
formulario_flask/
├── app.py                          # Aplicación Flask principal
├── init_database_complete.sql      # Script de base de datos
├── requirements.txt                # Dependencias Python
├── README.md                       # Este archivo
│
├── templates/
│   ├── formulario_actualizado.html # Formulario de registro
│   ├── registros.html              # Panel de administración
│   └── admin_login.html            # Login de admin
│
└── static/
    └── uploads/                    # Archivos subidos
```

---

## 🔐 Seguridad

- ✅ Validación en cliente (JavaScript)
- ✅ Validación en servidor (Python)
- ✅ Prepared statements (prevención SQL injection)
- ✅ Nombres de archivo seguros
- ✅ Límite de tamaño de archivos (16MB)
- ✅ Protección de rutas administrativas
- ✅ **Contraseñas con hash bcrypt** (seguridad mejorada)
- ✅ **Sesiones con timeout** (30 minutos de inactividad)
- ✅ **Validación de duplicados** (previene documentos repetidos)

---

## 📈 Estadísticas

- **Tablas:** 10 tablas normalizadas (3NF)
- **Índices:** 12 índices para optimización
- **Validaciones:** 12 validaciones exhaustivas + validación de duplicados
- **Categorías:** 15 categorías de servicios
- **Ciudades:** 32 ciudades colombianas
- **Líneas de código:** 1,200+ (Python) + 1,173 (HTML/JS)
- **Funcionalidades Admin:** Búsqueda, filtros, exportación, estadísticas
- **Seguridad:** Hash bcrypt + sesiones con timeout

---

## 🚀 Próximos Pasos

1. **API REST** - Para conectar con app móvil
2. **App Móvil** - Para clientes
3. **Sistema de Notificaciones** - Push notifications
4. **Sistema de Calificaciones** - Reseñas y ratings
5. **Chat en Tiempo Real** - Mensajería
6. **Pagos Integrados** - Procesamiento de pagos

---

## 📝 Notas Importantes

- **Contraseña Admin:** `admin123` (cambiar en producción)
- **Puerto:** 5000 (Flask)
- **Base de Datos:** profiles_cv_db
- **Tarifas:** Solo mano de obra (sin materiales)
- **Archivos:** Máximo 16MB por archivo

---

## 👥 Autor

Desarrollado para TalentHub

---

## 📄 Licencia

Este proyecto es privado y confidencial.

---

## 🆘 Soporte

Para preguntas o problemas, contactar al administrador del sistema.

