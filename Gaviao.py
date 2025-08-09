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

# Mapeamento dos padrões com emojis explicativos (as chaves devem bater com detectar_padrao)
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

# --- Helpers de lógica ---
def oposto(cor):
    if cor == 'V':
        return 'A'
    if cor == 'A':
        return 'V'
    return None

def last_non_e(historico):
    for r in reversed(historico):
        if r != 'E':
            return r
    return None

def detectar_padrao(historico):
    """
    Retorna (padrao_str, confianca_int)
    Prioriza padrões mais fortes primeiro para evitar sobreposição de regras.
    """
    if not historico or len(historico) < 1:
        return "Sem padrão suficiente", 0

    n = len(historico)
    ultimos_18 = historico[-18:] if n >= 18 else historico[:]
    empates = ultimos_18.count('E')
    inversoes = sum(
        1 for i in range(len(ultimos_18)-1)
        if ultimos_18[i] != ultimos_18[i+1] and ultimos_18[i] != 'E' and ultimos_18[i+1] != 'E'
    )

    # contagem da sequência atual (contiguous igual ao último valor)
    ultimo = historico[-1]
    count_atual = 0
    for i in range(n-1, -1, -1):
        if historico[i] == ultimo:
            count_atual += 1
        else:
            break

    # sequência anterior (cor diferente imediatamente antes da atual)
    cor_anterior = None
    count_anterior = 0
    idx_prev = n - 1 - count_atual
    if idx_prev >= 0:
        cor_anterior = historico[idx_prev]
        for j in range(idx_prev, -1, -1):
            if historico[j] == cor_anterior:
                count_anterior += 1
            else:
                break

    # --- Prioridade de detecção (mais fortes primeiro) ---
    # 1) Sequências Longas de Uma Cor (evitar apostar, risco alto)
    if count_atual >= 5 and ultimo != 'E':
        confianca = min(95, 50 + count_atual * 7)
        return "Sequências Longas de Uma Cor", confianca

    # 2) Manipulação por Nível de Confiança (empates + várias inversões)
    if empates >= 1 and inversoes >= 2:
        return "Manipulação por Nível de Confiança", 85

    # 3) Padrões de Ciclos Curtos (x x x | x x x)
    slice_u = ultimos_18
    for i in range(0, len(slice_u) - 5):
        bloco1 = slice_u[i:i+3]
        bloco2 = slice_u[i+3:i+6]
        if bloco1 == bloco2 and 'E' not in bloco1 and 'E' not in bloco2:
            return "Padrões de Ciclos Curtos", 80

    # 4) Padrão de Dois ou Três Repetidos + Inversão
    for i in range(0, len(slice_u) - 3):
        a, b, c, d = slice_u[i], slice_u[i+1], slice_u[i+2], slice_u[i+3]
        if a == b and c != b and d == c and a != 'E' and c != 'E':
            return "Padrão de Dois ou Três Repetidos + Inversão", 75

    # 5) Sequência Repetitiva após quebra
    if count_atual >= 3 and cor_anterior and cor_anterior != ultimo and count_anterior >= 2 and ultimo != 'E':
        return "Sequência Repetitiva após quebra", min(85, 50 + count_atual * 6)

    # 6) Sequência Repetitiva (3 ou mais)
    if count_atual >= 3 and ultimo != 'E':
        return "Sequência Repetitiva", min(75, 45 + count_atual * 6)

    # 7) Padrão Alternado (verificar os últimos não-empates)
    non_e = [x for x in historico if x != 'E']
    if len(non_e) >= 4:
        tail = non_e[-8:] if len(non_e) >= 8 else non_e
        alternado = True
        for i in range(len(tail)-1):
            if tail[i] == tail[i+1]:
                alternado = False
                break
        if alternado:
            return "Padrão Alternado", 60

    # 8) Quebra de Padrão (2 iguais seguidos por inversão)
    if count_atual == 2 and n >= 3 and historico[-3] != ultimo:
        return "Quebra de Padrão", 55

    # 9) Empates Estratégicos (qualquer empate recente pode indicar confusão proposital)
    if empates >= 1:
        return "Empates Estratégicos", 50

    # 10) Falsos Padrões (poucas repetições seguidas -> muito ruído)
    repeticoes = sum(1 for i in range(len(ultimos_18)-1) if ultimos_18[i] == ultimos_18[i+1])
    if repeticoes <= 1:
        return "Falsos Padrões", 40

    # 11) Ruído Controlado / Quântico (fallback)
    return "Ruído Controlado / Quântico", 35

def sugerir_aposta(padrao, historico, confianca):
    """
    Retorna (aposta_texto, explicacao_texto)
    Observação: padrao deve ser uma das chaves de PADROES_INFO.
    """
    if not historico:
        return "Sem sugestão", "Histórico vazio"

    ultimo = historico[-1]
    ultimo_valido = last_non_e(historico)
    # recalcula contagens curtas locais
    n = len(historico)
    count_atual = 0
    for i in range(n-1, -1, -1):
        if historico[i] == ultimo:
            count_atual += 1
        else:
            break

    # Mapeamento estrito por padrão detectado (sem substring)
    if padrao == "Sequência Repetitiva após quebra":
        # apostar na continuidade da sequência retomada (se último não for empate)
        if ultimo != 'E':
            return f"Aposte em {EMOJI_MAP[ultimo]}", f"Sequência retomada após quebra ({count_atual}x). Aposte na continuidade — confiança ≈ {confianca}%"
        elif ultimo_valido:
            return f"Aposte em {EMOJI_MAP[ultimo_valido]}", f"Último válido {EMOJI_MAP[ultimo_valido]}. Sequência retomada após empate — confiança ≈ {confianca}%"
        else:
            return "Aguardar", "Resultado recente é empate sem cor válida anterior."

    if padrao == "Sequência Repetitiva":
        # espera-se quebra — sugerir contrário
        if ultimo != 'E':
            cor_oposta = oposto(ultimo)
            if cor_oposta:
                return f"Aposte em {EMOJI_MAP[cor_oposta]}", f"Sequência de {count_atual} detectada; sugerimos apostar no oposto esperando quebra — confiança ≈ {confianca}%"
        return "Aguardar", "Sequência identificada mas último é empate ou inválido."

    if padrao == "Padrão Alternado":
        # aposta no oposto do último
        if ultimo != 'E':
            return f"Aposte em {EMOJI_MAP[oposto(ultimo)]}", f"Padrão alternado detectado — apostar no oposto do último (confiança ≈ {confianca}%)."
        elif ultimo_valido:
            return f"Aposte em {EMOJI_MAP[oposto(ultimo_valido)]}", f"Padrão alternado detectado — usar último válido como referência (confiança ≈ {confianca}%)."
        else:
            return "Sem sugestão clara", "Padrão alternado identificado, mas sem referência válida."

    if padrao == "Quebra de Padrão":
        # apostar na continuidade do último (a quebra normalmente tende a continuar curto prazo)
        if ultimo != 'E':
            return f"Aposte em {EMOJI_MAP[ultimo]}", f"Quebra de padrão detectada — aposte na continuidade do último (confiança ≈ {confianca}%)."
        elif ultimo_valido:
            return f"Aposte em {EMOJI_MAP[ultimo_valido]}", f"Quebra detectada — usar última cor válida (confiança ≈ {confianca}%)."
        else:
            return "Aguardar", "Quebra detectada mas sem cor válida."

    if padrao == "Empates Estratégicos":
        # apostar na última cor válida com confiança reduzida
        if ultimo_valido:
            return f"Aposte em {EMOJI_MAP[ultimo_valido]}", f"Empate estratégico detectado — apostar na última cor válida {EMOJI_MAP[ultimo_valido]} com cautela (confiança ≈ {confianca}%)."
        else:
            return "Aguardar", "Somente empates recentes — aguarde cor válida."

    if padrao == "Sequências Longas de Uma Cor":
        return "Aguardar", f"Sequência muito longa detectada ({count_atual}x). Risco alto — aguardar (confiança ≈ {confianca}%)."

    if padrao == "Padrão de Dois ou Três Repetidos + Inversão":
        # Tenta inferir a inversão: aposta na cor após o pequeno ciclo
        if n >= 3:
            # pegar penúltimo como referência de inversão
            alvo = historico[-2] if historico[-2] != 'E' else ultimo_valido
            if alvo:
                return f"Aposte em {EMOJI_MAP[alvo]}", f"Padrão de 2/3 seguido por inversão — apostar em {EMOJI_MAP[alvo]} (confiança ≈ {confianca}%)."
        return "Aguardar", "Padrão detectado, mas inversão não confiável."

    if padrao == "Padrões de Ciclos Curtos":
        # tenta prever repetição do ciclo (pegar o próximo do ciclo se detectado)
        # buscamos o último ciclo repetido encontrado
        slice_u = ultimos_18 = historico[-18:] if len(historico) >= 18 else historico
        for i in range(0, len(slice_u) - 5):
            bloco1 = slice_u[i:i+3]
            bloco2 = slice_u[i+3:i+6]
            if bloco1 == bloco2 and 'E' not in bloco1:
                # Próxima posição do ciclo é bloco1[0] (ciclo repetido)
                return f"Aposte em {EMOJI_MAP[bloco1[0]]}", f"Ciclo curto detectado; esperada repetição: {EMOJI_MAP[bloco1[0]]} (confiança ≈ {confianca}%)."
        return "Aguardar", "Ciclo curto detectado mas próxima posição não confiável."

    if padrao == "Falsos Padrões":
        return "Evitar aposta", f"Padrão inconsistente (alto ruído) — evitar apostas (confiança ≈ {confianca}%)."

    if padrao == "Manipulação por Nível de Confiança":
        return "Aposte com cautela", f"Padrão complexo detectado — apostar valores pequenos e com gestão de risco (confiança ≈ {confianca}%)."

    if padrao == "Ruído Controlado / Quântico":
        return "Sem sugestão clara", "Sequência muito ruidosa/aleatória — aguardar mais dados."

    # Fallback
    return "Sem sugestão clara", "Padrão não identificável com confiança suficiente."

# --- Inicialização do estado da sessão ---
if 'historico' not in st.session_state:
    st.session_state.historico = collections.deque(maxlen=100)

# --- Interface ---
st.title("🔮 Analisador Avançado de Padrões Football Studio — Versão Revisada")
st.markdown("---")

st.markdown("### 1. Inserir Resultados")
st.write("Clique para inserir o resultado da rodada (inserção manual):")

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
    # exibimos o histórico mais recente à esquerda (da esquerda para a direita), 9 por linha, até 10 linhas
    historico_list = list(st.session_state.historico)
    # queremos mostrar mais recentes primeiro (como nos seus requisitos anteriores)
    hist_emojis = [EMOJI_MAP[r] for r in reversed(historico_list)]
    linhas = [hist_emojis[i:i+9] for i in range(0, len(hist_emojis), 9)]
    for linha in linhas[:10]:  # até 10 linhas
        st.markdown(" ".join(linha))
else:
    st.info("Nenhum resultado registrado ainda")

st.markdown("---")

# Análise e sugestão
if st.session_state.historico:
    historico_list = list(st.session_state.historico)
    padrao, confianca = detectar_padrao(historico_list)

    # Informações do padrão (buscar pela chave exata)
    info = PADROES_INFO.get(padrao, {
        "numero": "?",
        "emoji": "❔",
        "descricao": "Padrão não identificado."
    })

    aposta, explicacao = sugerir_aposta(padrao, historico_list, confianca)

    st.markdown(f"**Padrão Detectado: {info['numero']}. {padrao} {info['emoji']}**")
    st.write(info["descricao"])

    # Mostrar confiança como métrica
    st.metric("Confiança da Detecção", f"{confianca}%")
    # Barra de progresso (0-1) — convertendo
    try:
        st.progress(confianca / 100.0)
    except Exception:
        # fallback se a API do Streamlit aceitar 0-100
        st.progress(confianca)

    # Exibir sugestão de aposta com tipo de mensagem adequado
    if isinstance(aposta, str) and aposta.startswith("Aposte"):
        st.success(f"**Sugestão de Aposta:** {aposta}")
    elif isinstance(aposta, str) and (aposta.startswith("Evitar") or aposta.startswith("Aguardar") or aposta.startswith("Sem")):
        st.warning(f"**Recomendação:** {aposta}")
    else:
        st.info(f"**Recomendação:** {aposta}")

    st.info(f"**Explicação:** {explicacao}")
else:
    st.info("Insira resultados para começar a análise")

st.markdown("---")
st.write("Analisador de padrões Football Studio - Use com responsabilidade")
