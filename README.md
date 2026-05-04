# nettrace

Dashboard Streamlit para analise de eventos de rede ao longo do tempo, com foco em relacao entre IP e MAC.

## Visao Geral

O projeto tem dois blocos principais:

- Aplicacao Streamlit para explorar os dados (upload de um ou mais arquivos CSV/Excel).
- Script de coleta (`scripts/collector.sh`) para gerar CSVs periodicamente via `nmap`.

## Requisitos

- Python 3.13
- Poetry
- `nmap` (para o script coletor)

## Instalacao

```bash
poetry install
```

## Executando o Dashboard

```bash
poetry run streamlit run main.py
```

No app:

- Voce pode anexar 1 ou mais arquivos (`.csv`, `.xlsx`, `.xls`).
- Modo `IP`: eixo Y por MAC, com default de IPs que aparecem com mais de 1 MAC.
- Modo `MAC`: eixo Y por IP, com default de MACs que aparecem com mais de 1 IP.

## Formato Esperado dos Dados

Colunas necessarias:

- `Timestamp`
- `IP`
- `MAC`

Observacoes:

- `Timestamp` e convertido para datetime; linhas invalidas sao descartadas.
- O filtro de datas considera o dia inteiro de `Start Date` e `End Date`.

## Script Coletor (`scripts/collector.sh`)

O script faz scan de rede e gera arquivos CSV diarios no formato:

- `scan_YYYY-MM-DD.csv`

Com colunas:

- `Timestamp,IP,MAC`

### Uso

```bash
bash scripts/collector.sh -n <rede_cidr> [-o <diretorio_saida>]
```

Exemplo:

```bash
bash scripts/collector.sh -n 192.168.1.0/24 -o /home/seu_usuario/logs_rede
```

Parametros:

- `-n` obrigatorio: rede no formato CIDR (`192.168.1.0/24`, por exemplo).
- `-o` opcional: diretorio de saida (default: `$HOME/logs_rede`).

### Agendamento com Cron (a cada 10 minutos)

Como o `nmap -PR` normalmente exige privilegios elevados, configure no crontab do root:

```bash
sudo crontab -e
```

Adicione:

```cron
*/10 * * * * /bin/bash /caminho/absoluto/nettrace/scripts/collector.sh -n 192.168.1.0/24 -o /home/seu_usuario/logs_rede
```

Notas importantes:

- Se usar root e nao passar `-o`, o default sera `/root/logs_rede` (por causa do `$HOME` do root).
- O script possui lockfile em `/tmp/collector_nettrace.lock` para evitar sobreposicao de execucoes.

## Estrutura do Projeto

- `main.py`: entrypoint do Streamlit (navegacao com uma unica pagina).
- `pages/IP_MAC.py`: pagina principal de analise (modo IP/MAC).
- `scripts/collector.sh`: coleta periodica de dados de rede e geracao de CSV.
- `netlogs.csv`: exemplo de dados.

## Troubleshooting Rapido

- `nmap: command not found`:
  instale `nmap` no host que executa o coletor.
- CSV vazio:
  confira rede CIDR, permissao de execucao e conectividade da rede.
- Dashboard sem dados:
  valide se os arquivos possuem colunas `Timestamp`, `IP` e `MAC`.
