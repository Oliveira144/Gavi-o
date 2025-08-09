import streamlit as st
import collections

# --- Configuração da página ---
st.set_page_config(
    page_title="Analisador Fantasmas de Padrões Football Studio",
    page_icon="🔮",
    layout="wide"
)

# --- Mapas ---
EMOJI_MAP = {'V': '🔴', 'A': '🔵', 'E': '🟡'}

# Mapeamento dos padrões com emojis explicativos
PADROES_INFO = {
    "Sequência Repetitiva": {
        "numero": "1",
        "emoji": "🔴",
        "descricao": "3 ou mais resultados iguais consecutivos, indicando possível quebra."
    },
    "Sequência Repetitiva após quebra": {
        "numero": "1b",
        "emoji": "🔄",
        "descricao": "Sequência retomada após quebra de padrão."
    },
    "Padrão Alternado": {
        "numero": "2",
        "emoji": "🔵",
        "descricao": "Resultados alternados (ex: 🔴🔵🔴🔵), padrão comum de manipulação."
    },
    "Quebra de Padrão": {
        "numero": "3",
        "emoji": "⚠️",
        "descricao": "Mudança inesperada após padrão repetitivo, indicando manipulação."
    },
    "Empates Estratégicos": {
        "numero": "4",
        "emoji": "🟡",
        "descricao": "Empates usados como estratégia para confundir leitura."
    },
    "Sequências Longas de Uma Cor": {
        "numero": "5",
        "emoji": "🔴",
        "descricao": "Sequência longa (>5) da mesma cor, manipulação evidente."
    },
    "Padrão de Dois ou Três Repetidos + Inversão": {
        "numero": "6",
        "emoji": "🔵",
        "descricao": "Ciclo com 2-3 repetições seguido de inversão, tentando iludir."
    },
    "Padrões de Ciclos Curtos": {
        "numero": "7",
        "emoji": "🔄",
        "descricao": "Repetição de pequenos ciclos de resultados."
    },
    "Ruído Controlado / Quântico": {
        "numero": "8",
        "emoji": "❓",
        "descricao": "Sequência aparentemente aleatória para confundir apostas."
    },
    "Falsos Padrões": {
        "numero": "9",
        "emoji": "🚫",
        "descricao": "Padrão falso, alta alternância aleatória para evitar leitura."
    },
    "Manipulação por Nível de Confiança": {
        "numero": "10",
        "emoji": "🔒",
        "descricao": "Manipulação sofisticada com empates e inversões frequentes."
    }
}

def oposto(cor):
    if cor == 'V': return 'A'
    if cor == 'A': return 'V'
    return None

def detectar_padrao(historico):
    if len(historico) < 2:
        return "Sem padrão suficiente"

    # Verificar a sequência atual no final do histórico
    ultimo = historico[-1]
    count_atual = 1
    for i in range(len(historico)-2, max(-1, len(historico)-18), -1):
        if historico[i] == ultimo:
            count_atual += 1
        else:
            break

    # Verificar a sequência anterior que foi quebrada
    cor_anterior = None
    count_anterior = 0
    if len(historico) > count_atual:
        cor_anterior = historico[-count_atual-1]
        count_anterior = 1
        for i in range(len(historico)-count_atual-2, max(-1, len(historico)-count_atual-18), -1):
            if historico[i] == cor_anterior:
                count_anterior += 1
            else:
                break

    # Sequência Repetitiva (3 ou mais da mesma cor)
    if count_atual >= 3:
        # Se houve uma sequência anterior significativa que foi quebrada
        if count_anterior >= 2 and cor_anterior != ultimo:
            return f"Sequência Repetitiva após quebra ({count_atual}x {EMOJI_MAP[ultimo]})"
        return f"Sequência Repetitiva ({count_atual}x {EMOJI_MAP[ultimo]})"

    # Padrão alternado (ex: V A V A)
    if len(historico) >= 4:
        alternado = True
        for i in range(max(0, len(historico)-18), len(historico)-1):
            if historico[i] == historico[i+1]:
                alternado = False
                break
        if alternado:
            return "Padrão Alternado"

    # Quebra de padrão (2 iguais + inversão)
    if count_atual == 2 and historico[-2] == ultimo and len(historico) >= 3 and historico[-3] != ultimo:
        return "Quebra de Padrão"

    # Empates estratégicos
    if 'E' in historico[-18:]:
        return "Empates Estratégicos"

    # Sequências longas (>5)
    if count_atual >= 5:
        return "Sequências Longas de Uma Cor"

    # Padrão de dois ou três repetidos + inversão
    if len(historico) >= 4:
        last_group = historico[-18:] if len(historico) >= 18 else historico
        for i in range(len(last_group)-3):
            if last_group[i] == last_group[i+1] and last_group[i+2] != last_group[i+1] and last_group[i+3] == last_group[i+2]:
                return "Padrão de Dois ou Três Repetidos + Inversão"

    # Padrões de ciclos curtos
    if len(historico) >= 6:
        last_18 = historico[-18:] if len(historico) >= 18 else historico
        for i in range(len(last_18)-5):
            ciclo_1 = last_18[i:i+3]
            ciclo_2 = last_18[i+3:i+6]
            if ciclo_1 == ciclo_2:
                return "Padrões de Ciclos Curtos"

    # Falsos padrões
    if len(historico) >= 6:
        last_18 = historico[-18:] if len(historico) >= 18 else historico
        repeticoes = sum(1 for i in range(len(last_18)-1) if last_18[i] == last_18[i+1])
        if repeticoes <= 1:
            return "Falsos Padrões"

    # Manipulação por nível de confiança
    ultimos_18 = historico[-18:] if len(historico) >= 18 else historico
    empates = ultimos_18.count('E')
    inversoes = sum(1 for i in range(len(ultimos_18)-1) if ultimos_18[i] != ultimos_18[i+1] and ultimos_18[i] != 'E' and ultimos_18[i+1] != 'E')
    if empates >= 1 and inversoes >= 2:
        return "Manipulação por Nível de Confiança"

    return "Ruído Controlado / Quântico"

def sugerir_aposta(padrao, historico):
    if not historico:
        return "Sem sugestão", "Histórico vazio"
    
    ultimo = historico[-1]
    
    if "Sequência Repetitiva" in padrao:
        # Extrai informações da string do padrão
        parts = padrao.split('(')
        count = int(parts[1].split('x')[0])
        cor = ultimo
        
        if "após quebra" in padrao:
            return f"Aposte em {EMOJI_MAP[cor]}", "Sequência retomada após quebra, aposte na continuidade"
        else:
            return f"Aposte em {EMOJI_MAP[oposto(cor)]}", f"Aposte no contrário, esperando quebra da sequência de {count}"
    
    elif padrao == "Padrão Alternado":
        return f"Aposte em {EMOJI_MAP[oposto(ultimo)]}", "Padrão alternado detectado, aposte no oposto do último"
    
    elif padrao == "Quebra de Padrão":
        return f"Aposte em {EMOJI_MAP[ultimo]}", "Quebra de padrão detectada, aposte na continuidade"
    
    elif padrao == "Empates Estratégicos":
        # Encontrar a última cor não-empate
        for resultado in reversed(historico[:-1]):
            if resultado != 'E':
                return f"Aposte em {EMOJI_MAP[resultado]}", "Empate estratégico detectado, aposte na última cor válida"
        return "Aguardar", "Muitos empates consecutivos, aguardar padrão claro"
    
    elif padrao == "Sequências Longas de Uma Cor":
        return "Aguardar", "Sequência muito longa detectada, risco alto"
    
    elif padrao == "Padrão de Dois ou Três Repetidos + Inversão":
        if len(historico) >= 4:
            ciclo = historico[-4:-1]
            if ciclo[0] == ciclo[1] and ciclo[2] != ciclo[1]:
                return f"Aposte em {EMOJI_MAP[ciclo[2]]}", "Padrão de inversão detectado, aposte na continuidade"
        return "Aguardar", "Padrão de inversão não confirmado"
    
    elif padrao == "Padrões de Ciclos Curtos":
        if len(historico) >= 6:
            ciclo = historico[-6:-3]
            return f"Aposte em {EMOJI_MAP[ciclo[0]]}", "Ciclo detectado, aposte na repetição"
        return "Aguardar", "Ciclo não confirmado"
    
    elif padrao == "Falsos Padrões":
        return "Evitar aposta", "Padrão inconsistente detectado, evitar apostar"
    
    elif padrao == "Manipulação por Nível de Confiança":
        return "Aposte com cautela", "Padrão complexo detectado, aposte valores pequenos"
    
    else:
        return "Sem sugestão clara", "Padrão não identificado"

# Inicialização do estado da sessão
if 'historico' not in st.session_state:
    st.session_state.historico = collections.deque(maxlen=100)

# --- Interface ---
st.title("🔮 Analisador Avançado de Padrões Football Studio")
st.markdown("---")

st.markdown("### 1. Inserir Resultados")
st.write("Clique para inserir o resultado da rodada:")

col1, col2, col3, col4, col5 = st.columns(5)
with col1:
    if st.button("🔴 Vitória da Casa", use_container_width=True):
        st.session_state.historico.append('V')
with col2:
    if st.button("🔵 Vitória do Visitante", use_container_width=True):
        st.session_state.historico.append('A')
with col3:
    if st.button("🟡 Empate", use_container_width=True):
        st.session_state.historico.append('E')
with col4:
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("Desfazer", help="Remove o último resultado", use_container_width=True):
        if st.session_state.historico:
            st.session_state.historico.pop()
with col5:
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("Limpar Histórico", help="Apaga todo o histórico", use_container_width=True):
        st.session_state.historico.clear()

st.markdown("---")

st.markdown("### 2. Histórico de Resultados")
if st.session_state.historico:
    hist_emojis = [EMOJI_MAP[r] for r in reversed(st.session_state.historico)]
    linhas = [hist_emojis[i:i+9] for i in range(0, len(hist_emojis), 9)]
    for linha in linhas[:12]:  # Mostra até 12 linhas
        st.markdown(" ".join(linha))
else:
    st.info("Nenhum resultado registrado ainda")

st.markdown("---")

# Análise e sugestão
if st.session_state.historico:
    historico_list = list(st.session_state.historico)
    padrao = detectar_padrao(historico_list)
    
    # Obter informações do padrão
    padrao_base = padrao.split('(')[0].strip() if '(' in padrao else padrao
    info = PADROES_INFO.get(padrao_base, {
        "numero": "?",
        "emoji": "❔",
        "descricao": "Padrão não identificado."
    })
    
    aposta, explicacao = sugerir_aposta(padrao, historico_list)
    
    st.markdown(f"**Padrão Detectado: {info['numero']}. {padrao} {info['emoji']}**")
    st.write(info["descricao"])
    
    if aposta.startswith("Aposte"):
        st.success(f"**Sugestão de Aposta:** {aposta}")
    else:
        st.warning(f"**Recomendação:** {aposta}")
    st.info(f"**Explicação:** {explicacao}")
else:
    st.info("Insira resultados para começar a análise")

st.markdown("---")
st.write("Analisador de padrões Football Studio - Use com responsabilidade")
