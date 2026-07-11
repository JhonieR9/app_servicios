/**
 * TalentHub — Modal de confirmación bonito
 * Reemplaza el confirm() nativo del navegador
 * Uso: await thConfirm('¿Seguro?') → true/false
 *      await thConfirm({ titulo, mensaje, btnOk, btnCancel, tipo }) → true/false
 */
function thConfirm(opciones) {
    return new Promise(resolve => {
        // Normalizar parámetros
        if (typeof opciones === 'string') {
            opciones = { mensaje: opciones };
        }
        const {
            titulo    = 'Confirmar acción',
            mensaje   = '¿Estás seguro?',
            btnOk     = 'Confirmar',
            btnCancel = 'Cancelar',
            tipo      = 'default',   // 'default' | 'danger' | 'success' | 'warning'
            icono     = null
        } = opciones;

        // Colores por tipo
        const COLORES = {
            default: { grad: 'linear-gradient(135deg,#4f46e5,#7c3aed)', sombra: 'rgba(99,102,241,.35)' },
            danger:  { grad: 'linear-gradient(135deg,#ef4444,#dc2626)', sombra: 'rgba(239,68,68,.35)' },
            success: { grad: 'linear-gradient(135deg,#10b981,#059669)', sombra: 'rgba(16,185,129,.35)' },
            warning: { grad: 'linear-gradient(135deg,#f59e0b,#d97706)', sombra: 'rgba(245,158,11,.35)' },
        };
        const col = COLORES[tipo] || COLORES.default;

        const ICONOS = { default:'❓', danger:'⚠️', success:'✅', warning:'⚠️' };
        const ic = icono || ICONOS[tipo] || '❓';

        // Eliminar modal anterior si existe
        const viejo = document.getElementById('thConfirmModal');
        if (viejo) viejo.remove();

        const overlay = document.createElement('div');
        overlay.id = 'thConfirmModal';
        overlay.style.cssText = `
            position:fixed;inset:0;z-index:99999;
            background:rgba(0,0,0,0.55);backdrop-filter:blur(4px);
            display:flex;align-items:center;justify-content:center;
            padding:20px;animation:thFadeIn .2s ease;
        `;

        overlay.innerHTML = `
            <style>
                @keyframes thFadeIn  { from{opacity:0} to{opacity:1} }
                @keyframes thSlideUp { from{opacity:0;transform:translateY(20px) scale(.96)} to{opacity:1;transform:translateY(0) scale(1)} }
                #thConfirmBox {
                    background:white; border-radius:22px;
                    width:100%; max-width:360px;
                    padding:32px 24px 24px;
                    text-align:center;
                    box-shadow:0 24px 64px rgba(0,0,0,0.22);
                    animation:thSlideUp .25s cubic-bezier(.34,1.56,.64,1);
                    font-family:'Inter','Segoe UI',sans-serif;
                }
                .th-confirm-icon { font-size:3rem; margin-bottom:12px; display:block; }
                .th-confirm-titulo { font-size:1.05rem; font-weight:800; color:#0f172a; margin-bottom:8px; }
                .th-confirm-msg { font-size:0.88rem; color:#64748b; line-height:1.55; margin-bottom:24px; }
                .th-confirm-btns { display:flex; gap:10px; }
                .th-btn-ok {
                    flex:1; padding:13px; border:none; border-radius:13px;
                    background:${col.grad}; color:white; font-weight:700;
                    font-size:0.92rem; cursor:pointer;
                    box-shadow:0 4px 14px ${col.sombra};
                    transition:transform .15s,box-shadow .15s;
                    font-family:inherit;
                }
                .th-btn-ok:hover { transform:translateY(-2px); }
                .th-btn-cancel {
                    flex:1; padding:13px; border:2px solid #e2e8f0;
                    border-radius:13px; background:white; color:#64748b;
                    font-weight:700; font-size:0.92rem; cursor:pointer;
                    transition:background .15s; font-family:inherit;
                }
                .th-btn-cancel:hover { background:#f8fafc; }
            </style>
            <div id="thConfirmBox">
                <span class="th-confirm-icon">${ic}</span>
                <div class="th-confirm-titulo">${titulo}</div>
                <div class="th-confirm-msg">${mensaje}</div>
                <div class="th-confirm-btns">
                    <button class="th-btn-cancel" id="thBtnCancel">${btnCancel}</button>
                    <button class="th-btn-ok"     id="thBtnOk">${btnOk}</button>
                </div>
            </div>
        `;

        document.body.appendChild(overlay);

        // Cerrar al hacer clic fuera
        overlay.addEventListener('click', e => {
            if (e.target === overlay) { overlay.remove(); resolve(false); }
        });

        // Botón cancelar
        overlay.querySelector('#thBtnCancel').addEventListener('click', () => {
            overlay.remove(); resolve(false);
        });

        // Botón confirmar
        overlay.querySelector('#thBtnOk').addEventListener('click', () => {
            overlay.remove(); resolve(true);
        });

        // Tecla Escape
        const onKey = e => {
            if (e.key === 'Escape') { overlay.remove(); resolve(false); document.removeEventListener('keydown', onKey); }
            if (e.key === 'Enter')  { overlay.remove(); resolve(true);  document.removeEventListener('keydown', onKey); }
        };
        document.addEventListener('keydown', onKey);
    });
}
