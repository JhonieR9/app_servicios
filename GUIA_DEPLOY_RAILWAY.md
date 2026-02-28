# 🚀 Guía de Despliegue en Railway.app

## ✅ Ventajas de Railway

- ✅ **No necesitas PC encendida** - Servidor en la nube 24/7
- ✅ **Base de datos incluida** - MySQL en la nube
- ✅ **HTTPS automático** - Dominio seguro gratis
- ✅ **Fácil de usar** - Deploy en 15 minutos
- ✅ **Económico** - ~$5 USD/mes
- ✅ **Escalable** - Crece con tu negocio

---

## 💰 Costos

### Plan Hobby (Recomendado):
- **$5 USD/mes** de crédito gratis
- Después: **~$5-10 USD/mes** según uso
- Incluye: Servidor + Base de datos MySQL

### Qué incluye:
- Servidor FastAPI 24/7
- Base de datos MySQL
- 500 GB de transferencia
- HTTPS automático
- Dominio personalizado (opcional)

---

## 📋 Requisitos Previos

1. **Cuenta de GitHub** (gratis)
   - Si no tienes: https://github.com/signup

2. **Cuenta de Railway** (gratis)
   - Regístrate en: https://railway.app
   - Usa tu cuenta de GitHub para registrarte

3. **Tarjeta de crédito/débito**
   - Para verificación (no se cobra hasta superar $5)

---

## 🚀 Pasos de Despliegue

### Paso 1: Preparar el Proyecto

Ya está todo listo, solo necesitamos crear algunos archivos:

---

## 📁 Archivos que Voy a Crear

1. **`requirements.txt`** - Dependencias de Python
2. **`Procfile`** - Comando para iniciar el servidor
3. **`railway.json`** - Configuración de Railway
4. **`.gitignore`** - Archivos a ignorar
5. **`runtime.txt`** - Versión de Python

---

## 🔧 Configuración de Base de Datos

Railway incluye MySQL. Solo necesitamos:

1. **Crear base de datos en Railway**
2. **Ejecutar scripts SQL** para crear tablas
3. **Actualizar credenciales** en el código

---

## 📝 Pasos Detallados

### 1. Crear Repositorio en GitHub

```bash
# En tu carpeta del proyecto
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/TU-USUARIO/talenthub.git
git push -u origin main
```

### 2. Conectar Railway con GitHub

1. Ve a: https://railway.app
2. Click en "New Project"
3. Selecciona "Deploy from GitHub repo"
4. Autoriza Railway a acceder a GitHub
5. Selecciona tu repositorio

### 3. Agregar Base de Datos MySQL

1. En tu proyecto de Railway
2. Click en "New" → "Database" → "Add MySQL"
3. Railway creará la base de datos automáticamente
4. Copia las credenciales (las necesitarás)

### 4. Configurar Variables de Entorno

En Railway, ve a tu servicio → Variables:

```
DB_HOST=mysql.railway.internal
DB_USER=root
DB_PASSWORD=[generado por Railway]
DB_NAME=railway
DB_PORT=3306
```

### 5. Deploy Automático

Railway detectará tu código y lo desplegará automáticamente.

---

## 🌐 URL de tu Aplicación

Railway te dará una URL como:
```
https://talenthub-production.up.railway.app
```

Tu formulario estará en:
```
https://talenthub-production.up.railway.app/trabajador/registro
```

---

## 📊 Después del Deploy

### 1. Crear Tablas en la Base de Datos

Necesitarás ejecutar los scripts SQL en la base de datos de Railway.

**Opción A: Desde Railway CLI**
```bash
railway login
railway link
railway run python setup_database_cloud.py
```

**Opción B: Desde MySQL Workbench**
1. Conectar con las credenciales de Railway
2. Ejecutar scripts SQL manualmente

### 2. Verificar que Funciona

1. Abre tu URL de Railway
2. Ve al formulario de registro
3. Prueba registrar un trabajador
4. Verifica en el panel de admin

---

## 🔄 Actualizar el Código

Cada vez que hagas cambios:

```bash
git add .
git commit -m "Descripción del cambio"
git push
```

Railway detectará los cambios y desplegará automáticamente.

---

## 📱 Compartir el Formulario

**URL Permanente:**
```
https://tu-app.up.railway.app/trabajador/registro
```

Esta URL **NUNCA cambia**, puedes compartirla con confianza.

---

## 💡 Ventajas vs Ngrok

| Característica | Ngrok | Railway |
|---------------|-------|---------|
| Costo | Gratis | ~$5/mes |
| PC encendida | ✅ Necesaria | ❌ No necesaria |
| URL permanente | ❌ Cambia | ✅ Permanente |
| Base de datos | Local | En la nube |
| Confiabilidad | Media | Alta |
| Escalabilidad | Limitada | Alta |

---

## 🎯 Recomendación

**Usa Railway si:**
- ✅ Quieres lanzamiento profesional
- ✅ No quieres dejar PC encendida
- ✅ Esperas más de 100 registros
- ✅ Puedes invertir $5-10/mes
- ✅ Quieres URL permanente

**Usa Ngrok si:**
- ✅ Solo quieres probar (1-2 semanas)
- ✅ No quieres gastar dinero aún
- ✅ Puedes dejar PC encendida
- ✅ Son pocos registros iniciales

---

## 🆘 Soporte

**Railway:**
- Documentación: https://docs.railway.app
- Discord: https://discord.gg/railway
- Email: team@railway.app

**Alternativas a Railway:**
1. **Render.com** - Similar, ~$7/mes
2. **Fly.io** - Más técnico, ~$5/mes
3. **Heroku** - Más caro, ~$7/mes

---

## ✅ Checklist de Deploy

- [ ] Cuenta de GitHub creada
- [ ] Cuenta de Railway creada
- [ ] Repositorio creado en GitHub
- [ ] Código subido a GitHub
- [ ] Proyecto creado en Railway
- [ ] Base de datos MySQL agregada
- [ ] Variables de entorno configuradas
- [ ] Deploy exitoso
- [ ] Tablas creadas en la base de datos
- [ ] Formulario probado
- [ ] Panel de admin accesible
- [ ] URL compartida

---

¿Quieres que prepare todos los archivos necesarios para Railway?
