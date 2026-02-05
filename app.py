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

def safe_float(val):
    if pd.isna(val): return 0.0
    if isinstance(val, (int, float)): return float(val)
    try:
        s = str(val).replace('R$', '').replace('$', '').strip()
        if not s: return 0.0
        if ',' in s and '.' in s:
            if s.rfind(',') > s.rfind('.'): s = s.replace('.', '').replace(',', '.')
            else: s = s.replace(',', '')
        elif ',' in s: s = s.replace(',', '.')
        return float(s)
    except:
        return 0.0

# --- LÓGICA DE IMPORTAÇÃO EXCEL ---

def processar_excel(file):
    try:
        temp_analyzer = MarketAnalyzer()
        
        # 1. Cliente
        df_cliente = pd.read_excel(file, sheet_name="Cliente", header=None)
        def get_val_by_label(labels, default=""):
            for i in range(len(df_cliente)):
                cell_val = str(df_cliente.iloc[i, 0]).strip().lower()
                for label in labels:
                    if label.lower() in cell_val: return df_cliente.iloc[i, 1]
            return default

        empresa = str(get_val_by_label(["Empresa"], "Empresa Exemplo"))
        cat_macro_cliente = str(get_val_by_label(["Categoria macro"], "Geral"))
        ticket_medio = safe_float(get_val_by_label(["Ticket médio do cliente"], 0))
        margem = safe_float(get_val_by_label(["Margem atual"], 0))
        fat_3m = safe_float(get_val_by_label(["Faturamento médio"], 0))
        uni_3m = int(safe_float(get_val_by_label(["Unidades médias"], 0)))
        range_p = safe_float(get_val_by_label(["Range permitido"], 20))
        ticket_custom = safe_float(get_val_by_label(["Ticket custom"], None))
        
        temp_analyzer.set_cliente_data(
            empresa=empresa, categoria=cat_macro_cliente, ticket_medio=ticket_medio,
            margem=margem, faturamento_3m=fat_3m, unidades_3m=uni_3m,
            range_permitido=range_p, ticket_custom=ticket_custom
        )
        
        # 2. Mercado Categoria
        df_cat = pd.read_excel(file, sheet_name="Mercado_Categoria", skiprows=2)
        def find_col(df, names):
            for col in df.columns:
                if any(n.lower() in str(col).lower() for n in names): return col
            return None

        col_cat = find_col(df_cat, ["Categoria"])
        col_per = find_col(df_cat, ["Periodo", "Período"])
        col_fat = find_col(df_cat, ["Faturamento"])
        col_uni = find_col(df_cat, ["Unidades"])

        if col_cat and col_per:
            for _, row in df_cat.iterrows():
                if pd.notna(row[col_cat]) and pd.notna(row[col_per]):
                    raw_per = row[col_per]
                    per_val = raw_per.strftime('%d/%m/%Y') if isinstance(raw_per, datetime) else str(raw_per).strip()
                    temp_analyzer.add_mercado_categoria(
                        str(row[col_cat]).strip(), per_val, 
                        safe_float(row[col_fat]), int(safe_float(row[col_uni]))
                    )
        
        # 3. Mercado Subcategoria (NOVO FORMATO MENSAL)
        # Tenta ler cada aba que não seja 'Cliente' ou 'Mercado_Categoria' como uma aba de Categoria Macro
        xls = pd.ExcelFile(file)
        for sheet in xls.sheet_names:
            if sheet in ["Cliente", "Mercado_Categoria"]: continue
            
            df_sub = pd.read_excel(file, sheet_name=sheet, skiprows=2)
            # O padrão esperado: Coluna A = Subcategoria, Colunas B, C, D... = Meses
            # Mas vamos ser flexíveis: se houver colunas com nomes de meses, processamos.
            
            sub_col = find_col(df_sub, ["Subcategoria"])
            if not sub_col: continue
            
            # Identificar colunas de meses (Ex: "Janeiro - Faturamento", "Janeiro - Unidades")
            for _, row in df_sub.iterrows():
                sub_name = str(row[sub_col]).strip()
                if not sub_name or sub_name.lower() == 'nan': continue
                
                for col in df_sub.columns:
                    if " - " in str(col):
                        parts = str(col).split(" - ")
                        mes_ref = parts[0].strip()
                        tipo = parts[1].strip().lower()
                        
                        # Criar um período fictício ou usar o nome do mês
                        # Para simplificar, vamos associar ao histórico da categoria macro se o mês bater
                        # Ou apenas usar o nome do mês como chave de período
                        
                        val = safe_float(row[col])
                        if "faturamento" in tipo:
                            # Busca ou cria registro para esse mês
                            temp_analyzer.add_mercado_subcategoria(sheet, sub_name, mes_ref, val, 0)
                        elif "unidade" in tipo:
                            # Atualiza unidades para o registro já criado
                            if sheet in temp_analyzer.mercado_subcategorias and sub_name in temp_analyzer.mercado_subcategorias[sheet]:
                                for reg in temp_analyzer.mercado_subcategorias[sheet][sub_name]:
                                    if reg['periodo'] == mes_ref:
                                        reg['unidades'] = int(val)
                                        if val > 0: reg['ticket_medio'] = reg['faturamento'] / val
        
        st.session_state.analyzer = temp_analyzer
        st.success(f"Dados de {empresa} importados com sucesso!")
        return True
    except Exception as e:
        st.error(f"Erro na importação: {e}")
        return False

# --- UI PRINCIPAL ---

def main():
    st.sidebar.title("🚀 Menu")
    
    with st.sidebar.expander("📥 Upload de Dados", expanded=not hasattr(st.session_state, 'analyzer')):
        uploaded_file = st.file_uploader("Suba sua planilha padronizada", type=["xlsx"])
        if uploaded_file:
            if processar_excel(uploaded_file):
                st.rerun()

    if not hasattr(st.session_state, 'analyzer') or not st.session_state.analyzer.cliente_data:
        st.info("Por favor, faça o upload da planilha para começar.")
        return

    analyzer = st.session_state.analyzer
    
    tab1, tab2, tab3 = st.tabs(["📊 Dashboard", "🎯 Análise de Subcategorias", "📂 Gestão de Categorias"])

    with tab1:
        st.title(f"Dashboard: {analyzer.cliente_data['empresa']}")
        # Lógica de resumo aqui...
        st.write("Visão geral do mercado e performance.")

    with tab2:
        st.title("Análise Mensal de Subcategorias")
        cats = list(analyzer.mercado_subcategorias.keys())
        if cats:
            sel_cat = st.selectbox("Selecione a Categoria Macro:", cats)
            resumo = analyzer.get_subcategorias_resumo(sel_cat)
            df_resumo = pd.DataFrame(resumo)
            if not df_resumo.empty:
                st.dataframe(df_resumo)
                
                sel_sub = st.selectbox("Detalhar Subcategoria:", df_resumo['subcategoria'])
                hist = analyzer.mercado_subcategorias[sel_cat][sel_sub]
                df_hist = pd.DataFrame(hist)
                st.line_chart(df_hist.set_index('periodo')['faturamento'])
        else:
            st.warning("Nenhum dado de subcategoria encontrado nas abas adicionais.")

    with tab3:
        st.title("Gestão de Categorias Macro")
        # Gráficos de evolução que já funcionam...
        for cat, dados in analyzer.mercado_categoria.items():
            st.subheader(f"Evolução: {cat}")
            df = pd.DataFrame(dados)
            st.plotly_chart(criar_grafico_evolucao_categoria(df))

if __name__ == "__main__":
    main()
