#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Aplicação Streamlit - Tamanho do Mercado
Dashboard interativo para análise estratégica de múltiplas categorias macro
Layout Modernizado - Versão Dark Theme
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import sys
import os
import json
import re
import io
sys.path.append(os.path.join(os.path.dirname(__file__), 'utils'))
from utils.pdf_generator import PDFReportGenerator

from utils.market_analyzer import MarketAnalyzer
from utils.visualizations import (
    criar_grafico_evolucao_categoria,
    criar_grafico_ticket_medio,
    criar_grafico_ranking_subcategorias,
    criar_grafico_mercado_subcategorias,
    criar_grafico_cenarios,
    criar_grafico_crescimento,
    criar_gauge_score,
    criar_comparacao_tickets
)

# Configuração da página
st.set_page_config(
    page_title="Inteligência de Mercado",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- FUNÇÕES UTILITÁRIAS ---

def format_br(valor):
    """Formata números para o padrão brasileiro (1.234,56)"""
    if valor is None: return "0,00"
    try:
        return f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except:
        return str(valor)

def parse_large_number(text):
    """Converte strings como '1.5M' ou '500k' em números reais"""
    if isinstance(text, (int, float)):
        return float(text)
    
    text = str(text).strip().upper()
    if "," in text and "." in text:
        text = text.replace(".", "").replace(",", ".")
    elif "," in text:
        text = text.replace(",", ".")
    
    multipliers = {'K': 1_000, 'M': 1_000_000, 'B': 1_000_000_000}
    match = re.match(r"([\d.]+)([KMB]?)", text)
    if match:
        value, unit = match.groups()
        try:
            num = float(value)
            if unit in multipliers:
                num *= multipliers[unit]
            return num
        except ValueError:
            return 0.0
    return 0.0

def safe_float(val):
    if pd.isna(val): return 0.0
    if isinstance(val, (int, float)): return float(val)
    try:
        # Remove R$, pontos de milhar e troca vírgula por ponto
        s = str(val).replace('R$', '').replace('$', '').strip()
        if not s: return 0.0
        # Lógica para formato brasileiro: 1.234,56 -> 1234.56
        if ',' in s and '.' in s:
            if s.rfind(',') > s.rfind('.'): # 1.234,56
                s = s.replace('.', '').replace(',', '.')
            else: # 1,234.56
                s = s.replace(',', '')
        elif ',' in s:
            s = s.replace(',', '.')
        return float(s)
    except:
        return 0.0

def calcular_limites_ticket_local(ticket_mercado, range_permitido=0.20):
    """Calcula limites inferior e superior baseado no ticket do mercado"""
    if not ticket_mercado: return 0.0, 0.0
    inf = ticket_mercado * (1 - range_permitido)
    sup = ticket_mercado * (1 + range_permitido)
    return inf, sup

def criar_metric_card(icon_svg, label, value, border_color="#1E3A8A"):
    """Cria um card de métrica estilizado com ícone circular"""
    return f"""
    <div style="
        background: #0a0a0a;
        border: 1px solid #1a1a1a;
        border-radius: 16px;
        padding: 24px 20px;
        text-align: left;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.5);
        height: 100%;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    ">
        <div style="
            width: 45px;
            height: 45px;
            background: #1a1a1a;
            border: 1px solid #333;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            margin-bottom: 20px;
        ">
            {icon_svg}
        </div>
        <div>
            <div style="
                font-size: 0.7rem;
                color: #FFFFFF;
                text-transform: uppercase;
                letter-spacing: 1.5px;
                margin-bottom: 8px;
                font-weight: 600;
                opacity: 0.8;
            ">{label}</div>
            <div style="
                font-size: 1.5rem;
                color: #FFFFFF;
                font-weight: 700;
            ">{value}</div>
        </div>
    </div>
    """

# Ícones SVG Estilizados
SVG_ICONS = {
    "box": '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#FFFFFF" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16Z"></path><path d="m3.3 7 8.7 5 8.7-5"></path><path d="M12 22V12"></path></svg>',
    "dollar": '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#FFFFFF" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="1" x2="12" y2="23"></line><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"></path></svg>',
    "chart": '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#FFFFFF" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="20" x2="18" y2="10"></line><line x1="12" y1="20" x2="12" y2="4"></line><line x1="6" y1="20" x2="6" y2="14"></line></svg>',
    "target": '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#FFFFFF" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><circle cx="12" cy="12" r="6"></circle><circle cx="12" cy="12" r="2"></circle></svg>',
    "user": '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#FFFFFF" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle></svg>',
    "file": '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#FFFFFF" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line><polyline points="10 9 9 9 8 9"></polyline></svg>'
}

# --- INICIALIZAÇÃO ---

# Garantir que o analyzer esteja sempre na sessão e atualizado
if 'analyzer' not in st.session_state:
    st.session_state.analyzer = MarketAnalyzer()

# --- LÓGICA DE IMPORTAÇÃO EXCEL ---

def processar_excel(file):
    try:
        temp_analyzer = MarketAnalyzer()
        
        # 1. Cliente
        df_cliente = pd.read_excel(file, sheet_name="Cliente", header=None)
        
        def get_val_by_label(labels, default=""):
            if isinstance(labels, str): labels = [labels]
            for i in range(len(df_cliente)):
                cell_val = str(df_cliente.iloc[i, 0]).strip().lower()
                for label in labels:
                    if label.lower() in cell_val:
                        return df_cliente.iloc[i, 1]
            return default

        empresa = str(get_val_by_label(["Empresa", "Nome"], "Empresa Exemplo"))
        cat_macro_cliente = str(get_val_by_label(["Categoria Macro", "Macro", "Categoria"], "Geral"))
        ticket_medio = safe_float(get_val_by_label(["Ticket Médio Geral", "Ticket Médio"], 0))
        margem = safe_float(get_val_by_label(["Margem Atual", "Margem"], 0))
        fat_3m = safe_float(get_val_by_label(["Faturamento Médio 3M", "Faturamento"], 0))
        uni_3m = int(safe_float(get_val_by_label(["Unidades Médias 3M", "Unidades"], 0)))
        range_p = safe_float(get_val_by_label(["Range Permitido", "Range"], 0.20))
        ticket_c = get_val_by_label(["Ticket Customizado", "Customizado"], None)
        ticket_custom = safe_float(ticket_c) if pd.notna(ticket_c) and str(ticket_c).strip() != "" else None
        
        temp_analyzer.set_cliente_data(
            empresa=empresa, categoria=cat_macro_cliente, ticket_medio=ticket_medio,
            margem=margem, faturamento_3m=fat_3m, unidades_3m=uni_3m,
            range_permitido=range_p, ticket_custom=ticket_custom
        )
        
        # 2. Mercado Categoria
        df_cat = pd.read_excel(file, sheet_name="Mercado_Categoria", skiprows=2)
        
        def find_col(df, possible_names):
            for col in df.columns:
                if any(name.lower() == str(col).lower().strip() for name in possible_names):
                    return col
            for col in df.columns:
                if any(name.lower() in str(col).lower() for name in possible_names):
                    return col
            return None

        col_cat = find_col(df_cat, ["Categoria"])
        col_per = find_col(df_cat, ["Periodo", "Período"])
        col_fat = find_col(df_cat, ["Faturamento"])
        col_uni = find_col(df_cat, ["Unidades"])

        count_cat = 0
        if col_cat and col_per:
            for _, row in df_cat.iterrows():
                if pd.notna(row[col_cat]) and pd.notna(row[col_per]):
                    cat_val = str(row[col_cat]).strip()
                    raw_per = row[col_per]
                    per_val = raw_per.strftime('%d/%m/%Y') if isinstance(raw_per, datetime) else str(raw_per).strip()
                    fat_val = safe_float(row[col_fat]) if col_fat and col_fat in row else 0.0
                    uni_val = int(safe_float(row[col_uni])) if col_uni and col_uni in row else 0
                    if cat_val and per_val:
                        temp_analyzer.add_mercado_categoria(cat_val, per_val, fat_val, uni_val)
                        count_cat += 1
                
        # 3. Mercado Subcategoria (SUPORTE MENSAL)
        df_sub = pd.read_excel(file, sheet_name="Mercado_Subcategoria", skiprows=2)
        
        col_sub_cat = find_col(df_sub, ["Categoria"])
        col_sub_name = find_col(df_sub, ["Subcategoria"])
        col_sub_per = find_col(df_sub, ["Periodo", "Período"])
        col_sub_fat = find_col(df_sub, ["Faturamento"])
        col_sub_uni = find_col(df_sub, ["Unidades"])

        count_sub = 0
        if col_sub_cat and col_sub_name:
            for _, row in df_sub.iterrows():
                if pd.notna(row[col_sub_cat]) and pd.notna(row[col_sub_name]):
                    raw_per = row[col_sub_per] if col_sub_per and col_sub_per in row and pd.notna(row[col_sub_per]) else "Consolidado 6M"
                    per_val = raw_per.strftime('%d/%m/%Y') if isinstance(raw_per, datetime) else str(raw_per).strip()
                    
                    temp_analyzer.add_mercado_subcategoria(
                        str(row[col_sub_cat]), str(row[col_sub_name]), per_val,
                        safe_float(row[col_sub_fat]) if col_sub_fat and col_sub_fat in row else 0.0, 
                        int(safe_float(row[col_sub_uni])) if col_sub_uni and col_sub_uni in row else 0
                    )
                    count_sub += 1
        
        st.session_state.analyzer = temp_analyzer
        st.session_state['last_upload_info'] = f"✅ **{empresa}** importada com sucesso! ({count_cat} categorias, {count_sub} subcategorias)"
        return True
    except Exception as e:
        st.error(f"❌ Erro no processamento: {str(e)}")
        return False

# --- CSS CUSTOMIZADO DARK THEME ---
st.markdown("""
<style>
    .stApp { background-color: #000000 !important; }
    :root { --accent-blue: #1E3A8A; --accent-blue-hover: #1e40af; }
    .stTabs [data-baseweb="tab-list"] { gap: 8px; background-color: transparent; }
    .stTabs [data-baseweb="tab"] {
        height: 50px; background-color: #0a0a0a;
        border-radius: 8px 8px 0px 0px; color: #666;
        border: 1px solid #1a1a1a; padding: 10px 20px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #1a1a1a !important; color: #FFFFFF !important;
        border-bottom: 2px solid var(--accent-blue) !important;
    }
</style>
""", unsafe_allow_html=True)

# --- UI PRINCIPAL ---

def main():
    # Sidebar
    with st.sidebar:
        st.title("📊 Market Intelligence")
        st.markdown("---")
        
        with st.form("upload_form"):
            uploaded_file = st.file_uploader("Arraste sua planilha Excel aqui", type=["xlsx"])
            submit_button = st.form_submit_button("Processar Planilha")
            if submit_button and uploaded_file:
                if processar_excel(uploaded_file):
                    st.success("Planilha processada!")
        
        if 'last_upload_info' in st.session_state:
            st.info(st.session_state['last_upload_info'])

    # Dashboard Principal
    if not st.session_state.analyzer.cliente_data.get('empresa'):
        st.title("Bem-vindo ao Market Intelligence")
        st.info("Por favor, faça o upload de uma planilha Excel para começar a análise.")
        return

    analyzer = st.session_state.analyzer
    st.title(f"Dashboard: {analyzer.cliente_data['empresa']}")
    
    # Layout Original de Tabs
    tab1, tab2, tab3 = st.tabs(["📈 Dashboard de Oportunidades", "📊 Gestão de Categorias", "📝 Relatórios"])

    with tab1:
        # Layout Original de Cards
        col1, col2, col3, col4 = st.columns(4)
        with col1: st.markdown(criar_metric_card(SVG_ICONS["dollar"], "Faturamento 3M", f"R$ {format_br(analyzer.cliente_data['faturamento_3m'])}"), unsafe_allow_html=True)
        with col2: st.markdown(criar_metric_card(SVG_ICONS["box"], "Unidades 3M", f"{analyzer.cliente_data['unidades_3m']:,}".replace(",", ".")), unsafe_allow_html=True)
        with col3: st.markdown(criar_metric_card(SVG_ICONS["target"], "Ticket Médio", f"R$ {format_br(analyzer.cliente_data.get('ticket_custom') or analyzer.cliente_data['ticket_medio'])}"), unsafe_allow_html=True)
        with col4: st.markdown(criar_metric_card(SVG_ICONS["chart"], "Margem", f"{analyzer.cliente_data['margem']*100:.1f}%"), unsafe_allow_html=True)

        st.markdown("### 🎯 Priorização de Subcategorias (6 Meses)")
        df_ranking = analyzer.gerar_ranking()
        if not df_ranking.empty:
            col_rank, col_chart = st.columns([1, 1])
            with col_rank: st.dataframe(df_ranking[['Subcategoria', 'Status', 'Score', 'Mercado (R$)']], use_container_width=True)
            with col_chart: st.plotly_chart(criar_grafico_ranking_subcategorias(df_ranking), use_container_width=True, key="dash_rank")
        
        # Adição discreta da evolução mensal (Nova funcionalidade integrada ao layout antigo)
        if analyzer.mercado_subcategorias:
            with st.expander("📉 Ver Evolução Mensal Detalhada"):
                all_subs = []
                for cat in analyzer.mercado_subcategorias:
                    for sub in analyzer.mercado_subcategorias[cat]:
                        all_subs.append(f"{cat} | {sub}")
                
                sel_sub_full = st.selectbox("Selecione a subcategoria:", all_subs, key="evol_sel")
                if sel_sub_full:
                    cat_sel, sub_sel = sel_sub_full.split(" | ")
                    hist = analyzer.mercado_subcategorias[cat_sel][sub_sel]
                    df_hist = pd.DataFrame(hist)
                    if len(df_hist) > 1:
                        st.plotly_chart(px.line(df_hist, x="periodo", y="faturamento", title=f"Tendência: {sub_sel}"), use_container_width=True, key="dash_evol")

    with tab2:
        st.header("📊 Gestão e Evolução de Categorias")
        cats = list(analyzer.mercado_categoria.keys())
        if cats:
            for cat in cats:
                with st.expander(f"Evolução: {cat}", expanded=True):
                    df_c = pd.DataFrame(analyzer.mercado_categoria[cat])
                    st.plotly_chart(criar_grafico_evolucao_categoria(df_c), use_container_width=True, key=f"evol_{cat}")

    with tab3:
        st.header("📝 Relatórios e Exportação")
        if st.button("Gerar Relatório PDF"):
            st.info("Funcionalidade de PDF disponível na versão completa.")

if __name__ == "__main__":
    main()
