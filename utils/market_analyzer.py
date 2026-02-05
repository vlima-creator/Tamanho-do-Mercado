#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Módulo de análise de mercado e projeções mensais
"""

from typing import Dict, List, Tuple
import pandas as pd
import numpy as np

class MarketAnalyzer:
    def __init__(self):
        self.cliente_data = {}
        self.mercado_categoria = {} # { 'NomeCat': [ {'periodo': 'Jan/24', 'faturamento': 100, ...}, ... ] }
        self.mercado_subcategorias = {} # { 'NomeCat': { 'NomeSub': [ {'periodo': 'Jan/24', 'faturamento': 50, ...}, ... ] } }
        
    def set_cliente_data(self, empresa: str, categoria: str, ticket_medio: float, 
                         margem: float, faturamento_3m: float, unidades_3m: float,
                         range_permitido: float = 0.20, ticket_custom: float = None):
        """Define os dados base do cliente"""
        self.cliente_data = {
            'empresa': empresa,
            'categoria_macro': categoria,
            'ticket_medio': ticket_medio,
            'margem': margem / 100 if margem > 1 else margem, # Converte 10% para 0.1
            'faturamento_3m': faturamento_3m,
            'unidades_3m': unidades_3m,
            'range_permitido': range_permitido / 100 if range_permitido > 1 else range_permitido,
            'ticket_custom': ticket_custom
        }
        
    def add_mercado_categoria(self, categoria: str, periodo: str, faturamento: float, unidades: int):
        """Adiciona dados de mercado para uma categoria específica"""
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
        """Adiciona dados de mercado históricos para subcategorias"""
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

    def get_subcategorias_resumo(self, categoria: str) -> List[Dict]:
        """Retorna um resumo das subcategorias baseado no histórico disponível"""
        if categoria not in self.mercado_subcategorias:
            return []
            
        resumo = []
        for sub, historico in self.mercado_subcategorias[categoria].items():
            df = pd.DataFrame(historico)
            if df.empty: continue
            
            # Pegar os dados mais recentes para o ranking (ou média dos últimos meses)
            total_fat = df['faturamento'].sum()
            total_uni = df['unidades'].sum()
            ticket_medio = total_fat / total_uni if total_uni > 0 else 0
            
            resumo.append({
                'subcategoria': sub,
                'faturamento_total': total_fat,
                'unidades_total': total_uni,
                'ticket_medio': ticket_medio,
                'meses_historico': len(df)
            })
        return resumo

    def calcular_score(self, categoria: str, faturamento_sub: float, ticket_sub: float) -> float:
        """Calcula score de priorização (GUT adaptada)"""
        resumo = self.get_subcategorias_resumo(categoria)
        if not resumo: return 0.0
        
        # G - Gravidade (Tamanho do Mercado)
        max_fat = max([s['faturamento_total'] for s in resumo])
        g = faturamento_sub / max_fat if max_fat > 0 else 0
        
        # U - Urgência (Fit de Ticket)
        ticket_cliente = self.cliente_data.get('ticket_custom') or self.cliente_data.get('ticket_medio', 0)
        range_pct = self.cliente_data.get('range_permitido', 0.20)
        diff_pct = abs(ticket_cliente - ticket_sub) / ticket_sub if ticket_sub > 0 else 1
        u = 1.0 if diff_pct <= range_pct else (0.7 if ticket_cliente < ticket_sub else 0.3)
        
        # T - Tendência (Margem)
        t = self.cliente_data.get('margem', 0)
        
        return (g * 0.4) + (u * 0.4) + (t * 0.2)

    def gerar_cenarios_projetados(self, categoria: str, subcategoria: str) -> List[Dict]:
        """Gera cenários baseados no histórico mensal"""
        resumo = self.get_subcategorias_resumo(categoria)
        sub_data = next((s for s in resumo if s['subcategoria'] == subcategoria), None)
        if not sub_data: return []
        
        fat_mercado_mensal = sub_data['faturamento_total'] / max(1, sub_data['meses_historico'])
        margem = self.cliente_data.get('margem', 0.1)
        
        cenarios = []
        # Cenário Conservador (0.5% do mercado)
        cenarios.append(self._criar_cenario("Conservador", fat_mercado_mensal, 0.005, margem))
        # Cenário Realista (1.5% do mercado)
        cenarios.append(self._criar_cenario("Realista", fat_mercado_mensal, 0.015, margem))
        # Cenário Otimista (3% do mercado)
        cenarios.append(self._criar_cenario("Otimista", fat_mercado_mensal, 0.03, margem))
        
        return cenarios

    def _criar_cenario(self, nome: str, fat_mercado: float, share: float, margem: float) -> Dict:
        receita_mes = fat_mercado * share
        return {
            'Cenário': nome,
            'Market Share': f"{share*100:.1f}%",
            'Receita Mensal Est.': receita_mes,
            'Lucro Mensal Est.': receita_mes * margem,
            'Receita Projetada 6M': receita_mes * 6,
            'Lucro Projetada 6M': receita_mes * 6 * margem,
            'Crescimento (%)': 0 # Calculado no app
        }
