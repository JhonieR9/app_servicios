# 🗑️ PAPELERA DE RECICLAJE (Soft Delete)

## ¿Qué es Soft Delete?

Es una alternativa al **Flashback de Oracle** para MySQL. En lugar de eliminar permanentemente los registros, los marcamos como "eliminados" y los movemos a una papelera.

---

## 🎯 **CÓMO FUNCIONA:**

### **ANTES (Eliminación Permanente):**
```
Usuario hace clic en "Eliminar"
        ↓
Registro se borra de la base de datos
        ↓
❌ NO SE PUEDE RECUPERAR
```

### **AHORA (Soft Delete):**
```
Usuario hace clic en "Eliminar"
        ↓
Registro se marca como "eliminado"
        ↓
Se mueve a la Papelera
        ↓
✅ SE PUEDE RESTAURAR
```

---

## 📊 **ESTADOS DE UN REGISTRO:**

1. **activo** - Registro normal, visible en el panel
2. **inactivo** - Registro desactivado (para uso futuro)
3. **eliminado** - Registro en papelera, puede restaurarse

---

## 🔄 **FLUJO COMPLETO:**

### **1. Eliminar un Registro:**
```
Panel Admin → Clic en "Eliminar"
        ↓
Registro cambia a estado "eliminado"
        ↓
Se guarda fecha_eliminacion
        ↓
Desaparece del panel principal
        ↓
Aparece en "Ver Eliminados"
```

### **2. Ver Papelera:**
```
Panel Admin → Clic en "Ver Eliminados"
        ↓
Muestra todos los registros eliminados
        ↓
Con fecha de eliminación
        ↓
Opciones: Restaurar o Eliminar Permanente
```

### **3. Restaurar un Registro:**
```
Papelera → Clic en "Restaurar"
        ↓
Registro cambia a estado "activo"
        ↓
Se borra fecha_eliminacion
        ↓
Vuelve al panel principal
```

### **4. Eliminar Permanentemente:**
```
Papelera → Clic en "Eliminar Permanente"
        ↓
Confirmación de seguridad
        ↓
Registro se borra de la BD
        ↓
IDs se reorganizan
        ↓
Archivos se eliminan
        ↓
❌ NO SE PUEDE RECUPERAR
```

---

## 💾 **CAMBIOS EN LA BASE DE DATOS:**

### **Columnas Agregadas:**
```sql
fecha_eliminacion TIMESTAMP NULL
estado ENUM('activo', 'inactivo', 'eliminado')
```

### **Ejemplo de Registro:**
```
ACTIVO:
id_persona: 1
nombre: Juan Pérez
estado: 'activo'
fecha_eliminacion: NULL

ELIMINADO:
id_persona: 2
nombre: María López
estado: 'eliminado'
fecha_eliminacion: '2026-01-28 15:30:00'
```

---

## 🎨 **INTERFAZ:**

### **Panel Principal:**
```
┌─────────────────────────────────────────────┐
│ [+ Nuevo] [🗑️ Ver Eliminados] [📥 Excel]   │
└─────────────────────────────────────────────┘

Solo muestra registros con estado = 'activo'
```

### **Papelera:**
```
┌─────────────────────────────────────────────┐
│ 🗑️ Papelera de Reciclaje                    │
│ [← Volver a Registros]                      │
└─────────────────────────────────────────────┘

⚠️ Registros en papelera: 3

┌─────────────────────────────────────────────┐
│ Juan Pérez - CC: 123456                     │
│ Eliminado: 28/01/2026 15:30                 │
│ [↻ Restaurar] [🗑️ Eliminar Permanente]     │
└─────────────────────────────────────────────┘
```

---

## ✅ **VENTAJAS:**

1. **Recuperación de Errores**
   - Si eliminas por error, puedes restaurar
   - No pierdes datos importantes

2. **Auditoría**
   - Sabes cuándo se eliminó cada registro
   - Puedes revisar antes de eliminar permanentemente

3. **Seguridad**
   - Doble confirmación para eliminación permanente
   - Reduce riesgo de pérdida de datos

4. **Flexibilidad**
   - Puedes limpiar la papelera cuando quieras
   - O mantener registros históricos

---

## 🚀 **INSTALACIÓN:**

### **1. Ejecutar migración:**
```bash
mysql -u root -p < migrar_soft_delete.sql
```

### **2. Reiniciar aplicación:**
```bash
python app.py
```

### **3. Probar:**
```
1. Acceder a http://localhost:5000/admin/login
2. Eliminar un registro
3. Hacer clic en "Ver Eliminados"
4. Restaurar o eliminar permanentemente
```

---

## 📝 **RUTAS NUEVAS:**

```python
/eliminados              # Ver papelera
/restaurar/<id>          # Restaurar registro
/eliminar-permanente/<id> # Eliminar definitivamente
```

---

## ⚠️ **IMPORTANTE:**

### **Eliminación Normal:**
- Solo marca como eliminado
- NO borra archivos
- NO reorganiza IDs
- Reversible

### **Eliminación Permanente:**
- Borra de la base de datos
- Elimina archivos físicos
- Reorganiza IDs
- ❌ NO reversible

---

## 🎯 **CASOS DE USO:**

### **Caso 1: Error Humano**
```
Administrador elimina registro por error
        ↓
Va a "Ver Eliminados"
        ↓
Hace clic en "Restaurar"
        ↓
✅ Registro recuperado
```

### **Caso 2: Limpieza Periódica**
```
Cada mes, revisar papelera
        ↓
Eliminar permanentemente registros antiguos
        ↓
Liberar espacio en disco
```

### **Caso 3: Auditoría**
```
Revisar qué registros se eliminaron
        ↓
Ver fecha de eliminación
        ↓
Decidir si restaurar o eliminar
```

---

## 🔍 **COMPARACIÓN CON FLASHBACK:**

### **Oracle Flashback:**
```
✅ Viaja en el tiempo
✅ Recupera cualquier cambio
✅ Automático
❌ Solo en Oracle
❌ Requiere configuración compleja
```

### **Soft Delete (Nuestra Solución):**
```
✅ Funciona en MySQL
✅ Simple de implementar
✅ Fácil de entender
✅ Control total
❌ Solo para eliminaciones
❌ No recupera modificaciones
```

---

## 💡 **MEJORAS FUTURAS:**

1. **Auto-limpieza**
   - Eliminar automáticamente después de 30 días

2. **Historial de Cambios**
   - Guardar todas las modificaciones
   - No solo eliminaciones

3. **Búsqueda en Papelera**
   - Filtrar registros eliminados
   - Buscar por fecha

4. **Exportar Papelera**
   - Descargar registros eliminados
   - Para auditoría

---

## ✅ **CHECKLIST DE PRUEBAS:**

- [ ] Eliminar un registro → Va a papelera
- [ ] Ver papelera → Muestra registros eliminados
- [ ] Restaurar registro → Vuelve al panel
- [ ] Eliminar permanente → Se borra definitivamente
- [ ] IDs se reorganizan correctamente
- [ ] Archivos se eliminan solo en eliminación permanente
- [ ] Mensajes de confirmación funcionan
- [ ] Contador de papelera es correcto

---

**¡Sistema de Papelera implementado exitosamente! 🎉**
