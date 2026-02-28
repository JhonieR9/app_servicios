# 🚀 Deploy en Railway - Paso a Paso (15 minutos)

## ✅ Lo que Vas a Lograr

- ✅ Servidor en la nube 24/7 (sin necesidad de tu PC)
- ✅ Base de datos MySQL en la nube
- ✅ URL permanente con HTTPS
- ✅ Costo: ~$5 USD/mes

---

## 📋 Paso 1: Crear Cuenta en Railway (2 minutos)

1. Ve a: **https://railway.app**
2. Click en **"Login"**
3. Selecciona **"Login with GitHub"**
4. Si no tienes GitHub, créalo primero en: **https://github.com/signup**
5. Autoriza Railway a acceder a tu GitHub

✅ **Listo:** Ahora tienes cuenta en Railway

---

## 📦 Paso 2: Subir tu Código a GitHub (5 minutos)

### Opción A: Desde GitHub Desktop (Más Fácil)

1. Descarga **GitHub Desktop**: https://desktop.github.com
2. Instala y abre GitHub Desktop
3. Click en **"File" → "Add Local Repository"**
4. Selecciona tu carpeta: `C:\Users\Usuario\Desktop\app_servicios`
5. Click en **"Create Repository"**
6. Click en **"Publish Repository"**
7. Desmarca **"Keep this code private"** (o déjalo privado si prefieres)
8. Click en **"Publish Repository"**

### Opción B: Desde la Terminal (Más Rápido)

```bash
# En tu carpeta del proyecto
git init
git add .
git commit -m "Deploy inicial"
git branch -M main

# Crea un repositorio en GitHub primero, luego:
git remote add origin https://github.com/TU-USUARIO/talenthub.git
git push -u origin main
```

✅ **Listo:** Tu código está en GitHub

---

## 🚂 Paso 3: Crear Proyecto en Railway (3 minutos)

1. Ve a: **https://railway.app/dashboard**
2. Click en **"New Project"**
3. Selecciona **"Deploy from GitHub repo"**
4. Busca y selecciona tu repositorio **"talenthub"** (o como lo hayas llamado)
5. Railway comenzará a desplegar automáticamente

✅ **Listo:** Tu servidor está desplegándose

---

## 🗄️ Paso 4: Agregar Base de Datos MySQL (2 minutos)

1. En tu proyecto de Railway, click en **"New"**
2. Selecciona **"Database"**
3. Click en **"Add MySQL"**
4. Railway creará la base de datos automáticamente
5. Espera 30 segundos a que se active

✅ **Listo:** Base de datos MySQL creada

---

## 🔧 Paso 5: Configurar Variables de Entorno (2 minutos)

1. En Railway, click en tu servicio (el que tiene tu código)
2. Ve a la pestaña **"Variables"**
3. Click en **"RAW Editor"**
4. Pega esto:

```
ENVIRONMENT=production
DB_HOST=${{MySQL.MYSQL_PRIVATE_URL}}
DB_USER=${{MySQL.MYSQLUSER}}
DB_PASSWORD=${{MySQL.MYSQLPASSWORD}}
DB_NAME=${{MySQL.MYSQLDATABASE}}
DB_PORT=${{MySQL.MYSQLPORT}}
```

5. Click en **"Update Variables"**

✅ **Listo:** Variables configuradas

---

## 🌐 Paso 6: Obtener tu URL Pública (1 minuto)

1. En Railway, click en tu servicio
2. Ve a la pestaña **"Settings"**
3. Busca la sección **"Networking"**
4. Click en **"Generate Domain"**
5. Railway te dará una URL como: `talenthub-production.up.railway.app`

✅ **Listo:** Ya tienes tu URL permanente

---

## 📊 Paso 7: Configurar la Base de Datos (3 minutos)

### Opción A: Desde Railway CLI (Recomendado)

```bash
# Instalar Railway CLI
npm install -g @railway/cli

# O con PowerShell:
iwr https://railway.app/install.ps1 | iex

# Luego:
railway login
railway link
railway run python setup_database_cloud.py
```

### Opción B: Manualmente

1. En Railway, ve a tu base de datos MySQL
2. Click en **"Connect"**
3. Copia las credenciales
4. Usa MySQL Workbench o cualquier cliente MySQL
5. Conecta y ejecuta los scripts SQL:
   - `database_mvp.sql`
   - `database_auth_fix.sql`
   - `database_gps_fix.sql`

✅ **Listo:** Base de datos configurada

---

## 🎉 Paso 8: Probar tu Aplicación

1. Abre tu URL de Railway: `https://tu-app.up.railway.app`
2. Ve al formulario: `https://tu-app.up.railway.app/trabajador/registro`
3. Prueba registrar un trabajador
4. Ve al panel de admin: `https://tu-app.up.railway.app/trabajador/admin/login`
   - Password: `admin123`

✅ **Listo:** ¡Tu aplicación está en línea 24/7!

---

## 📱 Compartir el Formulario

**URL Permanente del Formulario:**
```
https://tu-app.up.railway.app/trabajador/registro
```

Esta URL **NUNCA cambia**, compártela con confianza en:
- WhatsApp
- Facebook
- Instagram
- Volantes impresos
- Tarjetas de presentación

---

## 💰 Costos

Railway te da **$5 USD gratis** cada mes.

**Uso estimado:**
- Servidor pequeño: ~$3-5/mes
- Base de datos MySQL: ~$2-3/mes
- **Total: ~$5-8 USD/mes**

Si usas menos de $5/mes, es **GRATIS**.

---

## 🔄 Actualizar tu Aplicación

Cada vez que hagas cambios en tu código:

### Con GitHub Desktop:
1. Abre GitHub Desktop
2. Verás los cambios en la izquierda
3. Escribe un mensaje de commit
4. Click en **"Commit to main"**
5. Click en **"Push origin"**

### Con Terminal:
```bash
git add .
git commit -m "Descripción del cambio"
git push
```

Railway detectará los cambios y desplegará automáticamente en 1-2 minutos.

---

## 📊 Monitorear tu Aplicación

En Railway puedes ver:
- **Logs:** Ver qué está pasando en tiempo real
- **Metrics:** CPU, RAM, tráfico
- **Deployments:** Historial de despliegues

---

## ⚠️ Solución de Problemas

### Si el deploy falla:

1. Ve a **"Deployments"** en Railway
2. Click en el deploy fallido
3. Lee los logs para ver el error
4. Común: Falta algún archivo o dependencia

### Si no puedes conectar a la base de datos:

1. Verifica que las variables de entorno estén correctas
2. Verifica que la base de datos MySQL esté corriendo
3. Revisa los logs del servicio

### Si el formulario no carga:

1. Verifica que el deploy haya terminado exitosamente
2. Abre la consola del navegador (F12) para ver errores
3. Revisa los logs en Railway

---

## 🆘 Soporte

**Railway:**
- Docs: https://docs.railway.app
- Discord: https://discord.gg/railway
- Status: https://status.railway.app

**Tu Desarrollador:**
- [Tu nombre]
- [Tu email]
- [Tu teléfono]

---

## ✅ Checklist Final

- [ ] Cuenta de Railway creada
- [ ] Código subido a GitHub
- [ ] Proyecto creado en Railway
- [ ] Base de datos MySQL agregada
- [ ] Variables de entorno configuradas
- [ ] Dominio generado
- [ ] Base de datos configurada (tablas creadas)
- [ ] Formulario probado y funcionando
- [ ] Panel de admin accesible
- [ ] URL compartida en redes sociales

---

## 🎯 Próximos Pasos

1. **Promocionar:** Comparte la URL en redes sociales
2. **Monitorear:** Revisa los registros cada 2-3 horas
3. **Optimizar:** Basado en el feedback de los usuarios
4. **Escalar:** Si crece mucho, considera plan más grande

---

## 💡 Tips

- **Dominio personalizado:** Puedes usar tu propio dominio (ej: talenthub.com)
- **Backups:** Railway hace backups automáticos de la base de datos
- **Logs:** Revisa los logs regularmente para detectar problemas
- **Alertas:** Configura alertas para cuando algo falle

---

¡Felicidades! 🎉 Tu aplicación está en la nube 24/7 sin necesidad de tu PC.
