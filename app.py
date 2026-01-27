#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Aplicação Streamlit - Análise de Mercado Marketplace (Mercado Livre)
Dashboard interativo para análise estratégica de múltiplas categorias macro
"""

import streamlit as st
import pandas as pd
from datetime import datetime
import sys
import os
import json

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
    page_title="Análise de Mercado - Mercado Livre",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS customizado
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #FFE600;
        background-color: #2D3277;
        text-align: center;
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 2rem;
    }
    .sub-header {
        font-size: 1.5rem;
        font-weight: bold;
        color: #2D3277;
        margin-top: 2rem;
        margin-bottom: 1rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 5px solid #2D3277;
    }
</style>
""", unsafe_allow_html=True)

# Inicializar session state
if 'analyzer' not in st.session_state:
    st.session_state.analyzer = MarketAnalyzer()
    
    # Carregar dados iniciais se existirem
    if os.path.exists('initial_data.json'):
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
            
            # Carregar mercado categoria (agora com suporte a múltiplas)
            cat_nome = c.get('categoria', 'Geral')
            for item in initial_data.get('mercado_categoria', []):
                st.session_state.analyzer.add_mercado_categoria(
                    categoria=cat_nome,
                    periodo=item.get('periodo'),
                    faturamento=item.get('faturamento'),
                    unidades=item.get('unidades')
                )
                
            # Carregar subcategorias
            for item in initial_data.get('mercado_subcategorias', []):
                st.session_state.analyzer.add_mercado_subcategoria(
                    categoria=cat_nome,
                    subcategoria=item.get('subcategoria'),
                    faturamento_6m=item.get('faturamento_6m'),
                    unidades_6m=item.get('unidades_6m')
                )

if 'menu_index' not in st.session_state:
    st.session_state.menu_index = 0

# Header
st.markdown('<div class="main-header">📊 Análise de Mercado - Mercado Livre</div>', unsafe_allow_html=True)

# Sidebar - Navegação
with st.sidebar:
    st.markdown("### 🌐 Canal: Mercado Livre")
    st.info("Foco exclusivo em Mercado Livre ativado.")
    
    st.markdown("---")
    st.markdown("### 🧭 Navegação")
    
    menu = st.radio(
        "Escolha a seção:",
        ["🏠 Início", "👤 Dados do Cliente", "📈 Gestão de Categorias", "🎯 Mercado Subcategorias", 
         "📊 Dashboard Executivo"],
        index=st.session_state.menu_index
    )
    
    st.markdown("---")
    st.markdown("### 📋 Categorias Ativas")
    cats = list(st.session_state.analyzer.mercado_subcategorias.keys())
    if cats:
        for cat in cats:
            st.write(f"- {cat}")
    else:
        st.write("Nenhuma categoria cadastrada.")
    
    st.markdown("---")
    if st.button("🗑️ Limpar Todos os Dados", use_container_width=True):
        st.session_state.analyzer.clear_data()
        st.rerun()

# ====================
# SEÇÃO: INÍCIO
# ====================
if menu == "🏠 Início":
    st.markdown("## 🎯 Análise Estratégica Multi-Categoria")
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        ### 📖 O que mudou?
        Agora você pode cadastrar **múltiplas categorias macro** para o mesmo cliente.
        
        - ✅ **Visão Consolidada**: Analise o fit de ticket em diferentes frentes.
        - ✅ **Priorização Cruzada**: Compare subcategorias de diferentes macros.
        - ✅ **Foco Mercado Livre**: Lógica otimizada para o ecossistema Meli.
        """)
    
    with col2:
        st.success("""
        ### 🚀 Próximos Passos
        1. Revise os **Dados do Cliente**.
        2. Adicione ou edite **Categorias Macro**.
        3. Insira as **Subcategorias** de cada macro.
        4. Veja o ranking no **Dashboard Executivo**.
        """)

# ====================
# SEÇÃO: DADOS DO CLIENTE
# ====================
elif menu == "👤 Dados do Cliente":
    st.markdown("## 👤 Dados do Cliente")
    
    with st.form("form_cliente"):
        col1, col2 = st.columns(2)
        with col1:
            empresa = st.text_input("* Nome da Empresa", value=st.session_state.analyzer.cliente_data.get('empresa', ''))
            ticket_medio = st.number_input("Ticket Médio Geral (R$)", min_value=0.0, 
                                          value=float(st.session_state.analyzer.cliente_data.get('ticket_medio', 0.0)))
            margem = st.number_input("* Margem Atual (%)", min_value=0.0, max_value=100.0, 
                                    value=float(st.session_state.analyzer.cliente_data.get('margem', 0.0) * 100))
        
        with col2:
            faturamento_3m = st.number_input("* Faturamento Médio 3M (R$)", min_value=0.0,
                                            value=float(st.session_state.analyzer.cliente_data.get('faturamento_3m', 0.0)))
            unidades_3m = st.number_input("* Unidades Médias 3M", min_value=0,
                                         value=int(st.session_state.analyzer.cliente_data.get('unidades_3m', 0)))
            range_permitido = st.number_input("Range Permitido (±%)", min_value=0.0, max_value=100.0,
                                             value=float(st.session_state.analyzer.cliente_data.get('range_permitido', 0.20) * 100))
        
        submitted = st.form_submit_button("💾 Salvar Dados", use_container_width=True)
        if submitted:
            st.session_state.analyzer.set_cliente_data(
                empresa=empresa, categoria="Geral", ticket_medio=ticket_medio,
                margem=margem, faturamento_3m=faturamento_3m, unidades_3m=unidades_3m,
                range_permitido=range_permitido
            )
            st.success("Dados salvos!")

# ====================
# SEÇÃO: GESTÃO DE CATEGORIAS
# ====================
elif menu == "📈 Gestão de Categorias":
    st.markdown("## 📈 Gestão de Categorias Macro")
    
    with st.expander("➕ Adicionar Nova Categoria Macro"):
        with st.form("nova_cat"):
            nova_cat = st.text_input("Nome da Categoria (ex: Ferramentas, Eletrodomésticos)")
            col1, col2, col3 = st.columns(3)
            periodo = col1.text_input("Período (ex: Jan/24)")
            fat = col2.number_input("Faturamento Mercado (R$)", min_value=0.0)
            uni = col3.number_input("Unidades Mercado", min_value=0)
            
            if st.form_submit_button("Adicionar"):
                if nova_cat:
                    st.session_state.analyzer.add_mercado_categoria(nova_cat, periodo, fat, uni)
                    st.success(f"Categoria {nova_cat} adicionada!")
                    st.rerun()

    st.markdown("### Categorias Cadastradas")
    for cat in st.session_state.analyzer.mercado_categoria.keys():
        df_cat = st.session_state.analyzer.get_mercado_categoria_df(cat)
        st.write(f"**{cat}**")
        st.dataframe(df_cat, use_container_width=True)

# ====================
# SEÇÃO: SUBCATEGORIAS
# ====================
elif menu == "🎯 Mercado Subcategorias":
    st.markdown("## 🎯 Mercado Subcategorias")
    
    categorias = list(st.session_state.analyzer.mercado_categoria.keys())
    if not categorias:
        st.warning("Cadastre uma Categoria Macro primeiro!")
    else:
        cat_selecionada = st.selectbox("Selecione a Categoria Macro:", categorias)
        
        with st.form("nova_sub"):
            sub = st.text_input("Nome da Subcategoria")
            col1, col2 = st.columns(2)
            fat_6m = col1.number_input("Faturamento 6M (R$)", min_value=0.0)
            uni_6m = col2.number_input("Unidades 6M", min_value=0)
            
            if st.form_submit_button("Adicionar Subcategoria"):
                if sub:
                    st.session_state.analyzer.add_mercado_subcategoria(cat_selecionada, sub, fat_6m, uni_6m)
                    st.success(f"Subcategoria {sub} adicionada a {cat_selecionada}!")
                    st.rerun()
        
        if cat_selecionada in st.session_state.analyzer.mercado_subcategorias:
            st.markdown(f"### Subcategorias de {cat_selecionada}")
            df_sub = pd.DataFrame(st.session_state.analyzer.mercado_subcategorias[cat_selecionada])
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
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.markdown("### 🏆 Ranking Geral de Priorização")
            st.dataframe(df_ranking[['Categoria Macro', 'Subcategoria', 'Score', 'Status', 'Leitura']], 
                         use_container_width=True)
            
        with col2:
            fig_ranking = criar_grafico_ranking_subcategorias(df_ranking)
            st.plotly_chart(fig_ranking, use_container_width=True)
            
        st.markdown("---")
        st.markdown("### 🔍 Detalhes por Subcategoria")
        
        sub_foco = st.selectbox("Selecione uma subcategoria para análise detalhada:", 
                                df_ranking['Subcategoria'].tolist())
        
        # Encontrar a categoria da subcategoria selecionada
        cat_foco = df_ranking[df_ranking['Subcategoria'] == sub_foco]['Categoria Macro'].values[0]
        
        res = st.session_state.analyzer.simular_cenarios(cat_foco, sub_foco)
        
        if res:
            c1, c2, c3 = st.columns(3)
            c1.metric("Mercado 6M", f"R$ {res['mercado_6m']:,.2f}")
            c2.metric("Ticket Mercado", f"R$ {res['ticket_mercado']:,.2f}")
            c3.metric("Share Atual", f"{res['share_atual']:.4f}%")
            
            st.markdown("#### 📈 Cenários de Crescimento")
            st.dataframe(res['cenarios'], use_container_width=True)
            
            fig_cenarios = criar_grafico_cenarios(res['cenarios'])
            st.plotly_chart(fig_cenarios, use_container_width=True)
