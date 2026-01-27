#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Módulo de cálculos de mercado e análise estratégica
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple


class MarketAnalyzer:
    """Classe para análise de mercado e cálculo de scores"""
    
    def __init__(self):
        self.cliente_data = {}
        self.mercado_categoria = []
        self.mercado_subcategorias = []
        
    def set_cliente_data(self, empresa: str, categoria: str, ticket_medio: float,
                        margem: float, faturamento_3m: float, unidades_3m: int,
                        range_permitido: float = 20.0, ticket_custom: float = None):
        """Define dados do cliente"""
        self.cliente_data = {
            'empresa': empresa,
            'categoria': categoria,
            'ticket_medio': ticket_medio if ticket_medio else (faturamento_3m / unidades_3m if unidades_3m > 0 else 0),
            'margem': margem / 100 if margem > 1 else margem,  # Converter para decimal se necessário
            'faturamento_3m': faturamento_3m,
            'unidades_3m': unidades_3m,
            'range_permitido': range_permitido / 100 if range_permitido > 1 else range_permitido,
            'ticket_custom': ticket_custom
        }
        
    def add_mercado_categoria(self, periodo: str, faturamento: float, unidades: int):
        """Adiciona dados de mercado da categoria"""
        ticket_medio = faturamento / unidades if unidades > 0 else 0
        self.mercado_categoria.append({
            'periodo': periodo,
            'faturamento': faturamento,
            'unidades': unidades,
            'ticket_medio': ticket_medio
        })
        
    def add_mercado_subcategoria(self, subcategoria: str, faturamento_6m: float, unidades_6m: int):
        """Adiciona dados de mercado de subcategoria"""
        ticket_medio = faturamento_6m / unidades_6m if unidades_6m > 0 else 0
        self.mercado_subcategorias.append({
            'subcategoria': subcategoria,
            'faturamento_6m': faturamento_6m,
            'unidades_6m': unidades_6m,
            'ticket_medio': ticket_medio
        })
        
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
    
    def calcular_score(self, faturamento_6m: float, ticket_mercado: float) -> float:
        """
        Calcula score de priorização baseado em:
        - Tamanho de mercado (peso 70%)
        - Fit de ticket (peso 30%)
        """
        if not self.mercado_subcategorias:
            return 0.0
            
        # Normalizar tamanho de mercado (0-1)
        max_faturamento = max([s['faturamento_6m'] for s in self.mercado_subcategorias])
        score_mercado = faturamento_6m / max_faturamento if max_faturamento > 0 else 0
        
        # Calcular score de fit de ticket (0-1)
        ticket_cliente = self.cliente_data.get('ticket_custom') or self.cliente_data.get('ticket_medio', 0)
        range_pct = self.cliente_data.get('range_permitido', 0.20)
        
        # Diferença percentual
        diff_pct = abs(ticket_cliente - ticket_mercado) / ticket_mercado if ticket_mercado > 0 else 1
        
        # Score de fit: 1.0 se dentro do range, decai linearmente fora
        if diff_pct <= range_pct:
            score_fit = 1.0
        else:
            # Penalizar proporcionalmente ao desvio
            score_fit = max(0, 1 - (diff_pct - range_pct))
        
        # Score final ponderado
        score_final = (score_mercado * 0.7) + (score_fit * 0.3)
        
        return score_final
    
    def calcular_status(self, score: float, fit_ticket: str) -> str:
        """Determina status baseado no score e fit de ticket"""
        if score >= 0.7 and fit_ticket == "DENTRO":
            return "FOCO"
        elif score >= 0.4 or fit_ticket == "DENTRO":
            return "OK"
        else:
            return "EVITAR"
    
    def calcular_share_atual(self, mercado_6m: float) -> float:
        """Calcula share atual do cliente no mercado da subcategoria"""
        faturamento_3m = self.cliente_data.get('faturamento_3m', 0)
        # Projetar 3M para 6M (multiplicar por 2)
        faturamento_6m_projetado = faturamento_3m * 2
        
        if mercado_6m > 0:
            return (faturamento_6m_projetado / mercado_6m) * 100
        return 0.0
    
    def gerar_ranking(self) -> pd.DataFrame:
        """Gera ranking de subcategorias com scores e status"""
        if not self.mercado_subcategorias:
            return pd.DataFrame()
        
        ranking_data = []
        
        for subcat in self.mercado_subcategorias:
            score = self.calcular_score(subcat['faturamento_6m'], subcat['ticket_medio'])
            fit_status, leitura = self.calcular_fit_ticket(subcat['ticket_medio'])
            status = self.calcular_status(score, fit_status)
            
            ranking_data.append({
                'Subcategoria': subcat['subcategoria'],
                'Mercado (R$)': subcat['faturamento_6m'],
                'Unidades 6M': subcat['unidades_6m'],
                'Ticket Mercado': subcat['ticket_medio'],
                'Ticket Cliente': self.cliente_data.get('ticket_custom') or self.cliente_data.get('ticket_medio', 0),
                'Score': score,
                'Status': status,
                'Leitura': leitura
            })
        
        # Ordenar por score decrescente
        df = pd.DataFrame(ranking_data)
        df = df.sort_values('Score', ascending=False).reset_index(drop=True)
        
        return df
    
    def simular_cenarios(self, subcategoria: str) -> Dict:
        """Simula cenários de crescimento para uma subcategoria"""
        # Encontrar dados da subcategoria
        subcat_data = next((s for s in self.mercado_subcategorias if s['subcategoria'] == subcategoria), None)
        
        if not subcat_data:
            return {}
        
        mercado_6m = subcat_data['faturamento_6m']
        ticket_usado = self.cliente_data.get('ticket_custom') or self.cliente_data.get('ticket_medio', 0)
        margem = self.cliente_data.get('margem', 0)
        faturamento_atual_6m = self.cliente_data.get('faturamento_3m', 0) * 2
        
        cenarios = {
            'Conservador': {'share_alvo': 0.002, 'label': '0,2%'},
            'Provável': {'share_alvo': 0.005, 'label': '0,5%'},
            'Otimista': {'share_alvo': 0.010, 'label': '1,0%'}
        }
        
        resultados = []
        
        for nome, config in cenarios.items():
            receita_projetada = mercado_6m * config['share_alvo']
            lucro_projetado = receita_projetada * margem
            delta = receita_projetada - faturamento_atual_6m
            
            resultados.append({
                'Cenário': nome,
                'Share Alvo': config['label'],
                'Ticket Usado': ticket_usado,
                'Receita Projetada 6M': receita_projetada,
                'Lucro Projetado 6M': lucro_projetado,
                'Delta vs Atual': delta,
                'Crescimento (%)': (delta / faturamento_atual_6m * 100) if faturamento_atual_6m > 0 else 0
            })
        
        return {
            'cenarios': pd.DataFrame(resultados),
            'mercado_6m': mercado_6m,
            'ticket_mercado': subcat_data['ticket_medio'],
            'share_atual': self.calcular_share_atual(mercado_6m)
        }
    
    def calcular_limites_ticket(self, ticket_mercado: float) -> Tuple[float, float]:
        """Calcula limites inferior e superior do ticket"""
        range_pct = self.cliente_data.get('range_permitido', 0.20)
        limite_inferior = ticket_mercado * (1 - range_pct)
        limite_superior = ticket_mercado * (1 + range_pct)
        return limite_inferior, limite_superior
    
    def get_mercado_categoria_df(self) -> pd.DataFrame:
        """Retorna DataFrame com dados de mercado da categoria"""
        if not self.mercado_categoria:
            return pd.DataFrame()
        return pd.DataFrame(self.mercado_categoria)
    
    def clear_data(self):
        """Limpa todos os dados"""
        self.cliente_data = {}
        self.mercado_categoria = []
        self.mercado_subcategorias = []
