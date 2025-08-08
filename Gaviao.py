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

# Função para detectar padrão
def detectar_padrao(historico):
    if len(historico) < 2:
        return "Sem padrão suficiente"

    ultimo = historico[-1]
    penultimo = historico[-2]

    # Sequência repetitiva (3 ou mais)
    count = 1
    for i in range(len(historico)-2, -1, -1):
        if historico[i] == ultimo:
            count += 1
        else:
            break
    if count >= 3:
        return "Sequência Repetitiva"

    # Padrão alternado (ex: V A V A)
    if len(historico) >= 4:
        alternado = True
        for i in range(len(historico)-1):
            if historico[i] == historico[i+1]:
                alternado = False
                break
        if alternado:
            return "Padrão Alternado"

    # Quebra de padrão (2 iguais + inversão)
    if count == 2 and penultimo == ultimo and len(historico) >= 3 and historico[-3] != ultimo:
        return "Quebra de Padrão"

    # Empates estratégicos
    if 'E' in historico[-5:]:
        return "Empates Estratégicos"

    # Sequências longas (>5)
    if count >= 5:
        return "Sequências Longas de Uma Cor"

    # Padrão de dois ou três repetidos + inversão
    if len(historico) >= 4:
        last_four = historico[-4:]
        if last_four[0] == last_four[1] and last_four[2] != last_four[1] and last_four[3] == last_four[2]:
            return "Padrão de Dois ou Três Repetidos + Inversão"

    # Padrões de ciclos curtos
    if len(historico) >= 6:
        ciclo_1 = historico[-3:]
        ciclo_2 = historico[-6:-3]
        if ciclo_1 == ciclo_2:
            return "Padrões de Ciclos Curtos"

    # Falsos padrões (muita alternância, pouca repetição)
    if len(historico) >= 6:
        repeticoes = sum(1 for i in range(len(historico)-1) if historico[i] == historico[i+1])
        if repeticoes <= 1:
            return "Falsos Padrões"

    # Manipulação por nível de confiança (empates e inversões)
    ultimos_6 = historico[-6:]
    empates = ultimos_6.count('E')
    inversoes = sum(1 for i in range(len(ultimos_6)-1) if ultimos_6[i] != ultimos_6[i+1] and ultimos_6[i] != 'E' and ultimos_6[i+1] != 'E')
    if empates >= 1 and inversoes >= 2:
        return "Manipulação por Nível de Confiança"

    return "Ruído Controlado / Quântico"

# Função para sugerir aposta
def sugerir_aposta(padrao, historico):
    ultimo = historico[-1] if historico else None

    if padrao == "Sequência Repetitiva":
        return f"Aposte em {EMOJI_MAP[oposto(ultimo)]}", "Aposte no contrário da sequência, esperando a quebra do padrão."
    elif padrao == "Padrão Alternado":
        return f"Aposte em {EMOJI_MAP[ultimo]}", "Aposte na continuação da alternância do padrão atual."
    elif padrao == "Quebra de Padrão":
        return f"Aposte em {EMOJI_MAP[oposto(ultimo)]}", "Após uma quebra, aposte no oposto do último resultado."
    elif padrao == "Empates Estratégicos":
        for i in reversed(historico[:-1]):
            if i != 'E':
                return f"Aposte em {EMOJI_MAP[i]}", "Empate detectado. Aposte na repetição do último lado vencedor."
        return "Aguardar", "Empate detectado, mas sem histórico claro para apostar."
    elif padrao == "Sequências Longas de Uma Cor":
        return f"Aposte em {EMOJI_MAP[ultimo]}", "Sequência longa detectada. Aposte na continuação ou aguarde a quebra."
    elif padrao == "Padrão de Dois ou Três Repetidos + Inversão":
        ciclo = historico[-4:-1]
        if ciclo[0] == ciclo[1] and ciclo[2] != ciclo[1]:
            return f"Aposte em {EMOJI_MAP[ciclo[2]]}", "Aposte na repetição da inversão do ciclo detectado."
        return "Aguardar", "Ciclo não claro para apostar."
    elif padrao == "Padrões de Ciclos Curtos":
        ciclo = historico[-4:]
        return f"Aposte em {EMOJI_MAP[ciclo[0]]}", "Ciclo curto detectado. Aposte na continuidade do ciclo."
    elif padrao == "Falsos Padrões":
        return "Evitar aposta", "Falso padrão detectado. Evite apostar para não ser enganado."
    elif padrao == "Manipulação por Nível de Confiança":
        return "Aposte com cautela e valor baixo", "Manipulação sofisticada detectada. Aposte com prudência."
    else:
        return "Sem sugestão clara", "Padrão não identificado claramente para sugerir aposta."

# Inicialização do estado da sessão
if 'historico' not in st.session_state:
    st.session_state.historico = collections.deque(maxlen=90)  # Pode ajustar o tamanho conforme necessidade

# --- Layout ---
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
hist_emojis = [EMOJI_MAP[r] for r in reversed(st.session_state.historico)]
linhas = [hist_emojis[i:i+9] for i in range(0, len(hist_emojis), 9)]
for linha in linhas[:10]:
    st.markdown(" ".join(linha))

st.markdown("---")

# Análise e sugestão
if st.session_state.historico:
    historico_list = list(st.session_state.historico)
    padrao = detectar_padrao(historico_list)
    info = PADROES_INFO.get(padrao, {"numero": "?", "emoji": "❔", "descricao": "Padrão não identificado."})
    aposta, explicacao = sugerir_aposta(padrao, historico_list)
    st.markdown(f"**Padrão Detectado: {info['numero']}. {padrao} {info['emoji']}**")
    st.success(f"**Sugestão de Aposta:** {aposta}")
    st.info(f"**Explicação:** {explicacao}")
else:
    st.info("Insira resultados para começar a análise.")

# Rodapé
st.markdown("---")
st.write("Desenvolvido para análise de padrões no Football Studio. Jogue com responsabilidade.")
