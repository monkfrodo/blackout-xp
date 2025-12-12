#!/usr/bin/env python3
import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
import os

GUILD_NAME = "Blackout"
WORLD = "Luminera"
TOP_N = 50

GUILDSTATS_URL = f"https://guildstats.eu/guild={GUILD_NAME}&op=3"

def parse_exp_value(exp_str):
    """Converte string de XP para inteiro."""
    if not exp_str or exp_str.strip() in ['*-*', '-', '', '0']:
        return 0
    clean = exp_str.strip().replace(',', '').replace('.', '').replace('+', '').replace(' ', '')
    is_negative = clean.startswith('-')
    clean = clean.replace('-', '')
    try:
        return -int(clean) if is_negative else int(clean)
    except:
        return 0

def buscar_vocacoes_guild_tibiadata():
    """Busca vocações e levels de todos os membros da guild via TibiaData API."""
    print("Buscando vocações da guild via TibiaData API...")
    vocacoes = {}
    try:
        url = f"https://api.tibiadata.com/v4/guild/{GUILD_NAME}"
        resp = requests.get(url, timeout=30)
        if resp.status_code == 200:
            data = resp.json()
            if 'guild' in data and 'members' in data['guild']:
                for member in data['guild']['members']:
                    nome_lower = member.get('name', '').lower()
                    vocacoes[nome_lower] = {
                        'vocation': member.get('vocation', ''),
                        'level': member.get('level', 0)
                    }
                print(f"  ✓ {len(vocacoes)} vocações carregadas")
    except Exception as e:
        print(f"  ERRO: {e}")
    return vocacoes

def buscar_dados_guild():
    """Busca dados de XP da guild no GuildStats (página op=3)."""
    print("Buscando dados de XP do GuildStats...")
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    resp = requests.get(GUILDSTATS_URL, headers=headers, timeout=30)
    resp.raise_for_status()
    
    soup = BeautifulSoup(resp.text, 'html.parser')
    jogadores = []
    
    for row in soup.find_all('tr'):
        cols = row.find_all('td')
        if len(cols) < 15:
            continue
        
        char_link = None
        for col in cols:
            link = col.find('a')
            if link and 'character?nick=' in str(link.get('href', '')):
                char_link = link
                break
        
        if not char_link:
            continue
        
        nome = char_link.text.strip()
        
        level = 0
        level_text = cols[2].text.strip()
        if level_text.isdigit():
            level = int(level_text)
        
        exp_yesterday = parse_exp_value(cols[-4].text.strip())
        exp_7days = parse_exp_value(cols[-3].text.strip())
        exp_30days = parse_exp_value(cols[-2].text.strip())
        
        jogadores.append({
            'name': nome,
            'level': level,
            'exp_yesterday': exp_yesterday,
            'exp_7days': exp_7days,
            'exp_30days': exp_30days,
            'vocation': '',
            'is_extra': False
        })
    
    print(f"  ✓ {len(jogadores)} jogadores encontrados")
    return jogadores

def main():
    print("=" * 60)
    print(f"Atualizando ranking: {GUILD_NAME}")
    print(f"Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    vocacoes_guild = buscar_vocacoes_guild_tibiadata()
    jogadores = buscar_dados_guild()
    
    print("\nAplicando vocações...")
    for jogador in jogadores:
        nome_lower = jogador['name'].lower()
        if nome_lower in vocacoes_guild:
            jogador['vocation'] = vocacoes_guild[nome_lower]['vocation']
            if jogador['level'] == 0:
                jogador['level'] = vocacoes_guild[nome_lower]['level']
    
    def criar_ranking(jogadores, campo, top_n):
        filtrados = [j for j in jogadores if j.get(campo, 0) > 0]
        filtrados.sort(key=lambda x: x.get(campo, 0), reverse=True)
        return [{
            'rank': i,
            'name': j['name'],
            'vocation': j['vocation'],
            'level': j['level'],
            'points': j[campo],
            'is_extra': False
        } for i, j in enumerate(filtrados[:top_n], 1)]
    
    dados_finais = {
        'guild': GUILD_NAME,
        'world': WORLD,
        'last_update': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'last_update_display': datetime.now().strftime('%d/%m/%Y às %H:%M'),
        'total_members': len(jogadores),
        'rankings': {
            'yesterday': criar_ranking(jogadores, 'exp_yesterday', TOP_N),
            '7days': criar_ranking(jogadores, 'exp_7days', TOP_N),
            '30days': criar_ranking(jogadores, 'exp_30days', TOP_N)
        }
    }
    
    output_path = os.path.join(os.getcwd(), 'dados', 'ranking.json')
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    print(f"\nSalvando em: {output_path}")
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(dados_finais, f, ensure_ascii=False, indent=2)
    
    print(f"\n{'='*60}")
    print(f"✅ Concluído!")
    print(f"   Ontem: {len(dados_finais['rankings']['yesterday'])} jogadores")
    print(f"   7 dias: {len(dados_finais['rankings']['7days'])} jogadores")
    print(f"   30 dias: {len(dados_finais['rankings']['30days'])} jogadores")

if __name__ == "__main__":
    main()
