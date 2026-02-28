# 🚀 Guía para Lanzar el Formulario 24/7

## 📋 Opciones Disponibles

### Opción 1: Ngrok (Rápido - Recomendado para Inicio)

**Ventajas:**
- ✅ Configuración en 5 minutos
- ✅ HTTPS automático
- ✅ No requiere configuración de red
- ✅ Perfecto para lanzamiento inicial

**Desventajas:**
- ⚠️ Requiere que tu PC esté encendido 24/7
- ⚠️ La URL cambia si reinicias ngrok (con plan gratis)
- ⚠️ Plan gratis tiene límites de conexiones

**Pasos:**

1. **Mantener el servidor corriendo:**
   ```bash
   # Terminal 1: Servidor FastAPI
   uvicorn main:app --host 0.0.0.0 --port 8000 --reload
   ```

2. **Mantener ngrok corriendo:**
   ```bash
   # Terminal 2: Ngrok
   ngrok http 8000
   ```

3. **URL Pública:**
   ```
   https://alta-dynamoelectric-dania.ngrok-free.app
   ```

4. **Compartir el formulario:**
   ```
   https://alta-dynamoelectric-dania.ngrok-free.app/trabajador/registro
   ```

**Para mantenerlo 24/7:**
- Deja ambas terminales abiertas
- No cierres la laptop o configura para que no se suspenda
- Asegúrate de tener buena conexión a internet

---

### Opción 2: Ngrok con URL Fija (Recomendado)

**Costo:** $8 USD/mes
**Ventaja:** URL permanente que no cambia

1. **Actualizar plan de ngrok:**
   - Ve a: https://dashboard.ngrok.com/billing
   - Suscríbete al plan Personal ($8/mes)

2. **Configurar dominio fijo:**
   ```bash
   ngrok http 8000 --domain=tu-empresa.ngrok-free.app
   ```

3. **La URL será siempre la misma** incluso si reinicias

---

### Opción 3: Servidor en la Nube (Profesional)

**Opciones de hosting:**

#### A) Railway.app (Más Fácil)
- **Costo:** ~$5-10 USD/mes
- **Ventajas:** Deploy automático, HTTPS gratis, 24/7
- **Pasos:**
  1. Crear cuenta en railway.app
  2. Conectar tu repositorio GitHub
  3. Deploy automático

#### B) Heroku
- **Costo:** ~$7 USD/mes
- **Ventajas:** Muy confiable, fácil de usar

#### C) DigitalOcean / AWS / Google Cloud
- **Costo:** $5-20 USD/mes
- **Ventajas:** Control total, escalable
- **Desventajas:** Requiere más conocimientos técnicos

---

### Opción 4: Servidor Local con IP Pública (Gratis pero Complejo)

**Requisitos:**
- IP pública estática
- Configurar router (port forwarding)
- Configurar firewall
- Instalar certificado SSL

**No recomendado** para lanzamiento rápido.

---

## 🎯 Recomendación para Tu Caso

### Para Lanzamiento INMEDIATO (Hoy):

**Usa Ngrok Gratis:**

1. **Abre 2 terminales:**

   Terminal 1:
   ```bash
   uvicorn main:app --host 0.0.0.0 --port 8000
   ```

   Terminal 2:
   ```bash
   ngrok http 8000
   ```

2. **Comparte esta URL:**
   ```
   https://alta-dynamoelectric-dania.ngrok-free.app/trabajador/registro
   ```

3. **Deja tu PC encendida** con las terminales abiertas

4. **Configura Windows para no suspender:**
   - Panel de Control → Opciones de energía
   - Cambiar configuración del plan
   - Suspender el equipo: Nunca
   - Apagar pantalla: 30 minutos (opcional)

---

### Para Lanzamiento PROFESIONAL (1-2 días):

**Opción A: Ngrok con URL Fija ($8/mes)**
- Paga el plan Personal
- Tendrás URL permanente
- Más profesional

**Opción B: Railway.app ($5-10/mes)**
- Servidor en la nube 24/7
- No depende de tu PC
- Deploy en 30 minutos

---

## 📱 Compartir el Formulario

### URL del Formulario:
```
https://tu-url-ngrok.com/trabajador/registro
```

### Formas de compartir:

1. **WhatsApp:**
   ```
   🎯 ¡Únete a nuestro banco de talentos!
   
   Registra tu hoja de vida aquí:
   https://alta-dynamoelectric-dania.ngrok-free.app/trabajador/registro
   
   ✅ Gratis
   ✅ Rápido (5 minutos)
   ✅ Más oportunidades de trabajo
   ```

2. **Redes Sociales:**
   - Facebook
   - Instagram
   - LinkedIn

3. **Código QR:**
   - Genera un QR de la URL
   - Imprime y distribuye

---

## 🔧 Mantener el Servidor Corriendo

### Script para Windows (mantener_servidor.bat):

```batch
@echo off
title Servidor TalentHub 24/7
echo ========================================
echo SERVIDOR TALENTHUB - MODO 24/7
echo ========================================
echo.
echo Iniciando servidor...
echo.

cd C:\Users\Usuario\Desktop\app_servicios
uvicorn main:app --host 0.0.0.0 --port 8000

pause
```

### Script para Ngrok (mantener_ngrok.bat):

```batch
@echo off
title Ngrok TalentHub 24/7
echo ========================================
echo NGROK TALENTHUB - MODO 24/7
echo ========================================
echo.
echo Iniciando ngrok...
echo.

ngrok http 8000

pause
```

**Uso:**
1. Guarda ambos archivos .bat
2. Haz doble clic en cada uno
3. Déjalos corriendo

---

## 📊 Monitoreo

### Ver registros en tiempo real:

**Panel de Admin:**
```
https://tu-url-ngrok.com/trabajador/admin/login
Password: admin123
```

### Ver estadísticas:
- Total de registros
- Categorías más populares
- Ciudades con más registros

---

## ⚠️ Consideraciones Importantes

### Seguridad:
- ✅ Ya tienes validación de datos
- ✅ Ya tienes protección contra duplicados
- ⚠️ Considera agregar CAPTCHA si hay spam

### Respaldo:
```bash
# Hacer backup de la base de datos diariamente
mysqldump -u root -p profiles_cv_db > backup_$(date +%Y%m%d).sql
```

### Monitoreo:
- Revisa el panel de admin cada 2-3 horas
- Verifica que el servidor siga corriendo
- Revisa la calidad de los registros

---

## 🎉 Checklist de Lanzamiento

- [ ] Servidor corriendo en puerto 8000
- [ ] Ngrok corriendo y URL activa
- [ ] Formulario accesible desde internet
- [ ] Panel de admin funcional
- [ ] Base de datos vacía y lista
- [ ] PC configurada para no suspender
- [ ] URL compartida en redes sociales
- [ ] Mensaje de WhatsApp preparado
- [ ] Alguien monitoreando los registros

---

## 📞 Soporte

Si algo falla:
1. Verifica que ambas terminales estén corriendo
2. Revisa la conexión a internet
3. Reinicia el servidor si es necesario
4. Verifica que MySQL esté corriendo

---

## 💡 Tips Adicionales

1. **Promoción:**
   - Ofrece incentivo por registro (sorteo, descuento)
   - Comparte en grupos de WhatsApp locales
   - Contacta gremios y asociaciones

2. **Validación:**
   - Revisa registros cada 2-3 horas
   - Elimina registros falsos o duplicados
   - Contacta a los mejores perfiles

3. **Mejoras futuras:**
   - Agregar verificación por SMS
   - Agregar verificación de documentos
   - Agregar sistema de calificaciones

---

¡Éxito con el lanzamiento! 🚀
