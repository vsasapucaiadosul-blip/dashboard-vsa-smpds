import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

st.set_page_config(page_title='Dashboard SMPDS | VSA', page_icon='📊', layout='wide')
BASE = Path(__file__).parent

@st.cache_data
def load_data():
    df = pd.read_csv(BASE / 'dados' / 'indicadores.csv', encoding='utf-8-sig')
    order = ['Junho/2026', 'Julho/2026', 'Agosto/2026']
    df['Competência'] = pd.Categorical(df['Competência'], categories=order, ordered=True)
    return df

df = load_data()

st.title('Monitoramento Socioassistencial — SMPDS')
st.caption('Vigilância Socioassistencial | Sapucaia do Sul/RS | Junho a Agosto de 2026')

with st.sidebar:
    st.header('Filtros')
    period = st.selectbox('Competência', ['Todos os meses'] + list(df['Competência'].cat.categories))
    protection = st.selectbox('Proteção', ['Todos'] + sorted(df['Proteção'].unique().tolist()))
    units = sorted(df.loc[df['Proteção'].eq(protection), 'Unidade'].unique()) if protection != 'Todos' else sorted(df['Unidade'].unique())
    unit = st.selectbox('Unidade', ['Todas'] + units)

f = df.copy()
if period != 'Todos os meses': f = f[f['Competência'].astype(str).eq(period)]
if protection != 'Todos': f = f[f['Proteção'].eq(protection)]
if unit != 'Todas': f = f[f['Unidade'].eq(unit)]


def get(ind, unit_name=None, month=None):
    x = df[df['Indicador'].eq(ind)]
    if unit_name: x = x[x['Unidade'].eq(unit_name)]
    if month: x = x[x['Competência'].astype(str).eq(month)]
    return None if x.empty else float(x.iloc[0]['Valor'])


def n(v):
    if v is None: return '—'
    return f'{int(v):,}'.replace(',', '.') if float(v).is_integer() else f'{v:,.1f}'.replace(',', 'X').replace('.', ',').replace('X', '.')

m = period if period != 'Todos os meses' else 'Agosto/2026'
k = st.columns(4)
if protection in ('Todos', 'Proteção Social Básica'):
    k[0].metric('Famílias PAIF', n(get('Famílias acompanhadas', 'Todos os CRAS', m)))
    k[1].metric('Atendimentos particularizados', n(get('Atendimentos particularizados', 'Todos os CRAS', m)))
else:
    k[0].metric('Famílias PAEFI ativas', n(get('Famílias ativas', 'CREAS', m)))
    k[1].metric('Atendimentos CREAS', n(get('Atendimentos totais', 'CREAS', m)))
k[2].metric('Usuários PSR', n(get('Usuários', 'População em Situação de Rua', m)))
benef = f[f['Indicador'].eq('Benefícios')]['Valor'].sum()
k[3].metric('Benefícios no filtro', n(benef) if len(f[f['Indicador'].eq('Benefícios')]) else '—')

st.divider()
t1, t2, t3, t4, t5 = st.tabs(['Visão geral', 'Proteção Básica', 'Proteção Especial', 'CRM / Segurança Alimentar', 'Gestão / Financeiro'])

with t1:
    st.subheader('Evolução dos principais indicadores')
    choices = [x for x in ['Famílias acompanhadas','Atendimentos particularizados','Famílias ativas','Atendimentos totais','Atendimentos','Usuários'] if x in f['Indicador'].unique()]
    if choices:
        ind = st.selectbox('Indicador', choices)
        g = f[f['Indicador'].eq(ind)].copy()
        if 'Todos os CRAS' in g['Unidade'].values: g = g[g['Unidade'].eq('Todos os CRAS')]
        elif 'CREAS' in g['Unidade'].values: g = g[g['Unidade'].eq('CREAS')]
        if not g.empty:
            fig = px.line(g.sort_values('Competência'), x='Competência', y='Valor', markers=True, title=ind)
            st.plotly_chart(fig, use_container_width=True)
    st.dataframe(f.sort_values(['Competência','Proteção','Unidade','Indicador']), use_container_width=True, hide_index=True)

with t2:
    st.subheader('Proteção Social Básica')
    b = df[df['Proteção'].eq('Proteção Social Básica')].copy()
    if period != 'Todos os meses': b = b[b['Competência'].astype(str).eq(period)]
    if unit != 'Todas' and unit in b['Unidade'].unique(): b = b[b['Unidade'].eq(unit)]
    a = b[b['Indicador'].eq('Famílias acompanhadas') & ~b['Unidade'].eq('Todos os CRAS')]
    if not a.empty:
        st.plotly_chart(px.bar(a, x='Unidade', y='Valor', color='Competência', barmode='group', title='Famílias acompanhadas pelo PAIF por CRAS'), use_container_width=True)
    a = b[b['Indicador'].eq('Atendimentos particularizados') & ~b['Unidade'].eq('Todos os CRAS')]
    if not a.empty:
        st.plotly_chart(px.bar(a, x='Unidade', y='Valor', color='Competência', barmode='group', title='Atendimentos particularizados por CRAS'), use_container_width=True)
    a = b[b['Indicador'].eq('Benefícios')]
    if not a.empty:
        st.plotly_chart(px.bar(a, x='Unidade', y='Valor', color='Competência', barmode='group', title='Benefícios Eventuais por unidade'), use_container_width=True)

with t3:
    st.subheader('Proteção Social Especial')
    a = df[df['Indicador'].isin(['Famílias ativas','Atendimentos totais','Visitas domiciliares','Medidas socioeducativas','Abordagens']) & df['Unidade'].eq('CREAS')]
    if period != 'Todos os meses': a = a[a['Competência'].astype(str).eq(period)]
    if not a.empty:
        st.plotly_chart(px.bar(a, x='Indicador', y='Valor', color='Competência', barmode='group', title='Indicadores do CREAS'), use_container_width=True)
    a = df[df['Unidade'].isin(['Alta Complexidade','População em Situação de Rua'])]
    if period != 'Todos os meses': a = a[a['Competência'].astype(str).eq(period)]
    st.dataframe(a.sort_values(['Competência','Unidade','Indicador']), use_container_width=True, hide_index=True)

with t4:
    crm = df[df['Unidade'].eq('CRM')]
    food = df[df['Unidade'].eq('Segurança Alimentar')]
    if period != 'Todos os meses':
        crm = crm[crm['Competência'].astype(str).eq(period)]; food = food[food['Competência'].astype(str).eq(period)]
    st.subheader('Centro de Referência da Mulher')
    if not crm.empty: st.plotly_chart(px.bar(crm, x='Indicador', y='Valor', color='Competência', barmode='group'), use_container_width=True)
    st.subheader('Segurança Alimentar — PAA')
    if not food.empty: st.plotly_chart(px.bar(food, x='Indicador', y='Valor', color='Competência', barmode='group'), use_container_width=True)

with t5:
    st.subheader('Cadastro Único')
    cad = df[df['Unidade'].eq('Cadastro Único')]
    if period != 'Todos os meses': cad = cad[cad['Competência'].astype(str).eq(period)]
    if not cad.empty: st.plotly_chart(px.line(cad, x='Competência', y='Valor', color='Indicador', markers=True), use_container_width=True)
    st.subheader('Gestão financeira')
    fin = df[df['Unidade'].isin(['FNAS','FEAS','FMAS'])]
    if period != 'Todos os meses': fin = fin[fin['Competência'].astype(str).eq(period)]
    saldo = fin[fin['Indicador'].isin(['Saldo FNAS','Saldo FEAS'])]
    pag = fin[fin['Indicador'].eq('Pagamentos registrados')]
    if not saldo.empty: st.plotly_chart(px.line(saldo, x='Competência', y='Valor', color='Indicador', markers=True, title='Saldos FNAS e FEAS'), use_container_width=True)
    if not pag.empty: st.plotly_chart(px.bar(pag, x='Competência', y='Valor', title='Pagamentos registrados'), use_container_width=True)
    st.warning('O PDF contém divergências internas que devem ser conferidas na base original antes de publicação: benefícios de julho (276 CRAS + 10 CREAS no cabeçalho versus 291 na seção detalhada) e médias por sexo da PSR em agosto.')

st.caption('Fonte: Relatórios Mensais de Monitoramento Socioassistencial — SMPDS/VSA — junho, julho e agosto de 2026.')
