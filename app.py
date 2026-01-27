#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Aplicação Streamlit - Tamanho do Mercado
Dashboard interativo para análise estratégica de múltiplas categorias macro
"""

import streamlit as st
import pandas as pd
from datetime import datetime
import sys
import os
import json
import re
import io

# Adicionar pasta utils ao path
sys.path.append(os.path.join(os.path.dirname(__file__), 'utils'))

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
    page_title="Tamanho do Mercado",
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
    try:
        if pd.isna(val): return 0.0
        return float(val)
    except:
        return 0.0

# --- INICIALIZAÇÃO ---

# Garantir que o analyzer esteja sempre na sessão
if 'analyzer' not in st.session_state:
    st.session_state.analyzer = MarketAnalyzer()

# --- LÓGICA DE IMPORTAÇÃO EXCEL ---

def processar_excel(file):
    try:
        # Criar novo analyzer temporário
        temp_analyzer = MarketAnalyzer()
        
        # 1. Cliente
        df_cliente = pd.read_excel(file, sheet_name="Cliente", header=None)
        empresa = str(df_cliente.iloc[4, 1])
        cat_macro_cliente = str(df_cliente.iloc[5, 1])
        ticket_medio = safe_float(df_cliente.iloc[6, 1])
        margem = safe_float(df_cliente.iloc[7, 1])
        fat_3m = safe_float(df_cliente.iloc[8, 1])
        uni_3m = int(safe_float(df_cliente.iloc[9, 1]))
        range_p = safe_float(df_cliente.iloc[10, 1])
        ticket_c = df_cliente.iloc[11, 1]
        ticket_custom = safe_float(ticket_c) if pd.notna(ticket_c) and str(ticket_c).strip() != "" else None
        
        temp_analyzer.set_cliente_data(
            empresa=empresa, categoria=cat_macro_cliente, ticket_medio=ticket_medio,
            margem=margem, faturamento_3m=fat_3m, unidades_3m=uni_3m,
            range_permitido=range_p, ticket_custom=ticket_custom
        )
        
        # 2. Mercado Categoria
        df_cat = pd.read_excel(file, sheet_name="Mercado_Categoria", skiprows=2)
        count_cat = 0
        for _, row in df_cat.iterrows():
            if pd.notna(row['Categoria']) and pd.notna(row['Periodo (texto)']):
                temp_analyzer.add_mercado_categoria(
                    str(row['Categoria']), str(row['Periodo (texto)']), 
                    safe_float(row['Faturamento (R$)']), int(safe_float(row['Unidades']))
                )
                count_cat += 1
                
        # 3. Mercado Subcategoria
        df_sub = pd.read_excel(file, sheet_name="Mercado_Subcategoria", skiprows=2)
        count_sub = 0
        for _, row in df_sub.iterrows():
            if pd.notna(row['Categoria']) and pd.notna(row['Subcategoria']):
                temp_analyzer.add_mercado_subcategoria(
                    str(row['Categoria']), str(row['Subcategoria']), 
                    safe_float(row['Faturamento 6M (R$)']), int(safe_float(row['Unidades 6M']))
                )
                count_sub += 1
        
        # ATUALIZAÇÃO CRÍTICA: Substituir o objeto na sessão
        st.session_state.analyzer = temp_analyzer
        st.session_state['data_version'] = datetime.now().timestamp()
        st.session_state['last_upload_info'] = f"Empresa: {empresa} | Macros: {count_cat} | Subs: {count_sub}"
        return True
    except Exception as e:
        st.error(f"Erro no processamento: {str(e)}")
        return False

# --- CSS CUSTOMIZADO ---
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem; font-weight: bold; color: #FFFFFF; background-color: #1E1E1E;
        text-align: center; padding: 1.5rem; border-radius: 0.5rem; margin-bottom: 2rem; border-bottom: 4px solid #3498db;
    }
    .metric-card {
        background-color: #262730; padding: 1.2rem; border-radius: 0.5rem; border-top: 3px solid #3498db; text-align: center;
    }
    .metric-label { font-size: 0.85rem; color: #A0A0A0; margin-bottom: 0.3rem; }
    .metric-value { font-size: 1.2rem; font-weight: bold; color: #FFFFFF; }
</style>
""", unsafe_allow_html=True)

# --- SIDEBAR ---
with st.sidebar:
    st.markdown("### 🧭 Navegação")
    menu = st.radio("Escolha a seção:", ["🏠 Início", "👤 Dados do Cliente", "📈 Gestão de Categorias", "🎯 Mercado Subcategorias", "📊 Dashboard Executivo"])
    
    st.markdown("---")
    st.markdown("### 📤 Importar Dados")
    
    uploaded_file = st.file_uploader("Suba sua planilha Excel", type=["xlsx"], key="excel_uploader_v2")
    if uploaded_file is not None:
        if st.button("🚀 Processar Planilha", use_container_width=True):
            if processar_excel(uploaded_file):
                st.success("Dados carregados!")
                st.rerun()
    
    if 'last_upload_info' in st.session_state:
        st.info(st.session_state.last_upload_info)
    
    st.markdown("---")
    if st.button("🗑️ Limpar Tudo (Zerar)", use_container_width=True, type="secondary"):
        st.session_state.analyzer = MarketAnalyzer()
        if 'last_upload_info' in st.session_state: del st.session_state['last_upload_info']
        st.rerun()

# Header
st.markdown('<div class="main-header">📊 Tamanho do Mercado</div>', unsafe_allow_html=True)

# Referência curta para o analyzer da sessão
analyzer = st.session_state.analyzer

# ====================
# SEÇÃO: INÍCIO
# ====================
if menu == "🏠 Início":
    st.markdown("## 🎯 Bem-vindo")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        ### 🚀 Como usar?
        1. **Importe seu Excel**: Use o campo na barra lateral para subir sua planilha preenchida.
        2. **Ajuste Manual**: Se precisar, altere os dados nas abas de Cliente, Categorias ou Subcategorias.
        3. **Analise**: Vá para o Dashboard Executivo para ver o ranking e os cenários.
        """)
    with col2:
        st.info("💡 **Dica**: O sistema agora aceita o modelo de planilha que você já utiliza, facilitando a migração dos dados!")
        
    if not analyzer.cliente_data:
        st.warning("⚠️ Nenhum dado carregado. Suba uma planilha na barra lateral para começar.")
    else:
        st.success(f"✅ Dados carregados para: **{analyzer.cliente_data.get('empresa', 'Empresa')}**")

# ====================
# SEÇÃO: DADOS DO CLIENTE
# ====================
elif menu == "👤 Dados do Cliente":
    st.markdown("## 👤 Dados do Cliente")
    ver = st.session_state.get('data_version', 0)
    
    with st.form("form_cliente"):
        col1, col2 = st.columns(2)
        with col1:
            empresa = st.text_input("Nome da Empresa", value=analyzer.cliente_data.get('empresa', ''), key=f"emp_{ver}")
            ticket_medio = st.number_input("Ticket Médio Geral (R$)", min_value=0.0, value=float(analyzer.cliente_data.get('ticket_medio', 0.0)), format="%.2f", key=f"tm_{ver}")
            margem = st.number_input("Margem Atual (%)", min_value=0.0, max_value=100.0, value=float(analyzer.cliente_data.get('margem', 0.0) * 100), step=0.1, key=f"mg_{ver}")
        with col2:
            fat_val = analyzer.cliente_data.get('faturamento_3m', 0.0)
            fat_input = st.text_input("Faturamento Médio 3M (R$)", value=str(fat_val) if fat_val > 0 else "", key=f"fat_{ver}")
            uni_val = analyzer.cliente_data.get('unidades_3m', 0)
            uni_input = st.text_input("Unidades Médias 3M", value=str(uni_val) if uni_val > 0 else "", key=f"uni_{ver}")
            range_permitido = st.number_input("Range Permitido (±%)", min_value=0.0, max_value=100.0, value=float(analyzer.cliente_data.get('range_permitido', 0.20) * 100), key=f"rp_{ver}")
        
        if st.form_submit_button("💾 Salvar Dados"):
            analyzer.set_cliente_data(
                empresa=empresa, categoria="Geral", ticket_medio=ticket_medio,
                margem=margem, faturamento_3m=parse_large_number(fat_input), 
                unidades_3m=int(parse_large_number(uni_input)), range_permitido=range_permitido
            )
            st.toast("✅ Dados salvos!", icon="💾")
            st.rerun()

# ====================
# SEÇÃO: GESTÃO DE CATEGORIAS
# ====================
elif menu == "📈 Gestão de Categorias":
    st.markdown("## 📈 Categorias Macro")
    with st.expander("➕ Adicionar Nova Categoria Macro"):
        with st.form("nova_cat"):
            nova_cat = st.text_input("Nome da Categoria")
            col1, col2, col3 = st.columns(3)
            periodo = col1.text_input("Período (ex: Jan/24)")
            fat_cat = col2.text_input("Faturamento Mercado (R$)")
            uni_cat = col3.text_input("Unidades Mercado")
            if st.form_submit_button("Adicionar"):
                if nova_cat:
                    analyzer.add_mercado_categoria(nova_cat, periodo, parse_large_number(fat_cat), int(parse_large_number(uni_cat)))
                    st.rerun()

    if analyzer.mercado_categoria:
        for cat in analyzer.mercado_categoria.keys():
            df_cat = analyzer.get_mercado_categoria_df(cat).copy()
            if not df_cat.empty:
                df_cat['faturamento'] = df_cat['faturamento'].apply(format_br)
                df_cat['ticket_medio'] = df_cat['ticket_medio'].apply(format_br)
                st.write(f"**{cat}**")
                st.dataframe(df_cat, use_container_width=True)
    else:
        st.info("Nenhuma categoria macro cadastrada.")

# ====================
# SEÇÃO: SUBCATEGORIAS
# ====================
elif menu == "🎯 Mercado Subcategorias":
    st.markdown("## 🎯 Subcategorias")
    categorias = list(analyzer.mercado_categoria.keys())
    if not categorias:
        st.warning("Cadastre uma Categoria Macro primeiro!")
    else:
        cat_sel = st.selectbox("Selecione a Categoria Macro:", categorias)
        with st.form("nova_sub"):
            sub = st.text_input("Nome da Subcategoria")
            col1, col2 = st.columns(2)
            fat_6m = col1.text_input("Faturamento 6M (R$)")
            uni_6m = col2.text_input("Unidades 6M")
            if st.form_submit_button("Adicionar Subcategoria"):
                if sub:
                    analyzer.add_mercado_subcategoria(cat_sel, sub, parse_large_number(fat_6m), int(parse_large_number(uni_6m)))
                    st.rerun()
        
        if cat_sel in analyzer.mercado_subcategorias:
            df_sub = pd.DataFrame(analyzer.mercado_subcategorias[cat_sel]).copy()
            df_sub['faturamento_6m'] = df_sub['faturamento_6m'].apply(format_br)
            df_sub['ticket_medio'] = df_sub['ticket_medio'].apply(format_br)
            st.dataframe(df_sub, use_container_width=True)

# ====================
# SEÇÃO: DASHBOARD
# ====================
elif menu == "📊 Dashboard Executivo":
    st.markdown("## 📊 Dashboard Executivo")
    df_ranking = analyzer.gerar_ranking()
    if df_ranking.empty:
        st.info("Importe ou adicione dados para visualizar o dashboard.")
    else:
        col_rank1, col_rank2 = st.columns([1, 1])
        with col_rank1:
            st.markdown("### 🏆 Ranking")
            df_display = df_ranking[['Categoria Macro', 'Subcategoria', 'Score', 'Status']].copy()
            st.dataframe(df_display, use_container_width=True)
        with col_rank2:
            st.plotly_chart(criar_grafico_ranking_subcategorias(df_ranking), use_container_width=True)
            
        st.markdown("---")
        sub_foco = st.selectbox("Análise Detalhada:", df_ranking['Subcategoria'].tolist())
        row_foco = df_ranking[df_ranking['Subcategoria'] == sub_foco].iloc[0]
        res = analyzer.simular_cenarios(row_foco['Categoria Macro'], sub_foco)
        
        if res:
            m1, m2, m3, m4, m5 = st.columns(5)
            m1.markdown(f'<div class="metric-card"><div class="metric-label">Mercado 6M</div><div class="metric-value">R$ {format_br(res["mercado_6m"])}</div></div>', unsafe_allow_html=True)
            m2.markdown(f'<div class="metric-card"><div class="metric-label">Ticket Mercado</div><div class="metric-value">R$ {format_br(res["ticket_mercado"])}</div></div>', unsafe_allow_html=True)
            m3.markdown(f'<div class="metric-card"><div class="metric-label">Ticket Cliente</div><div class="metric-value">R$ {format_br(row_foco["Ticket Cliente"])}</div></div>', unsafe_allow_html=True)
            m4.markdown(f'<div class="metric-card"><div class="metric-label">Share Atual</div><div class="metric-value">{res["share_atual"]:.4f}%</div></div>', unsafe_allow_html=True)
            m5.markdown(f'<div class="metric-card"><div class="metric-label">Margem</div><div class="metric-value">{analyzer.cliente_data.get("margem", 0)*100:.1f}%</div></div>', unsafe_allow_html=True)
            
            g1, g2 = st.columns(2)
            with g1: st.plotly_chart(criar_gauge_score(row_foco['Score'], row_foco['Status']), use_container_width=True)
            with g2:
                l_inf, l_sup = analyzer.calcular_limites_ticket(res['ticket_mercado'])
                st.plotly_chart(criar_comparacao_tickets(res['ticket_mercado'], row_foco['Ticket Cliente'], l_inf, l_sup), use_container_width=True)
            
            st.markdown("#### 📈 Cenários")
            df_cen = res['cenarios'].copy()
            for col in ['Receita Projetada 6M', 'Lucro Projetado 6M', 'Delta vs Atual']:
                df_cen[col] = df_cen[col].apply(format_br)
            st.dataframe(df_cen, use_container_width=True)
