# PRE326 — Correlação passiva de endereços do Nitro (2026-11-07)

## Por que esta etapa
A fonte confirmada da instrumentação PRE247, `automation/kaggle/pre247_pal_meter_passive_probe_patch.py`, já emite `[NFSMW_PRE247_CHEATS_DIAG] meter_candidate=N addr=0x... written_f32_bits=0x...` **após a gravação original**, sem nova leitura guest. PRE321 verificou que o log do S24 FE apresenta o ciclo de consumo e recarga via PRE316, mas não analisou a identidade dos endereços da PRE247.

## Arquivos publicados
- `automation/kaggle/pre326_nitro_address_correlation_readonly.py`: recebe um log como entrada, reconhece os sites 1–5, conta endereços distintos por site e interseções entre sites; descarta sites 6–8 (Speedbreaker).
- `automation/kaggle/pre326_nitro_address_correlation_mock.py`: dez verificações sintéticas declaradas; resultado CI ainda pendente.
- `.github/workflows/nfsmw-pre326-nitro-address-correlation-mock.yml`: runner GitHub Actions sem credenciais.
- Commit de disparo PRE326: `3abb6d349613b10c6a8fc1ce91307f7bec4a38d7`.

## Integridade
O analisador é somente leitura do arquivo de entrada e produz JSON agregado, sem publicar endereços brutos. Não acessa Google Drive, GitHub secrets ou dados de assinatura; não recompila nem instala APK e não altera `MARCEK`.

## Limitações
- PRE247 limita volume a 12 registros/site por processo. A ausência de um endereço nos logs **não comprova** que aquele objeto nunca foi atualizado.
- O `nfsmw.log` da PRE321 concatena sessões antigas; sem segmentação por sessão, sobreposições de endereços podem representar somente reutilização. Uma mesma localização do medidor entre sites 1–4 **não prova** que o carro é do jogador.
- O log bruto PRE321 com SHA-256 `ac17e87607723c6f98b5a553b4e7c4c99ad8a0b968eea8c6af0bb1f235b4c9bc` foi mencionado no relatório anterior, mas **não estava acessível** para execução do analisador nesta etapa. Nenhum resultado real de endereço foi afirmado.
- PRE325 e PRE325B tiveram correções/publicações no GitHub, mas suas execuções ainda não tiveram logs/artefatos confirmados nesta conversa.
- Não criar V42 nem habilitar Nitro infinito antes de validar identidade/owner e semântica do limite e garantir opt-in fail-closed OFF=original.

## Próximos gates
1. Conferir os artefatos e logs dos workflows PRE325/PRE325B/PRE326.
2. Recuperar o log bruto V41 previamente analisado, verificar o SHA-256 e executar PRE326 em cópia local.
3. Se houver dados suficientes, comparar destinos de store na sessão controlada; se não, preparar instrumentação adicional com identificação contextual do carro do jogador, ainda passiva, limitada e reversível.
