/* TalentHub - catalogo de servicios compartido (iconos, problemas frecuentes y buscador).
   Lo usan la pantalla de inicio (buscador) y el formulario de solicitud. */

// Iconos Bootstrap Icons + color de fondo por categoría
const CAT_CONFIG = {
    'Plomería':           { bg:'#dbeafe', color:'#2563eb', icon:'bi-droplet-fill' },
    'Plomeria':           { bg:'#dbeafe', color:'#2563eb', icon:'bi-droplet-fill' },
    'Electricidad':       { bg:'#fef9c3', color:'#ca8a04', icon:'bi-lightning-charge-fill' },
    'Limpieza':           { bg:'#dcfce7', color:'#16a34a', icon:'bi-stars' },
    'Carpintería':        { bg:'#ffedd5', color:'#ea580c', icon:'bi-hammer' },
    'Carpinteria':        { bg:'#ffedd5', color:'#ea580c', icon:'bi-hammer' },
    'Pintura':            { bg:'#fce7f3', color:'#db2777', icon:'bi-brush-fill' },
    'Jardinería':         { bg:'#dcfce7', color:'#15803d', icon:'bi-tree-fill' },
    'Jardineria':         { bg:'#dcfce7', color:'#15803d', icon:'bi-tree-fill' },
    'Cerrajería':         { bg:'#f3e8ff', color:'#7c3aed', icon:'bi-key-fill' },
    'Cerrajeria':         { bg:'#f3e8ff', color:'#7c3aed', icon:'bi-key-fill' },
    'Mudanza':            { bg:'#fef3c7', color:'#d97706', icon:'bi-box-seam-fill' },
    'Construcción':       { bg:'#ffedd5', color:'#c2410c', icon:'bi-building-fill' },
    'Construccion':       { bg:'#ffedd5', color:'#c2410c', icon:'bi-building-fill' },
    'Vidriería':          { bg:'#e0f2fe', color:'#0284c7', icon:'bi-window' },
    'Vidrieria':          { bg:'#e0f2fe', color:'#0284c7', icon:'bi-window' },
    'Impermeabilización': { bg:'#cffafe', color:'#0891b2', icon:'bi-shield-fill-check' },
    'Impermeabilizacion': { bg:'#cffafe', color:'#0891b2', icon:'bi-shield-fill-check' },
    'Lavandería':         { bg:'#ede9fe', color:'#6d28d9', icon:'bi-basket2-fill' },
    'Lavanderia':         { bg:'#ede9fe', color:'#6d28d9', icon:'bi-basket2-fill' },
    'Control de plagas':  { bg:'#fef9c3', color:'#a16207', icon:'bi-bug-fill' },
    'Tecnología':         { bg:'#dbeafe', color:'#1d4ed8', icon:'bi-laptop-fill' },
    'Tecnologia':         { bg:'#dbeafe', color:'#1d4ed8', icon:'bi-laptop-fill' },
    'Electrodomésticos':  { bg:'#fce7f3', color:'#be185d', icon:'bi-plug-fill' },
    'Electrodomesticos':  { bg:'#fce7f3', color:'#be185d', icon:'bi-plug-fill' },
    'CCTV y Alarmas':     { bg:'#f1f5f9', color:'#475569', icon:'bi-camera-video-fill' },
    'Transporte':         { bg:'#fef3c7', color:'#b45309', icon:'bi-truck-front-fill' },
    'Mecánica':           { bg:'#f3f4f6', color:'#374151', icon:'bi-gear-fill' },
    'Mecanica':           { bg:'#f3f4f6', color:'#374151', icon:'bi-gear-fill' },
    'Salud':              { bg:'#fee2e2', color:'#dc2626', icon:'bi-heart-pulse-fill' },
    'Belleza':            { bg:'#fdf2f8', color:'#c026d3', icon:'bi-scissors' },
    'Gastronomía':        { bg:'#fff7ed', color:'#ea580c', icon:'bi-egg-fried' },
    'Gastronomia':        { bg:'#fff7ed', color:'#ea580c', icon:'bi-egg-fried' },
    'Eventos':            { bg:'#fdf4ff', color:'#a21caf', icon:'bi-balloon-fill' },
    'Fotografía':         { bg:'#f0fdf4', color:'#15803d', icon:'bi-camera-fill' },
    'Fotografia':         { bg:'#f0fdf4', color:'#15803d', icon:'bi-camera-fill' },
    'Contabilidad':       { bg:'#ecfdf5', color:'#059669', icon:'bi-calculator-fill' },
    'Diseño':             { bg:'#fdf4ff', color:'#9333ea', icon:'bi-palette-fill' },
    'Diseno':             { bg:'#fdf4ff', color:'#9333ea', icon:'bi-palette-fill' },
    'Mensajería':         { bg:'#eff6ff', color:'#3b82f6', icon:'bi-send-fill' },
    'Mensajeria':         { bg:'#eff6ff', color:'#3b82f6', icon:'bi-send-fill' },
    'Idiomas':            { bg:'#f0f9ff', color:'#0369a1', icon:'bi-translate' },
    'Masajes':            { bg:'#fdf2f8', color:'#db2777', icon:'bi-person-arms-up' },
    'Veterinaria':        { bg:'#f0fdf4', color:'#16a34a', icon:'bi-heart-pulse' },
    'Mascotas':           { bg:'#fef9c3', color:'#92400e', icon:'bi-emoji-heart-eyes' },
    'Educación':          { bg:'#fef9c3', color:'#854d0e', icon:'bi-book-fill' },
    'Educacion':          { bg:'#fef9c3', color:'#854d0e', icon:'bi-book-fill' },
    'Reparaciones Locativas': { bg:'#f0fdf4', color:'#166534', icon:'bi-house-gear-fill' },
    'Psicología':         { bg:'#fce7f3', color:'#9333ea', icon:'bi-person-hearts' },
    'Psicologia':         { bg:'#fce7f3', color:'#9333ea', icon:'bi-person-hearts' },
    'Derecho':            { bg:'#ede9fe', color:'#4338ca', icon:'bi-bank2' },
};
const CAT_DEFAULT = { bg:'#f1f5f9', color:'#64748b', icon:'bi-tools' };

// CHIPS PER CATEGORY
const CHIPS = {
    'Plomeria':              ['Tubería rota','Goteras','Instalación nueva','Baño tapado','Otro'],
    'Electricidad':          ['Sin luz','Corto circuito','Instalación','Toma dañada','Otro'],
    'Limpieza':              ['Casa completa','Oficina','Post-obra','Solo baños','Otro'],
    'Carpinteria':           ['Mueble roto','Puerta dañada','Instalación','Closet','Otro'],
    'Pintura':               ['Interior','Exterior','Retoques','Impermeabilizar','Otro'],
    'Jardineria':            ['Corte de césped','Poda','Diseño de jardín','Fumigación','Otro'],
    'Mecanica':              ['Carro no enciende','Cambio de aceite','Frenos','Llantas','Otro'],
    'Tecnologia':            ['PC lento','Virus','Red/WiFi','Instalación software','Otro'],
    'Construccion':          ['Remodelación','Fisuras','Pisos','Techo','Otro'],
    'Educacion':             ['Matemáticas','Inglés','Refuerzo escolar','Universitario','Otro'],
    'Salud':                 ['Enfermería','Fisioterapia','Cuidado adulto mayor','Primeros auxilios','Otro'],
    'Belleza':               ['Corte de cabello','Manicure','Maquillaje','Depilación','Otro'],
    'Gastronomia':           ['Almuerzo','Cena especial','Domicilio','Catering','Otro'],
    // Transporte = llevar personas o carga. Los paquetes, documentos y mandados son de Mensajería,
    // y los trasteos de casa o apartamento son de Mudanza.
    'Transporte':            ['Traslado de personas','Traslado al aeropuerto','Viaje a otro municipio','Carga o mercancía','Otro'],
    'Cerrajeria':            ['Puerta bloqueada','Cambio de chapa','Copia de llave','Caja fuerte','Otro'],
    'Mudanza':               ['Apartamento','Casa','Solo muebles grandes','Embalaje','Otro'],
    'Vidrieria':             ['Vidrio roto','Ventana nueva','Espejo','Vitrina','Otro'],
    'Impermeabilizacion':    ['Techo con filtración','Terraza','Baño','Sótano','Otro'],
    'Lavanderia':            ['Ropa general','Sábanas','Cortinas','Planchado','Otro'],
    'Control de plagas':     ['Cucarachas','Ratas','Hormigas','Pulgas','Otro'],
    'Electrodomesticos':     ['Nevera','Lavadora','Horno','Aire acondicionado','Otro'],
    'CCTV y Alarmas':        ['Cámaras nuevas','Mantenimiento','Alarma','Control de acceso','Otro'],
    'Idiomas':               ['Inglés','Francés','Alemán','Portugués','Otro'],
    'Eventos':               ['Decoración','Organización','Sonido','Iluminación','Otro'],
    'Fotografia':            ['Matrimonio','Quinces','Empresarial','Producto','Otro'],
    'Contabilidad':          ['Declaración de renta','Nómina','Contabilidad mensual','Asesoría','Otro'],
    'Diseno':                ['Logo','Redes sociales','Publicidad','Página web','Otro'],
    'Mensajeria':            ['Documentos','Paquete pequeño','Paquete grande','Urgente','Otro'],
    'Masajes':               ['Relajante','Terapéutico','Deportivo','Prenatal','Otro'],
    'Veterinaria':           ['Consulta general','Vacunas','Desparasitación','Urgencia','Otro'],
    'Mascotas':              ['Paseo de perros','Cuidador en casa','Guardería','Baño y peluquería','Adiestramiento','Otro'],
};

// ============================================================
// BUSCADOR: sinonimos y utilidades (usa CAT_CONFIG y CHIPS de arriba)
// ============================================================

// Nombres oficiales de las categorias (se usan si no se pueden pedir al servidor)
const CATEGORIAS_BASE = ['Plomería','Electricidad','Limpieza','Carpintería','Pintura','Jardinería','Cerrajería','Mudanza',
    'Construcción','Vidriería','Impermeabilización','Lavandería','Control de plagas','Tecnología','Electrodomésticos',
    'CCTV y Alarmas','Transporte','Mecánica','Salud','Belleza','Masajes','Veterinaria','Educación','Idiomas','Gastronomía',
    'Eventos','Fotografía','Contabilidad','Diseño','Mensajería','Mascotas','Reparaciones Locativas','Psicología'];

// Palabras que la gente usa para pedir cada servicio (clave: nombre sin tildes y en minusculas)
const SINONIMOS = {
    'plomeria': ['agua','fuga','fugas','llave','grifo','tuberia','tubo','bano','inodoro','sanitario','ducha','lavamanos','lavaplatos','caneria','calentador','tanque','destapar','desague','alcantarilla','gotera','goteras','taponado'],
    'electricidad': ['luz','energia','corriente','cable','cableado','toma','enchufe','bombillo','breaker','tablero','apagon','cortocircuito','lampara','interruptor','instalacion electrica','chispa'],
    'limpieza': ['aseo','limpiar','trapear','barrer','desinfeccion','lavar','mucama','empleada','domestica','casa','oficina','vidrios','alfombra','sofa','fondo'],
    'carpinteria': ['madera','mueble','muebles','puerta','closet','cocina integral','escritorio','cama','repisa','biblioteca','ebanista'],
    'pintura': ['pintar','pared','paredes','muro','fachada','estuco','drywall','techo','brocha','repintar'],
    'jardineria': ['jardin','cesped','pasto','poda','podar','plantas','arbol','arboles','matas','guadana','zacate'],
    'cerrajeria': ['llave','llaves','chapa','cerradura','puerta','candado','abrir','copia','bloqueada','encerrado','cerrajero'],
    'mudanza': ['trasteo','trastear','mudarse','cajas','acarreo','embalaje','flete','cambio de casa','cambio de apartamento'],
    'construccion': ['obra','remodelar','remodelacion','albanil','pisos','ceramica','techo','muro','fisura','cemento','plancha','maestro de obra'],
    'vidrieria': ['vidrio','vidrios','ventana','ventanas','espejo','cristal','vitrina','box de bano'],
    'impermeabilizacion': ['humedad','filtracion','gotera','goteras','techo','terraza','impermeabilizar','moho','sellar','salitre'],
    'lavanderia': ['ropa','lavar','planchar','planchado','sabanas','cortinas','tintoreria','edredon','cobijas'],
    'control de plagas': ['fumigar','fumigacion','cucaracha','cucarachas','rata','ratas','hormiga','hormigas','pulgas','mosquitos','termitas','comején','comejen','chinches','insectos','plaga','plagas'],
    'tecnologia': ['computador','computadora','pc','portatil','laptop','internet','wifi','router','virus','celular','impresora','red','software','formatear','sistema'],
    'electrodomesticos': ['nevera','refrigerador','lavadora','secadora','horno','estufa','microondas','aire acondicionado','ventilador','televisor','tv','licuadora','calentador','extractor'],
    'cctv y alarmas': ['camaras','camara','seguridad','alarma','vigilancia','cctv','citofono','portero','sensor','cerca electrica'],
    'transporte': ['viaje','viajes','taxi','carro','moto','camion','camioneta','carga','aeropuerto','conductor','pasajeros','llevar','trasladar','traslado'],
    'mecanica': ['carro','moto','vehiculo','motor','frenos','aceite','llantas','bateria','taller','varado','mecanico','no prende'],
    'salud': ['enfermera','enfermero','enfermeria','inyeccion','curacion','adulto mayor','cuidador','fisioterapia','medico','terapia','abuelo','abuela','sonda'],
    'belleza': ['peluqueria','peluquera','cabello','pelo','corte','manicure','pedicure','unas','maquillaje','depilacion','barba','tintura','peinado','barberia'],
    'masajes': ['masaje','relajante','espalda','spa','descontracturante','estres'],
    'veterinaria': ['perro','gato','mascota','veterinario','vacuna','animal','cachorro'],
    'educacion': ['clases','clase','tareas','profesor','profe','tutor','refuerzo','colegio','universidad','matematicas','ingles','fisica','quimica'],
    'idiomas': ['ingles','frances','aleman','portugues','traductor','traduccion','italiano'],
    'gastronomia': ['comida','cocinero','cocinera','chef','almuerzo','cena','catering','banquete','postres','torta','pastel','domicilio de comida'],
    'eventos': ['fiesta','fiestas','cumpleanos','matrimonio','boda','decoracion','sonido','dj','globos','quinceanera','baby shower','celebracion'],
    'fotografia': ['foto','fotos','fotografo','video','matrimonio','quinces','sesion','retrato'],
    'contabilidad': ['contador','contadora','impuestos','renta','dian','declaracion','nomina','facturacion','balance','rut'],
    'diseno': ['logo','grafico','publicidad','marca','pagina web','redes sociales','flyer','banner','identidad'],
    'mensajeria': ['paquete','paquetes','domicilio','documentos','envio','envios','mandado','mandados','entrega','diligencia','diligencias','recoger','mensajero'],
    'mascotas': ['perro','perros','gato','gatos','paseo','guarderia','peluqueria canina','cuidador','adiestramiento','hotel para mascotas','paseador'],
    'reparaciones locativas': ['arreglo','arreglos','mantenimiento','casa','gotera','goteras','hogar','reparacion','adecuaciones','remodelar','todero','handyman','arreglos de casa'],
    'psicologia': ['psicologo','psicologa','terapia','ansiedad','depresion','estres','pareja','emocional','orientacion','salud mental']
};

// Palabras extra para problemas concretos (clave: categoria|problema, sin tildes)
const SINONIMOS_PROBLEMA = {
    'plomeria|goteras': 'fuga gotea llave goteando',
    'plomeria|bano tapado': 'destapar inodoro desague atascado sanitario lavamanos',
    'plomeria|tuberia rota': 'fuga agua reventada inundacion',
    'electricidad|sin luz': 'apagon sin energia no hay luz no hay corriente',
    'electricidad|toma danada': 'enchufe tomacorriente',
    'electricidad|corto circuito': 'chispa breaker salto tumbo',
    'tecnologia|red/wifi': 'internet router senal conexion',
    'tecnologia|pc lento': 'computador lento demora',
    'mecanica|carro no enciende': 'varado bateria no prende no arranca',
    'cerrajeria|puerta bloqueada': 'encerrado no abre llave adentro atascada',
    'cerrajeria|cambio de chapa': 'cerradura nueva cambiar chapa',
    'control de plagas|cucarachas': 'fumigar fumigacion',
    'transporte|traslado al aeropuerto': 'aeropuerto vuelo',
    'mudanza|apartamento': 'trasteo trastear apartamento',
    'mudanza|casa': 'trasteo trastear casa',
    'limpieza|casa completa': 'aseo general',
    'pintura|interior': 'pintar paredes cuarto sala',
    'pintura|exterior': 'pintar fachada exterior',
    'belleza|corte de cabello': 'peluqueria barberia pelo',
    'mensajeria|documentos': 'papeles sobre tramite'
};

// Orden de desempate: lo que mas se pide primero
const ORDEN_POPULAR = ['Plomería','Electricidad','Limpieza','Cerrajería','Pintura','Carpintería','Mudanza','Transporte','Control de plagas','Electrodomésticos','Tecnología','Mecánica','Jardinería','Mensajería'];

// Sugerencias que se muestran antes de escribir
const POPULARES = [
    ['Electricidad', 'Sin luz'], ['Plomería', 'Goteras'], ['Limpieza', 'Casa completa'],
    ['Cerrajería', 'Puerta bloqueada'], ['Control de plagas', 'Cucarachas'], ['Transporte', 'Traslado al aeropuerto']
];

// Minusculas y sin tildes (la "ñ" pasa a "n"); conserva la longitud para poder resaltar
function foldTexto(s) {
    return String(s == null ? '' : s).toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '');
}
function palabrasDe(s) {
    return foldTexto(s).replace(/[^a-z0-9]+/g, ' ').trim().split(' ').filter(Boolean);
}
function claveChips(nombre) {            // misma regla que usa el formulario de solicitud
    return String(nombre).normalize('NFD').replace(/[\u0300-\u036f]/g, '');
}
function iconoCategoria(nombre) {
    return CAT_CONFIG[nombre] || CAT_CONFIG[claveChips(nombre)] || CAT_DEFAULT;
}
function problemasDe(nombre) {
    return (CHIPS[claveChips(nombre)] || []).filter(p => p !== 'Otro');
}

// Cuanto coincide la consulta con un texto principal, sinonimos y contexto. 0 = no coincide.
function puntaje(tokens, principal, sinonimos, contexto) {
    const pPal = palabrasDe(principal), pTexto = pPal.join(' ');
    const pSin = palabrasDe((sinonimos || []).join(' '));
    const pCtx = palabrasDe(contexto || '');
    let total = 0;
    for (const tk of tokens) {
        let mejor = 0;
        if (pPal.some(w => w.startsWith(tk))) mejor = 10;
        else if (tk.length >= 3 && pTexto.includes(tk)) mejor = 6;
        if (pSin.some(w => w === tk || (tk.length >= 3 && w.startsWith(tk)))) mejor = Math.max(mejor, 5);
        else if (tk.length >= 4 && pSin.some(w => w.includes(tk))) mejor = Math.max(mejor, 3);
        if (pCtx.some(w => w.startsWith(tk))) mejor = Math.max(mejor, 4);
        if (!mejor) return 0;              // todas las palabras escritas deben coincidir
        total += mejor;
    }
    return total;
}

// Busca categorias y problemas. Devuelve [{cat, prob, score, resumen}] ordenado.
function buscarServicios(consulta, categorias, max) {
    const tokens = palabrasDe(consulta);
    if (!tokens.length) return [];
    const salida = [];
    (categorias || CATEGORIAS_BASE).forEach(cat => {
        const clave = foldTexto(cat);
        const probs = problemasDe(cat);
        const resumen = probs.slice(0, 3).join(', ');
        const sc = puntaje(tokens, cat, SINONIMOS[clave] || [], '');
        if (sc > 0) salida.push({ cat, prob: '', score: sc + 2, resumen });
        probs.forEach(p => {
            const extra = SINONIMOS_PROBLEMA[clave + '|' + foldTexto(p)] || '';
            const sp = puntaje(tokens, p, extra ? [extra] : [], cat);
            if (sp > 0) salida.push({ cat, prob: p, score: sp, resumen: '' });
        });
    });
    // Con igual puntaje se prefieren las categorias que mas se piden
    const prioridad = c => { const i = ORDEN_POPULAR.indexOf(c); return i === -1 ? 99 : i; };
    salida.sort((a, b) => b.score - a.score || prioridad(a.cat) - prioridad(b.cat) || (a.prob ? 1 : 0) - (b.prob ? 1 : 0) || a.cat.localeCompare(b.cat, 'es'));
    return salida.slice(0, max || 8);
}

// Direccion del formulario de solicitud ya con la categoria (y el problema) elegidos
function urlServicio(cat, prob, idCliente) {
    let u = '/cliente/solicitar_servicio?categoria=' + encodeURIComponent(cat);
    u += prob ? '&problema=' + encodeURIComponent(prob) : '&paso=2';
    if (idCliente) u += '&id_cliente=' + encodeURIComponent(idCliente);
    return u;
}

window.Catalogo = {
    CATEGORIAS_BASE, POPULARES, foldTexto, palabrasDe, iconoCategoria, problemasDe,
    buscar: buscarServicios, urlServicio
};
