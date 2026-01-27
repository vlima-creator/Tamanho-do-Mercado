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

# CSS customizado
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
    .sub-header {
        font-size: 1.5rem;
        font-weight: bold;
        color: #3498db;
        margin-top: 2rem;
        margin-bottom: 1rem;
    }
    .metric-card {
        background-color: #262730;
        padding: 1.5rem;
        border-radius: 0.5rem;
        border-top: 3px solid #3498db;
        text-align: center;
    }
    .metric-label {
        font-size: 0.9rem;
        color: #A0A0A0;
        margin-bottom: 0.5rem;
    }
    .metric-value {
        font-size: 1.4rem;
        font-weight: bold;
        color: #FFFFFF;
    }
</style>
""", unsafe_allow_html=True)

# Inicializar session state com verificação de compatibilidade
if 'analyzer' not in st.session_state or not hasattr(st.session_state.analyzer, 'mercado_subcategorias') or not isinstance(st.session_state.analyzer.mercado_subcategorias, dict):
    st.session_state.analyzer = MarketAnalyzer()
    
    # Carregar dados iniciais se existirem
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
                
                # Carregar mercado categoria
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
        except Exception as e:
            st.error(f"Erro ao carregar dados iniciais: {e}")

if 'menu_index' not in st.session_state:
    st.session_state.menu_index = 0

# Header
st.markdown('<div class="main-header">📊 Tamanho do Mercado</div>', unsafe_allow_html=True)

# Sidebar - Navegação
with st.sidebar:
    st.markdown("### 🧭 Navegação")
    
    menu = st.radio(
        "Escolha a seção:",
        ["🏠 Início", "👤 Dados do Cliente", "📈 Gestão de Categorias", "🎯 Mercado Subcategorias", 
         "📊 Dashboard Executivo"],
        index=st.session_state.menu_index
    )
    
    st.markdown("---")
    st.markdown("### 📋 Categorias Ativas")
    
    if hasattr(st.session_state.analyzer, 'mercado_subcategorias') and isinstance(st.session_state.analyzer.mercado_subcategorias, dict):
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
        ### 📖 O que é esta ferramenta?
        Esta aplicação ajuda você a tomar decisões estratégicas sobre **em qual categoria/subcategoria focar**, baseado em:
        
        - ✅ **Tamanho de mercado** (volume de faturamento)
        - ✅ **Fit de ticket** (alinhamento de preço cliente vs mercado)
        - ✅ **Potencial de crescimento** (simulação de cenários)
        - ✅ **Análise de lucratividade** (projeção de lucro)
        """)
    
    with col2:
        st.success("""
        ### 🚀 Como usar?
        1. Revise os **Dados do Cliente**.
        2. Adicione ou edite **Categorias Macro**.
        3. Insira as **Subcategorias** de cada macro.
        4. Veja o ranking e indicadores no **Dashboard Executivo**.
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
        # 1. Ranking Geral
        col_rank1, col_rank2 = st.columns([1, 1])
        with col_rank1:
            st.markdown("### 🏆 Ranking de Priorização")
            st.dataframe(df_ranking[['Categoria Macro', 'Subcategoria', 'Score', 'Status', 'Leitura']], 
                         use_container_width=True)
        with col_rank2:
            fig_ranking = criar_grafico_ranking_subcategorias(df_ranking)
            st.plotly_chart(fig_ranking, use_container_width=True)
            
        st.markdown("---")
        
        # 2. Indicadores Detalhados
        st.markdown("### 🔍 Indicadores Principais")
        sub_foco = st.selectbox("Selecione uma subcategoria para análise detalhada:", 
                                df_ranking['Subcategoria'].tolist())
        
        # Dados da subcategoria selecionada
        row_foco = df_ranking[df_ranking['Subcategoria'] == sub_foco].iloc[0]
        cat_foco = row_foco['Categoria Macro']
        res = st.session_state.analyzer.simular_cenarios(cat_foco, sub_foco)
        
        if res:
            # Cards de métricas
            m1, m2, m3, m4, m5 = st.columns(5)
            with m1:
                st.markdown(f'<div class="metric-card"><div class="metric-label">Mercado 6M</div><div class="metric-value">R$ {res["mercado_6m"]:,.0f}</div></div>', unsafe_allow_html=True)
            with m2:
                st.markdown(f'<div class="metric-card"><div class="metric-label">Ticket Mercado</div><div class="metric-value">R$ {res["ticket_mercado"]:,.2f}</div></div>', unsafe_allow_html=True)
            with m3:
                st.markdown(f'<div class="metric-card"><div class="metric-label">Ticket Cliente</div><div class="metric-value">R$ {row_foco["Ticket Cliente"]:,.2f}</div></div>', unsafe_allow_html=True)
            with m4:
                st.markdown(f'<div class="metric-card"><div class="metric-label">Share Atual</div><div class="metric-value">{res["share_atual"]:.4f}%</div></div>', unsafe_allow_html=True)
            with m5:
                st.markdown(f'<div class="metric-card"><div class="metric-label">Margem</div><div class="metric-value">{st.session_state.analyzer.cliente_data.get("margem", 0)*100:.1f}%</div></div>', unsafe_allow_html=True)
            
            # Gráficos de Gauge e Ticket
            st.markdown("<br>", unsafe_allow_html=True)
            g1, g2 = st.columns([1, 1])
            
            with g1:
                fig_gauge = criar_gauge_score(row_foco['Score'], row_foco['Status'])
                st.plotly_chart(fig_gauge, use_container_width=True)
                
            with g2:
                limite_inf, limite_sup = st.session_state.analyzer.calcular_limites_ticket(res['ticket_mercado'])
                fig_ticket = criar_comparacao_tickets(res['ticket_mercado'], row_foco['Ticket Cliente'], limite_inf, limite_sup)
                st.plotly_chart(fig_ticket, use_container_width=True)
            
            st.markdown("---")
            st.markdown("#### 📈 Cenários de Crescimento")
            col_cen1, col_cen2 = st.columns([1, 1])
            with col_cen1:
                st.dataframe(res['cenarios'][['Cenário', 'Share Alvo', 'Receita Projetada 6M', 'Lucro Projetado 6M', 'Crescimento (%)']], 
                             use_container_width=True)
            with col_cen2:
                fig_cenarios = criar_grafico_cenarios(res['cenarios'])
                st.plotly_chart(fig_cenarios, use_container_width=True)
