import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, date
import json
import pandas as pd

# ── Página ───────────────────────────────────────────────────────────────────
st.set_page_config(page_title="Zoolitos", page_icon="🐾", layout="wide")

# ── CSS ──────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Sans:wght@300;400;500&display=swap');

  html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
  h1,h2,h3 { font-family: 'Syne', sans-serif; }

  .block-container { padding: 1.5rem 2rem 3rem; max-width: 1200px; }

  /* Métricas */
  div[data-testid="metric-container"] {
    background: #1a1a2e; border: 1px solid #2a2a4a;
    border-radius: 12px; padding: 16px;
  }
  div[data-testid="metric-container"] label { color: #888 !important; font-size: 12px !important; text-transform: uppercase; letter-spacing: 0.05em; }
  div[data-testid="metric-container"] div[data-testid="stMetricValue"] { font-family: 'Syne', sans-serif; font-size: 1.6rem !important; color: #e8ff8b !important; }

  /* Botones */
  div[data-testid="stButton"] > button {
    border-radius: 8px; font-weight: 500; transition: all 0.15s;
  }
  div[data-testid="stButton"] > button[kind="primary"] {
    background: #e8ff8b !important; color: #0a0a1a !important; border: none !important;
  }
  div[data-testid="stButton"] > button[kind="primary"]:hover {
    background: #d4f060 !important;
  }

  /* Inputs */
  input, select, textarea {
    border-radius: 8px !important;
    background: #1a1a2e !important;
    color: #f0f0f0 !important;
    border: 1px solid #2a2a4a !important;
  }

  /* Tablas dataframe */
  div[data-testid="stDataFrame"] { border-radius: 12px; overflow: hidden; }

  /* Navegación radio */
  div[role="radiogroup"] label {
    background: #1a1a2e; border: 1px solid #2a2a4a;
    border-radius: 8px; padding: 8px 16px;
    font-family: 'Syne', sans-serif; font-weight: 600;
    transition: all 0.15s; cursor: pointer;
  }
  div[role="radiogroup"] label:has(input:checked) {
    background: #e8ff8b !important; color: #0a0a1a !important;
    border-color: #e8ff8b !important;
  }

  /* Tags */
  .tag-verde { background:#1a3a2a; color:#5dde8a; border:1px solid #2a5a3a; padding:2px 10px; border-radius:20px; font-size:12px; }
  .tag-rojo  { background:#3a1a1a; color:#de5d5d; border:1px solid #5a2a2a; padding:2px 10px; border-radius:20px; font-size:12px; }
  .tag-gris  { background:#2a2a3a; color:#aaa;    border:1px solid #3a3a4a; padding:2px 10px; border-radius:20px; font-size:12px; }
  .tag-amber { background:#3a2a1a; color:#dea85d; border:1px solid #5a4a2a; padding:2px 10px; border-radius:20px; font-size:12px; }

  .card {
    background: #1a1a2e; border: 1px solid #2a2a4a;
    border-radius: 12px; padding: 16px; margin-bottom: 8px;
  }

  .saldo-positivo { color: #de5d5d; font-weight: 700; font-family: 'Syne', sans-serif; font-size: 1.1rem; }
  .saldo-cero     { color: #5dde8a; font-weight: 700; font-family: 'Syne', sans-serif; font-size: 1.1rem; }

  /* Page title */
  .page-title {
    font-family: 'Syne', sans-serif; font-size: 1.6rem; font-weight: 800;
    color: #e8ff8b; margin-bottom: 1rem; letter-spacing: -0.02em;
  }

  /* Divider */
  hr { border-color: #2a2a4a !important; }
</style>
""", unsafe_allow_html=True)

# ── Google Sheets ─────────────────────────────────────────────────────────────
@st.cache_resource
def get_gc():
    """Conecta con Google Sheets usando Service Account"""
    creds = st.secrets["gcp_service_account"]
    
    scopes = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    
    credentials = Credentials.from_service_account_info(creds, scopes=scopes)
    return gspread.authorize(credentials)

def get_wb():
    return get_gc().open_by_key(st.secrets["SHEET_ID"])

def get_ws(name, headers):
    """Obtiene o crea una hoja con sus encabezados."""
    wb = get_wb()
    titles = [s.title for s in wb.worksheets()]
    if name not in titles:
        ws = wb.add_worksheet(title=name, rows=500, cols=len(headers))
        ws.append_row(headers)
        return ws
    return wb.worksheet(name)

# ── Cache de datos (TTL 20s) ──────────────────────────────────────────────────
@st.cache_data(ttl=20)
def load_clientes():
    ws = get_ws("Clientes", ["id","nombre","direccion","email","telefono","fecha_nacimiento","estado","fecha_alta","saldo_inicial"])
    rows = ws.get_all_values()
    
    if len(rows) <= 1:
        return pd.DataFrame(columns=["id","nombre","direccion","email","telefono","fecha_nacimiento","estado","fecha_alta","saldo_inicial"])
    
    df = pd.DataFrame(rows[1:], columns=rows[0])
    
    # Convertir columnas numéricas de forma segura
    for col in ["saldo_inicial"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
        else:
            df[col] = 0
    
    # Asegurar que existan todas las columnas esperadas
    expected_cols = ["id","nombre","direccion","email","telefono","fecha_nacimiento","estado","fecha_alta","saldo_inicial"]
    for col in expected_cols:
        if col not in df.columns:
            df[col] = "" if col == "fecha_nacimiento" else 0 if col == "saldo_inicial" else ""
    
    return df[expected_cols]  # Ordenar columnas

@st.cache_data(ttl=20)
def load_productos():
    ws = get_ws("Productos", ["id","nombre","descripcion","categoria","talla","color","precio_costo","stock"])
    rows = ws.get_all_values()
    if len(rows) <= 1: return pd.DataFrame(columns=["id","nombre","descripcion","categoria","talla","color","precio_costo","stock"])
    df = pd.DataFrame(rows[1:], columns=rows[0])
    df["precio_costo"] = pd.to_numeric(df["precio_costo"], errors="coerce").fillna(0)
    df["stock"] = pd.to_numeric(df["stock"], errors="coerce").fillna(0).astype(int)
    return df

@st.cache_data(ttl=20)
def load_ventas():
    ws = get_ws("Ventas", ["id","fecha","id_cliente","cliente","id_producto","producto","cantidad","precio_venta","total","pagado"])
    rows = ws.get_all_values()
    if len(rows) <= 1: return pd.DataFrame(columns=["id","fecha","id_cliente","cliente","id_producto","producto","cantidad","precio_venta","total","pagado"])
    df = pd.DataFrame(rows[1:], columns=rows[0])
    df["cantidad"]    = pd.to_numeric(df["cantidad"],    errors="coerce").fillna(0)
    df["precio_venta"]= pd.to_numeric(df["precio_venta"],errors="coerce").fillna(0)
    df["total"]       = pd.to_numeric(df["total"],       errors="coerce").fillna(0)
    return df

@st.cache_data(ttl=20)
def load_cobros():
    ws = get_ws("Cobros", ["id","fecha","id_cliente","cliente","monto","nota"])
    rows = ws.get_all_values()
    if len(rows) <= 1: return pd.DataFrame(columns=["id","fecha","id_cliente","cliente","monto","nota"])
    df = pd.DataFrame(rows[1:], columns=rows[0])
    df["monto"] = pd.to_numeric(df["monto"], errors="coerce").fillna(0)
    return df

def clear_cache():
    load_clientes.clear()
    load_productos.clear()
    load_ventas.clear()
    load_cobros.clear()

# ── Helpers ───────────────────────────────────────────────────────────────────
def new_id():
    return str(int(datetime.now().timestamp() * 1000))

def fmt(n):
    try: return f"${float(n):,.2f}".replace(",","X").replace(".",",").replace("X",".")
    except: return "$0,00"

def calcular_saldo_cliente(id_cliente, ventas_df, cobros_df, clientes_df):
    """Saldo = saldo_inicial + ventas no pagadas - cobros."""
    cl = clientes_df[clientes_df["id"] == str(id_cliente)]
    saldo_ini = float(cl["saldo_inicial"].values[0]) if len(cl) > 0 else 0

    v = ventas_df[(ventas_df["id_cliente"] == str(id_cliente)) & (ventas_df["pagado"].str.upper() != "SI")]
    total_ventas = v["total"].sum()

    c = cobros_df[cobros_df["id_cliente"] == str(id_cliente)]
    total_cobros = c["monto"].sum()

    return saldo_ini + total_ventas - total_cobros

# ── Estado sesión ─────────────────────────────────────────────────────────────
if "page" not in st.session_state: st.session_state["page"] = "Dashboard"
if "edit_cliente" not in st.session_state: st.session_state["edit_cliente"] = None
if "edit_producto" not in st.session_state: st.session_state["edit_producto"] = None

# ── Header ────────────────────────────────────────────────────────────────────
col_logo, col_nav = st.columns([1, 4])
with col_logo:
    st.markdown("## 🐾 Zoolitos")

with col_nav:
    pages = ["Dashboard", "Clientes", "Productos", "Ventas", "Cobros"]
    sel = st.radio("", pages, index=pages.index(st.session_state["page"]),
                   horizontal=True, label_visibility="collapsed", key="nav")
    if sel != st.session_state["page"]:
        st.session_state["page"] = sel
        st.session_state["edit_cliente"] = None
        st.session_state["edit_producto"] = None
        st.rerun()

st.markdown("---")
page = st.session_state["page"]

# ══════════════════════════════════════════════════════════════════════════════
# DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════
if page == "Dashboard":
    st.markdown('<div class="page-title">Dashboard</div>', unsafe_allow_html=True)

    clientes_df = load_clientes()
    productos_df = load_productos()
    ventas_df   = load_ventas()
    cobros_df   = load_cobros()

    # KPIs
    total_ventas = ventas_df["total"].sum() if len(ventas_df) > 0 else 0
    total_cobros = cobros_df["monto"].sum() if len(cobros_df) > 0 else 0
    stock_bajo   = len(productos_df[productos_df["stock"] <= 3]) if len(productos_df) > 0 else 0

    # Calcular total deuda
    total_deuda = 0
    if len(clientes_df) > 0:
        for _, cl in clientes_df.iterrows():
            s = calcular_saldo_cliente(cl["id"], ventas_df, cobros_df, clientes_df)
            if s > 0: total_deuda += s

    c1, c2, c3, c4 = st.columns(4)
    with c1: st.metric("Total vendido", fmt(total_ventas))
    with c2: st.metric("Total cobrado", fmt(total_cobros))
    with c3: st.metric("Deuda total", fmt(total_deuda))
    with c4: st.metric("Productos stock bajo", f"{stock_bajo} items")

    st.markdown("---")

    col_izq, col_der = st.columns(2)

    with col_izq:
        st.markdown("#### 🏆 Top 5 productos más vendidos")
        if len(ventas_df) > 0:
            top_prod = ventas_df.groupby("producto")["cantidad"].sum().sort_values(ascending=False).head(5).reset_index()
            top_prod.columns = ["Producto", "Unidades"]
            st.dataframe(top_prod, use_container_width=True, hide_index=True)
        else:
            st.caption("Sin datos todavía.")

    with col_der:
        st.markdown("#### ⚠️ Mayores deudores")
        if len(clientes_df) > 0:
            deudores = []
            for _, cl in clientes_df.iterrows():
                s = calcular_saldo_cliente(cl["id"], ventas_df, cobros_df, clientes_df)
                if s > 0:
                    deudores.append({"Cliente": cl["nombre"], "Saldo": s})
            if deudores:
                df_d = pd.DataFrame(deudores).sort_values("Saldo", ascending=False).head(5)
                df_d["Saldo"] = df_d["Saldo"].apply(fmt)
                st.dataframe(df_d, use_container_width=True, hide_index=True)
            else:
                st.success("Sin deudores pendientes ✓")
        else:
            st.caption("Sin datos todavía.")

    st.markdown("---")
    st.markdown("#### 📦 Productos con stock bajo (≤ 3 unidades)")
    if len(productos_df) > 0:
        bajo = productos_df[productos_df["stock"] <= 3][["nombre","categoria","talla","color","stock"]]
        if len(bajo) > 0:
            st.dataframe(bajo, use_container_width=True, hide_index=True)
        else:
            st.success("Todos los productos tienen stock suficiente ✓")
    else:
        st.caption("Sin productos cargados.")

# ══════════════════════════════════════════════════════════════════════════════
# CLIENTES
# ══════════════════════════════════════════════════════════════════════════════
elif page == "Clientes":
    st.markdown('<div class="page-title">Clientes</div>', unsafe_allow_html=True)

    clientes_df = load_clientes()
    ventas_df   = load_ventas()
    cobros_df   = load_cobros()

     # ── Formulario alta / edición ─────────────────────────────────────────────
    edit = st.session_state["edit_cliente"]

    with st.expander("➕ Nuevo cliente" if not edit else f"✏️ Editando: {edit['nombre']}", expanded=edit is not None):
        with st.form("form_cliente", clear_on_submit=True):   # ← Muy importante
            c1, c2 = st.columns(2)
            with c1:
                nombre        = st.text_input("Nombre *", value=edit.get("nombre", "") if edit else "")
                telefono      = st.text_input("Teléfono", value=edit.get("telefono", "") if edit else "")
                email         = st.text_input("Email", value=edit.get("email", "") if edit else "")
                fecha_nac     = st.date_input("Fecha de nacimiento", 
                                        value=datetime.strptime(edit.get("fecha_nacimiento", "01/01/2000"), "%d/%m/%Y").date() 
                                        if edit and edit.get("fecha_nacimiento") else date(2000, 1, 1))
        
            with c2:
                direccion     = st.text_input("Dirección", value=edit.get("direccion", "") if edit else "")
                estado        = st.selectbox("Estado", ["Activo","Inactivo"], 
                                        index=0 if not edit else (["Activo","Inactivo"].index(edit.get("estado", "Activo"))))
                saldo_ini     = st.number_input("Saldo inicial ($)", min_value=0.0, 
                                          value=float(edit.get("saldo_inicial", 0)) if edit else 0.0, 
                                          step=100.0, format="%.2f")

            submitted = st.form_submit_button("Guardar cliente", type="primary")

            if submitted:
                if not nombre.strip():
                    st.error("El nombre es obligatorio.")
                else:
                    ws = get_ws("Clientes", ["id","nombre","direccion","email","telefono","fecha_nacimiento","estado","fecha_alta","saldo_inicial"])
                
                    if edit:  # Actualizar
                        rows = ws.get_all_values()
                        for i, row in enumerate(rows[1:], start=2):
                            if row[0] == edit["id"]:
                                ws.update(f"A{i}:I{i}", [[ 
                                edit["id"], 
                                nombre.strip(), 
                                direccion, 
                                email, 
                                telefono, 
                                fecha_nac.strftime("%d/%m/%Y"), 
                                estado, 
                                edit.get("fecha_alta", date.today().strftime("%d/%m/%Y")), 
                                saldo_ini 
                                ]])
                                break
                        st.success(f"✓ Cliente '{nombre}' actualizado.")
                        st.session_state["edit_cliente"] = None
                    
                    else:  # Crear nuevo
                        ws.append_row([
                            new_id(), 
                            nombre.strip(), 
                            direccion, 
                            email, 
                            telefono, 
                            fecha_nac.strftime("%d/%m/%Y"), 
                            estado, 
                            date.today().strftime("%d/%m/%Y"), 
                            saldo_ini
                        ])
                        st.success(f"✓ Cliente '{nombre}' creado.")

                    clear_cache()
                    st.rerun()

        # Botón cancelar (fuera del form)
        if edit:
            if st.button("Cancelar edición"):
                st.session_state["edit_cliente"] = None
                st.rerun()

    st.markdown("---")

    # ── Búsqueda ──────────────────────────────────────────────────────────────
    buscar = st.text_input("🔍 Buscar cliente", placeholder="Nombre, teléfono...")
    df = clientes_df.copy()
    if buscar:
        mask = df.apply(lambda r: buscar.lower() in str(r).lower(), axis=1)
        df = df[mask]

    # ── Tabla de clientes ─────────────────────────────────────────────────────
    if len(df) == 0:
        st.info("No hay clientes. Agregá uno arriba.")
    else:
        for _, cl in df.iterrows():
            saldo = calcular_saldo_cliente(cl["id"], ventas_df, cobros_df, clientes_df)
            saldo_html = f'<span class="saldo-positivo">{fmt(saldo)}</span>' if saldo > 0 else f'<span class="saldo-cero">$0,00</span>'
            estado_tag = f'<span class="tag-verde">Activo</span>' if cl["estado"] == "Activo" else f'<span class="tag-gris">Inactivo</span>'

            col_info, col_acc = st.columns([5, 1])
            with col_info:
                st.markdown(f"""
                <div class="card">
                  <div style="display:flex;justify-content:space-between;align-items:flex-start">
                    <div>
                      <div style="font-family:'Syne',sans-serif;font-weight:700;font-size:1rem">{cl['nombre']}</div>
                      <div style="color:#888;font-size:13px;margin-top:3px">
                        {('📱 ' + cl['telefono']) if cl['telefono'] else ''}
                        {('  ✉️ ' + cl['email']) if cl['email'] else ''}
                      </div>
                    </div>
                    <div style="text-align:right">
                      <div style="font-size:12px;color:#888;margin-bottom:4px">Saldo pendiente</div>
                      {saldo_html}
                    </div>
                  </div>
                  <div style="margin-top:8px">{estado_tag}
                    <span style="font-size:12px;color:#555;margin-left:8px">Alta: {cl['fecha_alta']}</span>
                    {'<span style="font-size:12px;color:#888;margin-left:8px">Saldo inicial: ' + fmt(cl['saldo_inicial']) + '</span>' if float(cl['saldo_inicial']) > 0 else ''}
                  </div>
                </div>
                """, unsafe_allow_html=True)
            with col_acc:
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("✏️", key=f"edit_cl_{cl['id']}", help="Editar"):
                    st.session_state["edit_cliente"] = cl.to_dict()
                    st.rerun()
                if st.button("🗑️", key=f"del_cl_{cl['id']}", help="Eliminar"):
                    ws = get_ws("Clientes", [])
                    rows = ws.get_all_values()
                    for i, row in enumerate(rows[1:], start=2):
                        if row[0] == cl["id"]:
                            ws.delete_rows(i)
                            break
                    clear_cache()
                    st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# PRODUCTOS
# ══════════════════════════════════════════════════════════════════════════════
elif page == "Productos":
    st.markdown('<div class="page-title">Productos</div>', unsafe_allow_html=True)

    productos_df = load_productos()
    edit = st.session_state["edit_producto"]

    # ── Formulario ────────────────────────────────────────────────────────────
    with st.expander("➕ Nuevo producto" if not edit else f"✏️ Editando: {edit['nombre']}", expanded=edit is not None):
        with st.form("form_producto"):
            c1, c2, c3 = st.columns(3)
            with c1:
                nombre      = st.text_input("Nombre *", value=edit["nombre"] if edit else "")
                descripcion = st.text_input("Descripción", value=edit["descripcion"] if edit else "")
                categoria   = st.text_input("Categoría", value=edit["categoria"] if edit else "")
            with c2:
                talla       = st.text_input("Talla", value=edit["talla"] if edit else "")
                color       = st.text_input("Color", value=edit["color"] if edit else "")
            with c3:
                precio_costo = st.number_input("Precio costo ($)", min_value=0.0, value=float(edit["precio_costo"]) if edit else 0.0, step=100.0, format="%.2f")
                stock        = st.number_input("Stock", min_value=0, value=int(edit["stock"]) if edit else 0, step=1)

            submitted = st.form_submit_button("Guardar producto", type="primary")
            if submitted:
                if not nombre.strip():
                    st.error("El nombre es obligatorio.")
                else:
                    ws = get_ws("Productos", ["id","nombre","descripcion","categoria","talla","color","precio_costo","stock"])
                    if edit:
                        rows = ws.get_all_values()
                        for i, row in enumerate(rows[1:], start=2):
                            if row[0] == edit["id"]:
                                ws.update(f"A{i}:H{i}", [[edit["id"], nombre.strip(), descripcion, categoria, talla, color, precio_costo, stock]])
                                break
                        st.success(f"✓ Producto '{nombre}' actualizado.")
                        st.session_state["edit_producto"] = None
                    else:
                        ws.append_row([new_id(), nombre.strip(), descripcion, categoria, talla, color, precio_costo, stock])
                        st.success(f"✓ Producto '{nombre}' creado.")
                    clear_cache()
                    st.rerun()

        if edit:
            if st.button("Cancelar edición"):
                st.session_state["edit_producto"] = None
                st.rerun()

    st.markdown("---")

    # ── Filtros ───────────────────────────────────────────────────────────────
    col_b, col_c, col_s = st.columns(3)
    with col_b: buscar = st.text_input("🔍 Buscar", placeholder="Nombre, categoría...")
    with col_c:
        cats = ["Todas"] + sorted(productos_df["categoria"].unique().tolist()) if len(productos_df) > 0 else ["Todas"]
        cat_fil = st.selectbox("Categoría", cats)
    with col_s:
        stock_fil = st.selectbox("Stock", ["Todos", "Stock OK (>3)", "Stock bajo (≤3)", "Sin stock (0)"])

    df = productos_df.copy()
    if buscar:
        df = df[df.apply(lambda r: buscar.lower() in str(r).lower(), axis=1)]
    if cat_fil != "Todas":
        df = df[df["categoria"] == cat_fil]
    if stock_fil == "Stock OK (>3)":    df = df[df["stock"] > 3]
    elif stock_fil == "Stock bajo (≤3)": df = df[df["stock"] <= 3]
    elif stock_fil == "Sin stock (0)":   df = df[df["stock"] == 0]

    st.caption(f"{len(df)} productos")

    if len(df) == 0:
        st.info("No hay productos con esos filtros.")
    else:
        for _, pr in df.iterrows():
            stock_val = int(pr["stock"])
            if stock_val == 0:   stock_tag = f'<span class="tag-rojo">Sin stock</span>'
            elif stock_val <= 3: stock_tag = f'<span class="tag-amber">Stock bajo: {stock_val}</span>'
            else:                stock_tag = f'<span class="tag-verde">Stock: {stock_val}</span>'

            col_info, col_acc = st.columns([5, 1])
            with col_info:
                st.markdown(f"""
                <div class="card">
                  <div style="display:flex;justify-content:space-between;align-items:center">
                    <div>
                      <div style="font-family:'Syne',sans-serif;font-weight:700">{pr['nombre']}</div>
                      <div style="color:#888;font-size:13px;margin-top:3px">
                        {pr['descripcion']}
                        {(' · ' + pr['categoria']) if pr['categoria'] else ''}
                        {(' · Talla ' + pr['talla']) if pr['talla'] else ''}
                        {(' · ' + pr['color']) if pr['color'] else ''}
                      </div>
                    </div>
                    <div style="text-align:right">
                      <div style="font-size:12px;color:#888">Costo</div>
                      <div style="font-family:'Syne',sans-serif;color:#e8ff8b;font-weight:700">{fmt(pr['precio_costo'])}</div>
                    </div>
                  </div>
                  <div style="margin-top:8px">{stock_tag}</div>
                </div>
                """, unsafe_allow_html=True)
            with col_acc:
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("✏️", key=f"edit_pr_{pr['id']}"):
                    st.session_state["edit_producto"] = pr.to_dict()
                    st.rerun()
                if st.button("🗑️", key=f"del_pr_{pr['id']}"):
                    ws = get_ws("Productos", [])
                    rows = ws.get_all_values()
                    for i, row in enumerate(rows[1:], start=2):
                        if row[0] == pr["id"]:
                            ws.delete_rows(i)
                            break
                    clear_cache()
                    st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# VENTAS
# ══════════════════════════════════════════════════════════════════════════════
elif page == "Ventas":
    st.markdown('<div class="page-title">Ventas</div>', unsafe_allow_html=True)

    clientes_df  = load_clientes()
    productos_df = load_productos()
    ventas_df    = load_ventas()

    # ── Formulario nueva venta ────────────────────────────────────────────────
    with st.expander("➕ Registrar venta", expanded=False):
        with st.form("form_venta"):
            c1, c2 = st.columns(2)
            with c1:
                if len(clientes_df) == 0:
                    st.warning("Primero cargá clientes.")
                    st.stop()
                clientes_opts = clientes_df[clientes_df["estado"]=="Activo"]["nombre"].tolist()
                cliente_sel = st.selectbox("Cliente *", clientes_opts)

                if len(productos_df) == 0:
                    st.warning("Primero cargá productos.")
                    st.stop()
                prods_opts = productos_df[productos_df["stock"] > 0]["nombre"].tolist()
                if not prods_opts:
                    st.warning("No hay productos con stock disponible.")
                producto_sel = st.selectbox("Producto *", prods_opts if prods_opts else productos_df["nombre"].tolist())

            with c2:
                fecha_venta = st.date_input("Fecha *", value=date.today())
                cantidad    = st.number_input("Cantidad *", min_value=1, value=1, step=1)
                precio_venta = st.number_input("Precio de venta ($) *", min_value=0.0, value=0.0, step=100.0, format="%.2f")
                pagado = st.checkbox("✓ Pagado en el momento")

            submitted = st.form_submit_button("Registrar venta", type="primary")
            if submitted:
                if precio_venta <= 0:
                    st.error("Ingresá un precio de venta.")
                else:
                    cl_row = clientes_df[clientes_df["nombre"] == cliente_sel].iloc[0]
                    pr_row = productos_df[productos_df["nombre"] == producto_sel].iloc[0]
                    stock_actual = int(pr_row["stock"])

                    if cantidad > stock_actual:
                        st.error(f"Stock insuficiente. Disponible: {stock_actual}")
                    else:
                        total = round(float(cantidad) * float(precio_venta), 2)
                        # Guardar venta
                        ws_v = get_ws("Ventas", ["id","fecha","id_cliente","cliente","id_producto","producto","cantidad","precio_venta","total","pagado"])
                        ws_v.append_row([
                            new_id(),
                            fecha_venta.strftime("%d/%m/%Y"),
                            cl_row["id"], cliente_sel,
                            pr_row["id"], producto_sel,
                            cantidad, precio_venta, total,
                            "SI" if pagado else "NO"
                        ])
                        # Descontar stock
                        ws_p = get_ws("Productos", [])
                        rows_p = ws_p.get_all_values()
                        for i, row in enumerate(rows_p[1:], start=2):
                            if row[0] == pr_row["id"]:
                                ws_p.update_cell(i, 8, stock_actual - cantidad)
                                break
                        clear_cache()
                        st.success(f"✓ Venta registrada. Total: {fmt(total)}")
                        st.rerun()

    st.markdown("---")

    # ── Filtros ───────────────────────────────────────────────────────────────
    col_f1, col_f2, col_f3, col_f4 = st.columns(4)
    with col_f1:
        clientes_fil = ["Todos"] + sorted(ventas_df["cliente"].unique().tolist()) if len(ventas_df) > 0 else ["Todos"]
        cliente_f = st.selectbox("Cliente", clientes_fil)
    with col_f2:
        pagado_f = st.selectbox("Estado", ["Todos", "Pendientes", "Pagados"])
    with col_f3:
        desde_f = st.date_input("Desde", value=None, key="v_desde")
    with col_f4:
        hasta_f = st.date_input("Hasta", value=None, key="v_hasta")

    df = ventas_df.copy()
    if cliente_f != "Todos": df = df[df["cliente"] == cliente_f]
    if pagado_f == "Pendientes": df = df[df["pagado"].str.upper() != "SI"]
    elif pagado_f == "Pagados":  df = df[df["pagado"].str.upper() == "SI"]
    if desde_f:
        try:
            df = df[pd.to_datetime(df["fecha"], dayfirst=True) >= pd.Timestamp(desde_f)]
        except: pass
    if hasta_f:
        try:
            df = df[pd.to_datetime(df["fecha"], dayfirst=True) <= pd.Timestamp(hasta_f)]
        except: pass

    st.caption(f"{len(df)} ventas · Total: {fmt(df['total'].sum())}")

    if len(df) == 0:
        st.info("No hay ventas con esos filtros.")
    else:
        for _, v in df.sort_values("fecha", ascending=False).iterrows():
            pagado_tag = '<span class="tag-verde">Pagado</span>' if v["pagado"].upper() == "SI" else '<span class="tag-rojo">Pendiente</span>'
            col_info, col_acc = st.columns([5, 1])
            with col_info:
                st.markdown(f"""
                <div class="card">
                  <div style="display:flex;justify-content:space-between;align-items:center">
                    <div>
                      <div style="font-family:'Syne',sans-serif;font-weight:700">{v['cliente']}</div>
                      <div style="color:#888;font-size:13px;margin-top:2px">{v['producto']} · {int(float(v['cantidad']))} u · {fmt(v['precio_venta'])} c/u</div>
                    </div>
                    <div style="text-align:right">
                      <div style="font-family:'Syne',sans-serif;color:#e8ff8b;font-weight:700;font-size:1.1rem">{fmt(v['total'])}</div>
                      <div style="font-size:12px;color:#888">{v['fecha']}</div>
                    </div>
                  </div>
                  <div style="margin-top:8px">{pagado_tag}</div>
                </div>
                """, unsafe_allow_html=True)
            with col_acc:
                st.markdown("<br>", unsafe_allow_html=True)
                # Marcar como pagado
                if v["pagado"].upper() != "SI":
                    if st.button("✓", key=f"pag_{v['id']}", help="Marcar pagado"):
                        ws = get_ws("Ventas", [])
                        rows = ws.get_all_values()
                        for i, row in enumerate(rows[1:], start=2):
                            if row[0] == v["id"]:
                                ws.update_cell(i, 10, "SI")
                                break
                        clear_cache()
                        st.rerun()
                if st.button("🗑️", key=f"del_v_{v['id']}", help="Eliminar"):
                    # Devolver stock
                    pr_df = load_productos()
                    ws_p = get_ws("Productos", [])
                    rows_p = ws_p.get_all_values()
                    for i, row in enumerate(rows_p[1:], start=2):
                        if row[0] == v["id_producto"]:
                            stock_act = int(float(row[7]))
                            ws_p.update_cell(i, 8, stock_act + int(float(v["cantidad"])))
                            break
                    # Borrar venta
                    ws_v = get_ws("Ventas", [])
                    rows_v = ws_v.get_all_values()
                    for i, row in enumerate(rows_v[1:], start=2):
                        if row[0] == v["id"]:
                            ws_v.delete_rows(i)
                            break
                    clear_cache()
                    st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# COBROS
# ══════════════════════════════════════════════════════════════════════════════
elif page == "Cobros":
    st.markdown('<div class="page-title">Cobros</div>', unsafe_allow_html=True)

    clientes_df = load_clientes()
    ventas_df   = load_ventas()
    cobros_df   = load_cobros()

    # ── Resumen de deudores ───────────────────────────────────────────────────
    st.markdown("#### Estado de cuenta por cliente")

    if len(clientes_df) == 0:
        st.info("No hay clientes cargados.")
    else:
        deudores = []
        for _, cl in clientes_df[clientes_df["estado"]=="Activo"].iterrows():
            saldo = calcular_saldo_cliente(cl["id"], ventas_df, cobros_df, clientes_df)
            v_pend = ventas_df[(ventas_df["id_cliente"]==cl["id"]) & (ventas_df["pagado"].str.upper()!="SI")]
            c_clie = cobros_df[cobros_df["id_cliente"]==cl["id"]]
            deudores.append({
                "id": cl["id"],
                "nombre": cl["nombre"],
                "saldo_inicial": float(cl["saldo_inicial"]),
                "ventas_pendientes": v_pend["total"].sum(),
                "cobros_realizados": c_clie["monto"].sum(),
                "saldo": saldo
            })

        deudores_df = pd.DataFrame(deudores).sort_values("saldo", ascending=False)

        for _, d in deudores_df.iterrows():
            saldo_html = f'<span class="saldo-positivo">{fmt(d["saldo"])}</span>' if d["saldo"] > 0 else f'<span class="saldo-cero">Al día ✓</span>'

            with st.expander(f"👤 {d['nombre']}  —  Saldo: {fmt(d['saldo'])}"):
                col_det, col_cob = st.columns(2)
                with col_det:
                    st.markdown(f"""
                    <div style="font-size:13px;color:#888;line-height:2">
                      Saldo inicial: <strong style="color:#dea85d">{fmt(d['saldo_inicial'])}</strong><br>
                      Ventas pendientes: <strong style="color:#de5d5d">{fmt(d['ventas_pendientes'])}</strong><br>
                      Cobros realizados: <strong style="color:#5dde8a">{fmt(d['cobros_realizados'])}</strong><br>
                      <strong>Saldo total: {saldo_html}</strong>
                    </div>
                    """, unsafe_allow_html=True)

                with col_cob:
                    if d["saldo"] > 0:
                        st.markdown("**Registrar pago:**")
                        monto_cob = st.number_input("Monto ($)", min_value=0.0, value=0.0, step=100.0, format="%.2f", key=f"monto_{d['id']}")
                        fecha_cob = st.date_input("Fecha pago", value=date.today(), key=f"fecha_{d['id']}")
                        nota_cob  = st.text_input("Nota (opcional)", key=f"nota_{d['id']}")
                        if st.button("✓ Registrar cobro", key=f"cobrar_{d['id']}", type="primary"):
                            if monto_cob <= 0:
                                st.error("Ingresá un monto válido.")
                            else:
                                ws = get_ws("Cobros", ["id","fecha","id_cliente","cliente","monto","nota"])
                                ws.append_row([new_id(), fecha_cob.strftime("%d/%m/%Y"), d["id"], d["nombre"], monto_cob, nota_cob])
                                clear_cache()
                                st.success(f"✓ Cobro de {fmt(monto_cob)} registrado.")
                                st.rerun()

                # Historial de cobros del cliente
                hist = cobros_df[cobros_df["id_cliente"] == d["id"]].sort_values("fecha", ascending=False)
                if len(hist) > 0:
                    st.markdown("**Historial de cobros:**")
                    for _, cob in hist.iterrows():
                        st.markdown(f"""
                        <div style="font-size:13px;padding:6px 10px;background:#1a2a1a;border-radius:8px;margin-bottom:4px;display:flex;justify-content:space-between">
                          <span style="color:#888">{cob['fecha']} {('— ' + cob['nota']) if cob['nota'] else ''}</span>
                          <span style="color:#5dde8a;font-weight:600">{fmt(cob['monto'])}</span>
                        </div>
                        """, unsafe_allow_html=True)
                        col_del_c = st.columns([5,1])[1]
                        with col_del_c:
                            if st.button("✕", key=f"del_cob_{cob['id']}"):
                                ws = get_ws("Cobros", [])
                                rows = ws.get_all_values()
                                for i, row in enumerate(rows[1:], start=2):
                                    if row[0] == cob["id"]:
                                        ws.delete_rows(i)
                                        break
                                clear_cache()
                                st.rerun()

                # Ventas pendientes del cliente
                v_pend = ventas_df[(ventas_df["id_cliente"]==d["id"]) & (ventas_df["pagado"].str.upper()!="SI")]
                if len(v_pend) > 0:
                    st.markdown("**Ventas pendientes:**")
                    for _, vp in v_pend.sort_values("fecha", ascending=False).iterrows():
                        st.markdown(f"""
                        <div style="font-size:13px;padding:6px 10px;background:#2a1a1a;border-radius:8px;margin-bottom:4px;display:flex;justify-content:space-between">
                          <span style="color:#888">{vp['fecha']} — {vp['producto']} x{int(float(vp['cantidad']))}</span>
                          <span style="color:#de5d5d;font-weight:600">{fmt(vp['total'])}</span>
                        </div>
                        """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("#### 📋 Todos los cobros registrados")
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        cl_fil = ["Todos"] + sorted(cobros_df["cliente"].unique().tolist()) if len(cobros_df) > 0 else ["Todos"]
        cl_f = st.selectbox("Filtrar por cliente", cl_fil)
    with col_f2:
        desde_c = st.date_input("Desde", value=None, key="c_desde")

    df_c = cobros_df.copy()
    if cl_f != "Todos": df_c = df_c[df_c["cliente"] == cl_f]
    if desde_c:
        try: df_c = df_c[pd.to_datetime(df_c["fecha"], dayfirst=True) >= pd.Timestamp(desde_c)]
        except: pass

    if len(df_c) > 0:
        st.caption(f"{len(df_c)} cobros · Total: {fmt(df_c['monto'].sum())}")
        st.dataframe(df_c[["fecha","cliente","monto","nota"]].sort_values("fecha", ascending=False),
                     use_container_width=True, hide_index=True)
    else:
        st.info("Sin cobros registrados.")
