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
    
    text = str(text).strip().upper().replace(".", "").replace(",", ".")
    
    multipliers = {
        'K': 1_000,
        'M': 1_000_000,
        'B': 1_000_000_000
    }
    
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

# --- CSS CUSTOMIZADO ---
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #FFFFFF;
        background-color: #1E1E1E;
        text-align: center;
        padding: 1.5rem;
        border-radius: 0.5rem;
        margin-bottom: 2rem;
        border-bottom: 4px solid #3498db;
    }
    .metric-card {
        background-color: #262730;
        padding: 1.2rem;
        border-radius: 0.5rem;
        border-top: 3px solid #3498db;
        text-align: center;
    }
    .metric-label { font-size: 0.85rem; color: #A0A0A0; margin-bottom: 0.3rem; }
    .metric-value { font-size: 1.2rem; font-weight: bold; color: #FFFFFF; }
    .stNumberInput div[data-baseweb="input"] { background-color: #1E1E1E; }
</style>
""", unsafe_allow_html=True)

# --- INICIALIZAÇÃO ---

if 'analyzer' not in st.session_state or not hasattr(st.session_state.analyzer, 'calcular_limites_ticket'):
    st.session_state.analyzer = MarketAnalyzer()
    st.session_state.data_loaded = False

# Função para carregar dados do template
def carregar_template():
    if os.path.exists('initial_data.json'):
        try:
            with open('initial_data.json', 'r', encoding='utf-8') as f:
                initial_data = json.load(f)
                c = initial_data.get('cliente', {})
                if c:
                    st.session_state.analyzer.set_cliente_data(
                        empresa=c.get('empresa', ''),
                        categoria=c.get('categoria', ''),
                        ticket_medio=c.get('ticket_medio', 0),
                        margem=c.get('margem', 0) * 100,
                        faturamento_3m=c.get('faturamento_3m', 0),
                        unidades_3m=c.get('unidades_3m', 0),
                        range_permitido=c.get('range_permitido', 20),
                        ticket_custom=c.get('ticket_custom')
                    )
                cat_nome = c.get('categoria', 'Geral')
                for item in initial_data.get('mercado_categoria', []):
                    st.session_state.analyzer.add_mercado_categoria(cat_nome, item.get('periodo'), item.get('faturamento'), item.get('unidades'))
                for item in initial_data.get('mercado_subcategorias', []):
                    st.session_state.analyzer.add_mercado_subcategoria(cat_nome, item.get('subcategoria'), item.get('faturamento_6m'), item.get('unidades_6m'))
            st.session_state.data_loaded = True
            st.success("Dados do template carregados!")
        except Exception as e:
            st.error(f"Erro ao carregar template: {e}")

# --- SIDEBAR ---
with st.sidebar:
    st.markdown("### 🧭 Navegação")
    menu = st.radio("Escolha a seção:", ["🏠 Início", "👤 Dados do Cliente", "📈 Gestão de Categorias", "🎯 Mercado Subcategorias", "📊 Dashboard Executivo"])
    
    st.markdown("---")
    st.markdown("### 🛠️ Gestão de Dados")
    if st.button("📥 Carregar Dados Exemplo", use_container_width=True):
        carregar_template()
        st.rerun()
    
    if st.button("🗑️ Limpar Tudo (Zerar)", use_container_width=True, type="secondary"):
        st.session_state.analyzer = MarketAnalyzer()
        st.session_state.data_loaded = False
        st.warning("Todos os dados foram limpos!")
        st.rerun()

# Header
st.markdown('<div class="main-header">📊 Tamanho do Mercado</div>', unsafe_allow_html=True)

# ====================
# SEÇÃO: INÍCIO
# ====================
if menu == "🏠 Início":
    st.markdown("## 🎯 Bem-vindo")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        ### 🚀 Como começar?
        1. **Comece do Zero**: Use o botão 'Limpar Tudo' na lateral.
        2. **Dados do Cliente**: Insira o faturamento e margem atual.
        3. **Categorias**: Adicione as categorias macro que deseja analisar.
        4. **Subcategorias**: Insira os dados de mercado (use K para mil, M para milhão).
        """)
    with col2:
        st.info("💡 **Dica de Preenchimento**: Nos campos de faturamento, você pode digitar valores como '1.5M' ou '500K' para facilitar!")

# ====================
# SEÇÃO: DADOS DO CLIENTE
# ====================
elif menu == "👤 Dados do Cliente":
    st.markdown("## 👤 Dados do Cliente")
    with st.form("form_cliente"):
        col1, col2 = st.columns(2)
        with col1:
            empresa = st.text_input("Nome da Empresa", value=st.session_state.analyzer.cliente_data.get('empresa', ''))
            ticket_medio = st.number_input("Ticket Médio Geral (R$)", min_value=0.0, value=float(st.session_state.analyzer.cliente_data.get('ticket_medio', 0.0)), format="%.2f")
            margem = st.number_input("Margem Atual (%)", min_value=0.0, max_value=100.0, value=float(st.session_state.analyzer.cliente_data.get('margem', 0.0) * 100), step=0.1)
        with col2:
            fat_input = st.text_input("Faturamento Médio 3M (R$)", value=str(st.session_state.analyzer.cliente_data.get('faturamento_3m', 0.0)))
            uni_input = st.text_input("Unidades Médias 3M", value=str(st.session_state.analyzer.cliente_data.get('unidades_3m', 0)))
            range_permitido = st.number_input("Range Permitido (±%)", min_value=0.0, max_value=100.0, value=float(st.session_state.analyzer.cliente_data.get('range_permitido', 0.20) * 100))
        
        if st.form_submit_button("💾 Salvar Dados"):
            st.session_state.analyzer.set_cliente_data(
                empresa=empresa, categoria="Geral", ticket_medio=ticket_medio,
                margem=margem, faturamento_3m=parse_large_number(fat_input), 
                unidades_3m=int(parse_large_number(uni_input)), range_permitido=range_permitido
            )
            st.success(f"Dados salvos! Faturamento processado: R$ {format_br(st.session_state.analyzer.cliente_data['faturamento_3m'])}")

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
                    st.session_state.analyzer.add_mercado_categoria(nova_cat, periodo, parse_large_number(fat_cat), int(parse_large_number(uni_cat)))
                    st.success(f"Categoria {nova_cat} adicionada!")
                    st.rerun()

    for cat in st.session_state.analyzer.mercado_categoria.keys():
        df_cat = st.session_state.analyzer.get_mercado_categoria_df(cat).copy()
        if not df_cat.empty:
            df_cat['faturamento'] = df_cat['faturamento'].apply(format_br)
            st.write(f"**{cat}**")
            st.dataframe(df_cat, use_container_width=True)

# ====================
# SEÇÃO: SUBCATEGORIAS
# ====================
elif menu == "🎯 Mercado Subcategorias":
    st.markdown("## 🎯 Subcategorias")
    categorias = list(st.session_state.analyzer.mercado_categoria.keys())
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
                    st.session_state.analyzer.add_mercado_subcategoria(cat_sel, sub, parse_large_number(fat_6m), int(parse_large_number(uni_6m)))
                    st.success(f"Subcategoria {sub} adicionada!")
                    st.rerun()
        
        if cat_sel in st.session_state.analyzer.mercado_subcategorias:
            df_sub = pd.DataFrame(st.session_state.analyzer.mercado_subcategorias[cat_sel]).copy()
            df_sub['faturamento_6m'] = df_sub['faturamento_6m'].apply(format_br)
            st.dataframe(df_sub, use_container_width=True)

# ====================
# SEÇÃO: DASHBOARD
# ====================
elif menu == "📊 Dashboard Executivo":
    st.markdown("## 📊 Dashboard Executivo")
    df_ranking = st.session_state.analyzer.gerar_ranking()
    if df_ranking.empty:
        st.info("Adicione dados para visualizar o dashboard.")
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
        res = st.session_state.analyzer.simular_cenarios(row_foco['Categoria Macro'], sub_foco)
        
        if res:
            m1, m2, m3, m4, m5 = st.columns(5)
            m1.markdown(f'<div class="metric-card"><div class="metric-label">Mercado 6M</div><div class="metric-value">R$ {format_br(res["mercado_6m"])}</div></div>', unsafe_allow_html=True)
            m2.markdown(f'<div class="metric-card"><div class="metric-label">Ticket Mercado</div><div class="metric-value">R$ {format_br(res["ticket_mercado"])}</div></div>', unsafe_allow_html=True)
            m3.markdown(f'<div class="metric-card"><div class="metric-label">Ticket Cliente</div><div class="metric-value">R$ {format_br(row_foco["Ticket Cliente"])}</div></div>', unsafe_allow_html=True)
            m4.markdown(f'<div class="metric-card"><div class="metric-label">Share Atual</div><div class="metric-value">{res["share_atual"]:.4f}%</div></div>', unsafe_allow_html=True)
            m5.markdown(f'<div class="metric-card"><div class="metric-label">Margem</div><div class="metric-value">{st.session_state.analyzer.cliente_data.get("margem", 0)*100:.1f}%</div></div>', unsafe_allow_html=True)
            
            g1, g2 = st.columns(2)
            with g1: st.plotly_chart(criar_gauge_score(row_foco['Score'], row_foco['Status']), use_container_width=True)
            with g2:
                l_inf, l_sup = st.session_state.analyzer.calcular_limites_ticket(res['ticket_mercado'])
                st.plotly_chart(criar_comparacao_tickets(res['ticket_mercado'], row_foco['Ticket Cliente'], l_inf, l_sup), use_container_width=True)
            
            st.markdown("#### 📈 Cenários")
            df_cen = res['cenarios'].copy()
            for col in ['Receita Projetada 6M', 'Lucro Projetado 6M', 'Delta vs Atual']:
                df_cen[col] = df_cen[col].apply(format_br)
            st.dataframe(df_cen, use_container_width=True)
