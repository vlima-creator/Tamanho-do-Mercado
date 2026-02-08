#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Módulo de cálculos de mercado e análise estratégica - Suporte a Múltiplas Categorias e Visão Mensal/Semestral
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple


class MarketAnalyzer:
    """Classe para análise de mercado e cálculo de scores com suporte a múltiplas categorias e visão mensal/semestral"""
    
    def __init__(self):
        self.cliente_data = {
            'cac': 0.0,
            'investimento_mkt': 0.0
        }
        # Estrutura: { 'Categoria Nome': [ {periodo, faturamento, unidades, ticket_medio} ] }
        self.mercado_categoria = {} 
        # Estrutura: { 'Categoria Nome': { 'Subcategoria Nome': [ {periodo, faturamento, unidades, ticket_medio} ] } }
        self.mercado_subcategorias = {}
        
    def set_cliente_data(self, empresa: str, categoria: str, ticket_medio: float,
                        margem: float, faturamento_3m: float, unidades_3m: int,
                        range_permitido: float = 20.0, ticket_custom: float = None,
                        cac: float = 0.0, investimento_mkt: float = 0.0):
        """Define dados do cliente"""
        self.cliente_data.update({
            'empresa': empresa,
            'categoria_principal': categoria,
            'ticket_medio': ticket_medio if ticket_medio else (faturamento_3m / unidades_3m if unidades_3m > 0 else 0),
            'margem': margem / 100 if margem > 1 else margem,
            'faturamento_3m': faturamento_3m,
            'unidades_3m': unidades_3m,
            'range_permitido': range_permitido / 100 if range_permitido > 1 else range_permitido,
            'ticket_custom': ticket_custom,
            'cac': cac,
            'investimento_mkt': investimento_mkt
        })
        
    def add_mercado_categoria(self, categoria: str, periodo: str, faturamento: float, unidades: int):
        """Adiciona dados de mercado para uma categoria macro"""
        if categoria not in self.mercado_categoria:
            self.mercado_categoria[categoria] = []
        
        faturamento = float(faturamento) if faturamento else 0.0
        unidades = int(float(unidades)) if unidades else 0
        ticket_medio = faturamento / unidades if unidades > 0 else 0
        
        self.mercado_categoria[categoria].append({
            'periodo': periodo,
            'faturamento': faturamento,
            'unidades': unidades,
            'ticket_medio': ticket_medio
        })
        
    def add_mercado_subcategoria(self, categoria: str, subcategoria: str, periodo: str, faturamento: float, unidades: int):
        """Adiciona dados de mercado mensais para uma subcategoria"""
        if categoria not in self.mercado_subcategorias:
            self.mercado_subcategorias[categoria] = {}
            
        if subcategoria not in self.mercado_subcategorias[categoria]:
            self.mercado_subcategorias[categoria][subcategoria] = []
            
        faturamento = float(faturamento) if faturamento else 0.0
        unidades = int(float(unidades)) if unidades else 0
        ticket_medio = faturamento / unidades if unidades > 0 else 0
            
        self.mercado_subcategorias[categoria][subcategoria].append({
            'periodo': periodo,
            'faturamento': faturamento,
            'unidades': unidades,
            'ticket_medio': ticket_medio
        })

    def get_consolidado_6m(self, categoria: str, subcategoria: str) -> Dict:
        """Consolida os últimos 6 meses para a visão clássica de 6 meses"""
        if categoria not in self.mercado_subcategorias or subcategoria not in self.mercado_subcategorias[categoria]:
            return {'faturamento_6m': 0, 'unidades_6m': 0, 'ticket_medio': 0}
            
        historico = self.mercado_subcategorias[categoria][subcategoria]
        df = pd.DataFrame(historico)
        if df.empty:
            return {'faturamento_6m': 0, 'unidades_6m': 0, 'ticket_medio': 0}
            
        # Tentar ordenar por data se possível
        try:
            df['dt'] = pd.to_datetime(df['periodo'], dayfirst=True, errors='coerce')
            df = df.sort_values('dt', ascending=False).head(6)
        except:
            df = df.tail(6)
            
        faturamento_6m = df['faturamento'].sum()
        unidades_6m = df['unidades'].sum()
        ticket_medio = faturamento_6m / unidades_6m if unidades_6m > 0 else 0
        
        return {
            'subcategoria': subcategoria,
            'faturamento_6m': faturamento_6m,
            'unidades_6m': unidades_6m,
            'ticket_medio': ticket_medio
        }

    def calcular_score(self, categoria: str, faturamento_6m: float, ticket_mercado: float) -> float:
        """Calcula score de priorização (GUT adaptada)"""
        if categoria not in self.mercado_subcategorias:
            return 0.0
            
        # Pegar o faturamento máximo de 6m entre todas as subcategorias desta categoria
        fats_6m = []
        for sub_nome in self.mercado_subcategorias[categoria]:
            cons = self.get_consolidado_6m(categoria, sub_nome)
            fats_6m.append(cons['faturamento_6m'])
            
        max_faturamento = max(fats_6m) if fats_6m else 1.0
        g = faturamento_6m / max_faturamento if max_faturamento > 0 else 0
        
        ticket_cliente = self.cliente_data.get('ticket_custom') or self.cliente_data.get('ticket_medio', 0)
        range_pct = self.cliente_data.get('range_permitido', 0.20)
        diff_pct = abs(ticket_cliente - ticket_mercado) / ticket_mercado if ticket_mercado > 0 else 1
        
        u = 1.0 if diff_pct <= range_pct else (0.7 if ticket_cliente < ticket_mercado else 0.3)
        t = self.cliente_data.get('margem', 0)
        
        score_final = (g * 0.4) + (u * 0.4) + (t * 0.2)
        return min(1.0, score_final)

    def calcular_fit_ticket(self, ticket_mercado: float) -> Tuple[str, str]:
        """Calcula fit do ticket cliente vs mercado"""
        ticket_cliente = self.cliente_data.get('ticket_custom') or self.cliente_data.get('ticket_medio', 0)
        range_pct = self.cliente_data.get('range_permitido', 0.20)
        
        limite_inferior = ticket_mercado * (1 - range_pct)
        limite_superior = ticket_mercado * (1 + range_pct)
        
        if limite_inferior <= ticket_cliente <= limite_superior:
            return "DENTRO", "Ticket OK"
        elif ticket_cliente < limite_inferior:
            return "ABAIXO", "Aumentar ticket"
        else:
            return "ACIMA", "Reduzir ticket"

    def calcular_status(self, score: float, fit_ticket: str) -> str:
        """Determina status baseado no score e fit de ticket"""
        if score >= 0.7 and fit_ticket == "DENTRO":
            return "FOCO"
        elif score >= 0.4 or fit_ticket == "DENTRO":
            return "OK"
        else:
            return "EVITAR"

    def gerar_ranking(self, categoria: str = None) -> pd.DataFrame:
        """Gera ranking baseado na visão de 6 meses consolidada"""
        if not self.mercado_subcategorias:
            return pd.DataFrame()
            
        ranking_data = []
        categorias_alvo = [categoria] if categoria else list(self.mercado_subcategorias.keys())
        
        for cat in categorias_alvo:
            if cat in self.mercado_subcategorias:
                for sub_nome in self.mercado_subcategorias[cat]:
                    cons = self.get_consolidado_6m(cat, sub_nome)
                    score = self.calcular_score(cat, cons['faturamento_6m'], cons['ticket_medio'])
                    fit_status, leitura = self.calcular_fit_ticket(cons['ticket_medio'])
                    status = self.calcular_status(score, fit_status)
                    
                    ranking_data.append({
                        'Categoria Macro': cat,
                        'Subcategoria': sub_nome,
                        'Mercado (R$)': cons['faturamento_6m'],
                        'Unidades 6M': cons['unidades_6m'],
                        'Ticket Mercado': cons['ticket_medio'],
                        'Ticket Cliente': self.cliente_data.get('ticket_custom') or self.cliente_data.get('ticket_medio', 0),
                        'Score': score,
                        'Status': status,
                        'Leitura': leitura
                    })
        
        if not ranking_data: return pd.DataFrame()
        return pd.DataFrame(ranking_data).sort_values('Score', ascending=False).reset_index(drop=True)

    def simular_cenarios(self, categoria: str, subcategoria: str, custom_shares: Dict = None) -> Dict:
        """Simula cenários baseados na visão consolidada de 6 meses"""
        cons = self.get_consolidado_6m(categoria, subcategoria)
        mercado_6m = cons['faturamento_6m']
        margem = self.cliente_data.get('margem', 0)
        fat_3m = self.cliente_data.get('faturamento_3m', 0)
        faturamento_base_6m = float(fat_3m) * 2 if fat_3m else 0
        
        shares = custom_shares or {
            'Conservador': {'share_alvo': 0.002, 'label': '0,2%'},
            'Provável': {'share_alvo': 0.005, 'label': '0,5%'},
            'Otimista': {'share_alvo': 0.01, 'label': '1,0%'}
        }
        
        cenarios_res = []
        for nome, info in shares.items():
            receita_proj = mercado_6m * info['share_alvo']
            lucro_proj = receita_proj * margem
            delta = receita_proj - faturamento_base_6m
            crescimento = (delta / faturamento_base_6m * 100) if faturamento_base_6m > 0 else 0
            
            cenarios_res.append({
                'Cenário': nome,
                'Market Share': info['label'],
                'Receita Projetada 6M': receita_proj,
                'Lucro Projetado 6M': lucro_proj,
                'Delta vs Atual': delta,
                'Crescimento (%)': crescimento
            })
            
        return {
            'mercado_6m': mercado_6m,
            'ticket_mercado': cons['ticket_medio'],
            'cenarios': pd.DataFrame(cenarios_res)
        }

    def calcular_share_atual(self, mercado_6m: float) -> float:
        """Calcula share atual do cliente no mercado da subcategoria"""
        faturamento_3m = float(self.cliente_data.get('faturamento_3m', 0))
        faturamento_6m_projetado = faturamento_3m * 2
        if mercado_6m > 0:
            return (faturamento_6m_projetado / mercado_6m) * 100
        return 0.0

    def calcular_confianca(self, categoria: str, subcategoria: str) -> Dict:
        """Calcula o Índice de Confiança da Projeção (0 a 100%)"""
        score = 100
        motivos = []
        
        historico_cat = self.mercado_categoria.get(categoria, [])
        if len(historico_cat) < 3:
            score -= 30
            motivos.append("Pouco histórico de mercado (menos de 3 meses)")
        
        cons = self.get_consolidado_6m(categoria, subcategoria)
        ticket_mercado = cons['ticket_medio']
        ticket_cliente = self.cliente_data.get('ticket_custom') or self.cliente_data.get('ticket_medio', 0)
        if ticket_mercado > 0:
            diff = abs(ticket_cliente - ticket_mercado) / ticket_mercado
            if diff > 0.5:
                score -= 20
                motivos.append("Ticket muito fora da média do mercado (>50%)")
        
        if self.cliente_data.get('faturamento_3m', 0) == 0:
            score -= 40
            motivos.append("Faturamento atual do cliente não informado")
            
        return {
            "score": max(0, score),
            "nivel": "Alta" if score >= 80 else ("Média" if score >= 50 else "Baixa"),
            "motivos": motivos
        }

    def calcular_tendencia(self, categoria: str) -> Dict:
        """Calcula tendência baseada no histórico da categoria macro"""
        if categoria not in self.mercado_categoria or len(self.mercado_categoria[categoria]) < 2:
            return {'tendencia': 'Estável', 'crescimento_mensal': 0, 'projecao_3m': 0}
            
        df = pd.DataFrame(self.mercado_categoria[categoria])
        ultimo_fat = df['faturamento'].iloc[-1]
        penultimo_fat = df['faturamento'].iloc[-2]
        crescimento = ((ultimo_fat - penultimo_fat) / penultimo_fat) if penultimo_fat > 0 else 0
        
        tendencia = "Alta" if crescimento > 0.05 else ("Baixa" if crescimento < -0.05 else "Estável")
        proj_3m = ultimo_fat * (1 + crescimento) * 3
        
        return {
            'tendencia': tendencia,
            'crescimento_mensal': crescimento * 100,
            'projecao_3m': proj_3m
        }

    def identificar_anomalias(self, categoria: str) -> List[Dict]:
        """Identifica anomalias e oportunidades no mercado"""
        anomalias = []
        if categoria not in self.mercado_subcategorias: return []
        
        subs = []
        for sub_nome in self.mercado_subcategorias[categoria]:
            subs.append(self.get_consolidado_6m(categoria, sub_nome))
            
        if not subs: return []
        df_subs = pd.DataFrame(subs)
        avg_ticket = df_subs['ticket_medio'].mean()
        
        for _, row in df_subs.iterrows():
            if row['ticket_medio'] > avg_ticket * 1.5:
                anomalias.append({
                    'Subcategoria': row['subcategoria'],
                    'Tipo': 'Ticket Elevado',
                    'Impacto': 'Alto',
                    'Insight': 'Subcategoria com ticket muito acima da média. Verifique se há nicho premium.'
                })
        return anomalias

    def gerar_plano_acao(self, categoria: str) -> List[Dict]:
        """Gera recomendações estratégicas"""
        ranking = self.gerar_ranking(categoria)
        plano = []
        for _, row in ranking.iterrows():
            acoes = []
            if row['Status'] == "FOCO":
                acoes = ["Escalar investimento em Ads", "Expandir mix de produtos", "Otimizar logística"]
            elif row['Leitura'] == "Aumentar ticket":
                acoes = ["Revisar precificação", "Agregar valor ao produto", "Focar em kits"]
            else:
                acoes = ["Monitorar concorrência", "Manter operação eficiente"]
                
            plano.append({
                'Subcategoria': row['Subcategoria'],
                'Prioridade': "Alta" if row['Status'] == "FOCO" else "Média",
                'Ações': acoes,
                'Cor': "#2ecc71" if row['Status'] == "FOCO" else "#f1c40f",
                'Score': row['Score']
            })
        return plano
