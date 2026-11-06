# NFSMW Android — PRE251 análise do log da V37 (2026-11-06)

**Entrada:** arquivo `nfsmw.log` anexado pelo usuário, SHA-256 `194ee95720387fe29fe638512552a219c02483a6c23086557bd21d7ce934c052`, tamanho 510.254 bytes / 2.060 linhas, período 19:56:51.606–19:59:01.114 (129,5 s).

## Constatações verificadas

- Jogo abriu o menu e alcançou `[contexto] conduciendo` (condução) às 19:57:27.541 e 19:58:15.861; o log termina com pausa por segundo plano às 19:59:01.082, não com crash fatal documentado.
- Resolução interna informada: 1920×1080; cap informado: 60 FPS. Várias medições em janela de ~10 s indicam ~600–601 quadros, o que não comprova melhoria causal de desempenho.
- 84 eventos `[NFSMW_PRE247_CHEATS_DIAG]` em **sete locais**: nitro PAL candidatos 1=12, 2=12, 3=12, 4=12, **5=0**; Speedbreaker PAL candidatos 6=12, 7=12, 8=12. Cada local alcançou o máximo de 12 entradas. Não afirmar identidade funcional definitiva dos medidores.
- Nitro: sites 1/2, endereço observado `0xBFAD110C`, valores float 0,996667→0,960000 nos ~184 ms iniciais; sites 3/4 mesmo endereço, 0,756787→0,758364 nos ~170 ms iniciais. Pares com gravações idênticas.
- Speedbreaker: sites 6/8, endereço `0xBFA7CD34`, 0,998333→0,977384 em ~200 ms; site 7 no mesmo endereço 0,568991→0,577908 em ~249 ms. O limite de 12 eventos impede inferir o comportamento após esses instantes.
- `[NFSMW_PRE246_CHEATS_DIAG]` **não apareceu** (0 eventos de escrita de dinheiro observados). Isso não demonstra falha do logger; as rotas podem não ter sido exercidas na sessão.
- **C3 permanece:** às 19:57:27.426, `[error] ... [NFSMW_PRE194_C3 indice_fuera=false referencia_distinta=false copia_duplicada=true]`, com thread auxiliar de vinculação de texturas desabilitada pelo resto da sessão, caindo no fallback. Causa raiz ainda indeterminada.
- Início: `PG9076_BOOT SDL joysticks=0` e `SDL gamepads=0`. Touch gamepad inicializou, mas controle físico PG-9076 não foi comprovado neste log.
- 227 avisos no log (174 contêm código de arquivo 0xC000000F) e **um** erro explícito, o C3; não equivalem automaticamente a travamento. Não há `SIGSEGV`/fatal identificado.

## Próxima ação

1. Preservar backup dos saves; testar **uma alteração real de saldo** em sessão controlada e trazer novo `nfsmw.log` para verificar sondas PRE246, sem declarar dinheiro infinito ou mexer no sistema de save.
2. Não aplicar cheats ainda: nitro e Speedbreaker têm candidatos dinamicamente acionados, mas sua semântica/segurança completa não foi validada.
3. Qualquer futura V38 exige nova autorização de build. Melhorar amostragem de registros por transição, não apenas as primeiras 12 chamadas, sem novas leituras de memória guest e sem alterar original stores.
4. Continuar investigação da falha C3 `copia_duplicada=true` em uma trilha separada.
5. Preservar release original e assinatura (SHA-256 `1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b`), `io.github.nfsmwrecomp`, V35/V36 e saves, shaders, 1920×1080, cap atual 60 FPS e proteções térmicas. Sem ganho de FPS ou cheats funcionais comprovados.
6. Próxima revisão do `CONTEXTO_NFSMW.md` no Drive deve anexar estas evidências, mantendo backup antes de modificar arquivo canônico.
