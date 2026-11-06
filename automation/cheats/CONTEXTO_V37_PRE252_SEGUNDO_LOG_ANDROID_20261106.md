# NFSMW Android — PRE252: segundo teste físico V37 (2026-11-06)

## Evidência e escopo
- Arquivo enviado pelo usuário: `nfsmw.log`, **1.943.265 bytes**, **6.604 linhas**, SHA-256 `a5e763c0be4cdd6199478002d4e701c1994e372e63f85bb1734894cb575c6c33`.
- Intervalo: **20:04:29.214–20:16:25.351**, aproximadamente **11 min 56 s**, novo processo do app `io.github.nfsmwrecomp`.
- Cópia íntegra preservada na pasta privada de logs do Drive (`06_Logs_e_Medicoes`): https://drive.google.com/file/d/1MJ1aD-4BL6OCmNDhGX1k58jZcW9fQgEa/view ; tamanho no Drive confirmado igual.
- Comparação: PRE251 (sessão ~19:56:51–19:59:01) apresentava os mesmos 84 registros do medidor e zero registros de dinheiro.

## Sondas de recursos
- `NFSMW_PRE246_CHEATS_DIAG` (8 stores de dinheiro PAL): **0 linhas**. Nenhuma transação monetária pode ser inferida exclusivamente dos logs de save; a cobertura de compras/débitos da PRE246 continua **não validada**.
- `NFSMW_PRE247_CHEATS_DIAG`: **84 linhas**. Sites 1, 2, 3, 4 = **12 cada** (48 candidatos nitro); site 5 = **0**; sites 6, 7, 8 = **12 cada** (36 candidatos Speedbreaker).
- Os 7 sites acionados atingiram o limite **12/site**, logo o traço **não acompanha** mudanças posteriores da sessão.
- Aritmética observada: sites 1/2 gravaram valores float decrescentes ~0,996667→0,960000 no endereço runtime `0xBFACE77C`; sites 3/4 valores crescentes ~0,840556→0,846667 no mesmo endereço. Sites 6 gravaram ~0,998333→0,979222 em `0xBFA7CD34`; sites 7/8 incluem valores ~1,000667 e 1,000000. Endereços são runtime; **não usar como endereço constante de cheat**.
- A detecção de candidatos em tempo de execução não comprova semântica exata, segurança de não-decréscimo nem cheat funcional.

## Jogo, gráficos, saves e estabilidade
- Primeiro `[contexto] conduciendo` às 20:09:56.114; diversas transições condução/cinemática/pausa até 20:16:24; processo foi colocado em segundo plano às 20:16:25. Sem `SIGSEGV`/fatal no arquivo.
- Logs de save (`[guardado]`) aparecem **87 vezes**, com escritas e cópias ao longo da sessão; **não provam compra, débito, crédito ou saldo**, nem validam o valor gravado no save.
- Falha gráfica C3 recorrente: **20:09:56.095**, `NFSMW_PRE194_C3 indice_fuera=false referencia_distinta=false copia_duplicada=true`, thread auxiliar de vinculação de texturas desativada e fallback usado. Causa raiz não resolvida.
- **1 `[error]`**, referente a C3; **332 `[warning]`**, muitos relacionados a caminhos de arquivos ausentes (por exemplo `0xC000000F`), não concluir crash a partir destes.
- Resolução interna **1920×1080**, limite registrado **60 FPS**; saída configurada 1280×720@60. O log não comprova ganho causal de FPS.
- `PG9076_BOOT SDL joysticks=0` e `SDL gamepads=0` na inicialização; não comprova input físico PG-9076 na sessão.

## Conclusões e próxima etapa
1. **V37 diagnóstica está executando em Android**, com 7/8 sondas de medidores acionadas, mas todas limitadas pelo teto de 12 mensagens.
2. **Cheats continuam desativados**; dinheiro não observado em dois logs consecutivos, incluindo esta sessão mais longa.
3. Perguntar objetivamente se o usuário realizou **compra com gasto real** nesta sessão. Se não, pedir uma pequena compra após backup dos saves e novo log; se sim, **reavaliar a cobertura dos caminhos de débito** em análise estática e considerar V38 com instrumentação passiva diferente. Não aplicar alterações cegas a endereços guest.
4. Melhorar observabilidade da versão futura: registrar transições/amostras em momentos espaçados em vez de somente primeiras 12 entradas, com limitação global de custo e sem leituras extras da memória guest; sujeita a auditoria e autorização específica de compilação.
5. Seguir a trilha independente de C3 `copia_duplicada=true`; preservar V35/V36/V37, saves, assinatura permanente SHA-256 `1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b`, `versionCode` crescente, 1920×1080, gráficos, shaders, física, controle e proteção térmica.
6. Anexar este adendo ao `CONTEXTO_NFSMW.md` canônico do Drive após backup e confirmação da versão atual. Não confundir diagnóstico PRE252 com comprovação de cheats funcionais.
