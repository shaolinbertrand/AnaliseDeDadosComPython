import pandas as pd
import streamlit as st
import plotly.express as px # Importando Plotly Express

# --- Carregamento dos Dados ---
# Assumindo que 'exportacoes_franca.csv' sempre será carregado sem erros.
try:
    tabela = pd.read_csv('exportacoes_franca.csv')
except FileNotFoundError:
    st.error("Erro: O arquivo 'exportacoes_franca.csv' não foi encontrado. Por favor, verifique o caminho do arquivo.")
    st.stop() # Interrompe a execução se o arquivo não for encontrado

st.title("📊 Dashboard de Exportações para a França")

# --- Sidebar para Seleção de Cidades ---
# Garante que 'City' existe antes de tentar acessá-lo
if 'City' in tabela.columns:
    cidades = tabela['City'].unique().tolist()
    cidades.sort() # Ordena as cidades alfabeticamente na sidebar
else:
    st.error("Erro: A coluna 'City' não foi encontrada no arquivo de dados.")
    cidades = [] # Define cidades como vazia para evitar erros posteriores

st.sidebar.header("Filtro por Cidades")

cidades_selecionadas = {}
for cidade in cidades:
    cidades_selecionadas[cidade] = st.sidebar.checkbox(cidade, value=False)

# --- Exibição das Cidades Selecionadas e Geração de Gráficos ---
st.write("---")
st.header("Cidades Selecionadas")

cidades_escolhidas = [cidade for cidade, selecionado in cidades_selecionadas.items() if selecionado]

if cidades_escolhidas:
    st.write("Você selecionou as seguintes cidades:")
    for cidade in cidades_escolhidas:
        st.write(f"- {cidade}")

    # Filtra o DataFrame com base nas cidades selecionadas
    df_filtrado = tabela[tabela['City'].isin(cidades_escolhidas)].copy()

    st.write("---")
    st.header("Análises Gráficas")

    # 1. Gráfico: Valor exportado por cidade (AGORA COM PLOTLY EXPRESS)
    st.subheader("1. Valor Exportado por Cidade Selecionada")
    # Agrupa por cidade e soma o valor FOB
    valor_por_cidade = df_filtrado.groupby('City')['US$ FOB'].sum().reset_index()

    if not valor_por_cidade.empty:
        fig_bar_h = px.bar(
            valor_por_cidade.sort_values('US$ FOB', ascending=True),
            x='US$ FOB',
            y='City',
            orientation='h', # Barras horizontais
            title='Valor Exportado por Cidade',
            labels={'US$ FOB': 'Valor US$ FOB', 'City': 'Cidade'},
            color='US$ FOB', # Colore as barras com base no valor
            color_continuous_scale='YlGnBu', # Paleta de cores
            hover_data={'US$ FOB': ':.2f'} # Formata o valor no hover para 2 casas decimais
        )
        fig_bar_h.update_layout(title_x=0.5) # Centraliza o título
        st.plotly_chart(fig_bar_h, use_container_width=True)
    else:
        st.info("Nenhum dado para o Gráfico 1 nas cidades selecionadas.")


    # 2. Gráfico: Distribuição por SH2 (Donut - AGORA COM PLOTLY EXPRESS)
    st.subheader("2. Distribuição do Valor Exportado por Categoria SH2 (Donut)")
    distribuicao_sh2_donut = df_filtrado.groupby('SH2 Description')['US$ FOB'].sum().reset_index()

    if not distribuicao_sh2_donut.empty:
        # --- Passo 1: Agrupar categorias pequenas em "Outros" ---
        total_fob = distribuicao_sh2_donut['US$ FOB'].sum()
        limiar_percentual = 0.02 # Categorias abaixo de 2% serão agrupadas

        pequenas_categorias_df = distribuicao_sh2_donut[distribuicao_sh2_donut['US$ FOB'] / total_fob < limiar_percentual]
        if not pequenas_categorias_df.empty:
            distribuicao_sh2_donut = distribuicao_sh2_donut[distribuicao_sh2_donut['US$ FOB'] / total_fob >= limiar_percentual]
            outros_fob = pequenas_categorias_df['US$ FOB'].sum()
            distribuicao_sh2_donut = pd.concat([distribuicao_sh2_donut,
                                                pd.DataFrame([{'SH2 Description': 'Outros (<{:.0%})'.format(limiar_percentual),
                                                               'US$ FOB': outros_fob}])],
                                               ignore_index=True)
        # --- Fim do agrupamento ---

        fig_donut = px.pie(
            distribuicao_sh2_donut,
            values='US$ FOB',
            names='SH2 Description',
            title='Distribuição do Valor Exportado por Categoria SH2',
            hole=0.4, # Cria o efeito de donut
            color_discrete_sequence=px.colors.qualitative.Pastel, # Paleta de cores para categorias
            hover_data={'US$ FOB': ':.2f'} # Exibe o valor no hover
        )
        fig_donut.update_traces(textposition='inside', textinfo='percent+value') # Mostra % e valor dentro das fatias
        fig_donut.update_layout(title_x=0.5) # Centraliza o título
        st.plotly_chart(fig_donut, use_container_width=True)
    else:
        st.info("Nenhum dado de SH2 para as cidades selecionadas.")

    st.subheader("2.1 Distribuição do Valor Exportado por Categoria SH2 (Heatmap)")

    # O heatmap já era Plotly Express, apenas garantindo que o hover_data seja eficaz
    distribuicao_sh2_heatmap = df_filtrado.groupby(['City','SH2 Description'])['US$ FOB'].sum().reset_index()

    fig_heatmap = px.density_heatmap(
        distribuicao_sh2_heatmap,
        x='City',
        y='SH2 Description',
        z='US$ FOB',
        color_continuous_scale='PuRd',
        title='Distribuição do Valor Exportado por Categoria (Heatmap)',
        hover_data={'US$ FOB': ':.2f'} # Exibe o valor no hover
    )
    fig_heatmap.update_layout(title_x=0.5)
    st.plotly_chart(fig_heatmap, use_container_width=True)

    # 3. Gráfico: Top 5 produtos mais exportados nas cidades selecionadas (AGORA COM PLOTLY EXPRESS)
    st.subheader("3. Top 5 Produtos Mais Exportados nas Cidades Selecionadas (SH4 Description)")
    # Agrupa por SH4 Description, soma o valor FOB e pega os 5 maiores
    top_5_produtos = df_filtrado.groupby('SH4 Description')['US$ FOB'].sum().nlargest(5).reset_index()

    if not top_5_produtos.empty:
        fig_bar_h_top5 = px.bar(
            top_5_produtos.sort_values('US$ FOB', ascending=True),
            x='US$ FOB',
            y='SH4 Description',
            orientation='h',
            title='Top 5 Produtos Exportados',
            labels={'US$ FOB': 'Valor US$ FOB', 'SH4 Description': 'Produto'},
            color='SH4 Description', # Colore por produto
            color_discrete_sequence=px.colors.qualitative.Bold, # Paleta de cores para categorias
            hover_data={'US$ FOB': ':.2f'} # Exibe o valor no hover
        )
        fig_bar_h_top5.update_layout(title_x=0.5) # Centraliza o título
        fig_bar_h_top5.update_yaxes(showticklabels=False) # Remove os nomes do eixo Y
        st.plotly_chart(fig_bar_h_top5, use_container_width=True)
    else:
        st.info("Nenhum produto para exibir nas cidades selecionadas.")


    # 4. Gráfico: Relação valor vs peso líquido (AGORA COM PLOTLY EXPRESS SCATTERPLOT)
    st.subheader("4. Relação Valor (US$ FOB) vs. Peso Líquido (Net Weight)")
    if not df_filtrado.empty:
        fig_scatter = px.scatter(
            df_filtrado,
            x='Net Weight',
            y='US$ FOB',
            color='City', # Cor por cidade
            size='US$ FOB', # Tamanho do ponto por US$ FOB
            title='Relação Valor vs. Peso Líquido por Cidade',
            labels={'Net Weight': 'Peso Líquido', 'US$ FOB': 'Valor US$ FOB'},
            hover_data={'City': True, 'US$ FOB': ':.2f', 'Net Weight': ':.2f', 'SH2 Description': True, 'SH4 Description': True} # Dados adicionais no hover
        )
        fig_scatter.update_layout(title_x=0.5)
        st.plotly_chart(fig_scatter, use_container_width=True)
    else:
        st.info("Nenhum dado para a relação Valor vs. Peso Líquido nas cidades selecionadas.")

else:
    st.info("Nenhuma cidade selecionada ainda. Por favor, selecione uma ou mais cidades na barra lateral para ver as análises.")
