# PRE620 — hash completo do par ZDIR/ZZDATA4 PRE607 confirmado pelo usuário no Galaxy S24 FE (2026-11-09)

## Confirmação nova, somente leitura

O usuário executou `sha256sum` nos dois arquivos ativos em `/storage/emulated/0/NFSMW_PTBR/NFS` no Samsung Galaxy S24 FE e enviou as saídas textuais:

```text
f15d5da54148e0e762f65004d534092dbf3c08d12b0f8b710d6cf599235a32e2  /storage/emulated/0/NFSMW_PTBR/NFS/ZDIR.BIN
1ed79d0f031d400002da8db6153ee84188d717e33f093a501f7a6bdfc0e5e146  /storage/emulated/0/NFSMW_PTBR/NFS/ZZDATA4.BIN
```

Essas duas somas SHA-256 coincidem **byte a byte com os valores integrais previstos** e publicados pelo PRE606/PRE607 (`docs/PRE606_BMW_CORRECTED_PARENT_PRIVATE_PTBR_METADATA.json`, `automation/device/pre607_apply_bmw_child_parent_corrected_shevery.sh`) e anotados em PRE617. **Resultado:** identidade dos dois arquivos ativos **PRE607_CONFIRMED_BY_USER_SHA256**, e não mera inferência de que o script anterior foi executado. Os comandos não alteram os arquivos do jogo, APK nem saves.

**Limite importante:** os hashes atestam os arquivos no armazenamento nesse momento, mas **não provam leitura efetiva de um bloco específico `GLOBAL/ATTRIBUTES.BIN` ou a ativação/uso de `pvehicle.engine_upgrades=1` pelo guest**. O log PRE617 não mostrou um hash VPAK lido pelo engine, nem marcadores específicos de consulta ao novo export.

## Comparação com o sintoma já estabelecido

`nfsmw.log` anterior anexado, realmente lido: 3.937.714 B, 15.827 linhas, SHA256 `dc9fc0bb08ba943ede3e7675570c1c1fb15ddb5db743cee74edda4393109de0e`, com último menu BMW M3 GTR `type=41` às 15:06. A rotina de leitura original PAL `sub_823E5988` produziu `PRE447_ROUTE reason=2` para as sete consultas. O vetor `NFSMW_PRE429_LEVEL` foi:

| Tipo | Classe | Quantidade obtida |
|---|---|---|
| 4 | Motor | 0 |
| 3 | Transmissão | 0 |
| 2 | Suspensão | 0 |
| 6 | Nitro | 3 |
| 0 | Pneus | 0 |
| 1 | Freios | 0 |
| 5 | Indução | 0 |

Esse mesmo padrão foi observado na V47 PRE444 (BMW), e é diferente do Punto tipo 74 com contagens positivas. O rótulo `Option Title` aparece no menu segundo o usuário mas não no texto do log; associação à ausência de opções é uma inferência sustentada pela coincidência dos seis zeros, não mapeamento exato do ID de texto.

Com `PRE607_CONFIRMED_BY_USER_SHA256`, **a investigação deixa de priorizar erro de cópia ou restauração dos arquivos** e concentra-se na **semântica de lookup de atributos e geração de lista/pacotes do front-end**, incluindo a possibilidade de que o código guest não esteja consumindo a alteração VLT. Não forçar `candidate_count=4`, não fabricar itens, não comprar opções `Option Title`. PRE526 evidencia risco de preço sem instalação se `SetPackage` falhar no caminho PC reconstruído; isso não prova equivalência do guest Xbox.

## Próximo gate (a preparar/analisar em fonte antes de qualquer APK nova)

Inspecionar instruções e chamadas originais da cadeia PAL `sub_82582F70 → sub_8256F818 → sub_823E5988 → sub_8214B858 / sub_8214EDA8`, isolando qual atributo/descritor é consultado para `category 4` e por que o retorno é 0 na BMW, usando uma prévia de instrumentação passiva nos registros **já calculados** (`ctx.r3/r4/lr`) sem chamadas guest ou carregamentos/escritas extras, evitando sobrescrever o estado de guest.

O PRE447 já tem instrumentação `reason=2` na V48; a próxima instrumentação deve acrescentar informação **não redundante**, mantendo V48 intacta até revisão das instruções exatas. O hash do disco não basta para declarar que `pvehicle` foi utilizado.

Estado dispositivo: PRE607 ativa **confirmada por usuário por dois hashes**; perfil novo `NAME` com BMW importada; BMW abre oficina; 6 categorias com 0 e Nitro 3, tunagem BMW ainda NÃO funcional; resultado de compra/instalação/física/salvamento de upgrades NÃO demonstrado.

Regras imutáveis: pacote release `io.github.nfsmwrecomp`, APK V48 PRE452, certificado permanente SHA-256 `1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b`, Nitro PRE398, PG9076/touch, 1920×1080, meta 120 FPS, gráficos/shaders/efeitos, física geral, proteção térmica e backups originais; não regenerar assinatura, não limpar saves, não restaurar PRE607 sem motivo técnico.
