# NFSMW Android — PRE253: primeira gravação real de saldo, compra do primeiro carro (2026-11-06)

## Fonte, integridade e sessões
- Usuário afirmou **"Comprei o carro inicial"** e forneceu `nfsmw.log`.
- Log completo analisado localmente: **3.556.683 bytes, 12.321 linhas**, SHA-256 **`39803abc313b2d1e9748a2c17a9cfcd5cf77453526feed475c07d4a4b874531f`**.
- O log contém o prefixo **byte a byte idêntico** ao PRE252 anterior de **1.943.265 bytes**, SHA-256 **`a5e763c0be4cdd6199478002d4e701c1994e372e63f85bb1734894cb575c6c33`**. Logo, separar sessões e NÃO somar 156 medidores como se fossem desta execução.
- **Nova sessão isolada:** intervalo **20:21:56.745–20:33:25.518**, 1.613.418 bytes, 5.717 linhas, SHA-256 **`55447ce152bb81d6c81e1a447c522c65a5ef54d765814c76f9b696f5940b3fc6`**.
- Log integral preservado na pasta privada `06_Logs_e_Medicoes` do Drive: https://drive.google.com/file/d/1qM0jz1jF_toj1EwoklPD3vpAd-I89IUD/view (upload confirmado).

## Principal evidência — saldo observado
- **20:33:15.910**, linha **12129 do log completo**, linha **5525 da nova sessão**:
```text
[2026-11-06 20:33:15.910] [info] [core] [t5455] [NFSMW_PRE246_CHEATS_DIAG] money site=8 addr=0xAD68F09C previous=30000 written=3000
```
- Registro `site=8` corresponde ao **5º store** instrumentado em **`sub_82564D80` PAL**, `stw r5,12(r11)` / `REX_STORE_U32(ctx.r11.u32 + 12, ctx.r5.u32)`, PC candidato auditado `0x8256608C`. O valor anterior vem do registro `r10` identificado pela PRE240; o logger executa **após a gravação original** e não adiciona leitura guest.
- Valores observados: anterior **30.000**, gravado **3.000**, redução calculada **27.000**. O usuário afirma que comprou o primeiro carro na sessão, e a gravação ocorreu aproximadamente **21 s após entrar no estado `menus` às 20:32:54.583**, com retorno ao estado `conduciendo` às **20:33:18.185**. Isso é **forte evidência correlacional de débito associado à compra**, mas o log não informa diretamente o preço na interface nem prova que toda transação de dinheiro usa esse mesmo store.
- Endereço guest observado `0xAD68F09C` é de runtime; **não transportar como constante**, nem confundir com o endereço de Max Money `0xAD63F09C` do TeamXPG. Divergência merece estudo de dinâmica dos objetos, não extrapolação de endereço.
- A primeira oportunidade de gasto monitorada deu resultado que não apareceu nas sessões anteriores sem compra (PRE251/252). **Nenhum cheat foi aplicado ou ativado**.

## Outras observações da nova sessão
- `NFSMW_PRE246_CHEATS_DIAG`: 1 evento, somente `site=8`.
- `NFSMW_PRE247_CHEATS_DIAG`: 72 eventos, sites 1/2/3/4/7/8 com **12 cada**, sites 5/6 não observados nesta sessão; todos os acionados chegaram ao teto de 12 e não mostram atividade posterior.
- C3 continua com `copia_duplicada=true`, às **20:27:27.465**, desligando thread auxiliar de texturas; não é corrigido por cheats.
- O watchdog `[vigilante]` registrou **oito mensagens principais de estagnação** (cada uma afirmando 5 s sem progresso em nenhum dos 17 hilos) entre **20:24:33 e 20:26:38**. Essas mensagens geraram **198 linhas [error] de diagnósticos de threads**, além de **1 linha de erro C3**. Não interpretar 199 linhas como 199 falhas independentes; houve atividade depois e compra registrada. Não diagnosticar causa de congelamento com o dado atual.
- Sem texto `SIGSEGV` ou `[fatal]` nesta sessão. O log termina às 20:33:25 sem evento de encerramento fatal detectado; não comprova ausência de falhas fora do registro.
- Touch/PG9076, resolução 1920×1080, cap atual 60 FPS, gráficos, shaders, física, saves e limites térmicos não foram modificados pela análise.

## Implicação para os cheats e próximo passo
1. **Foi encontrado ao menos um caminho real de redução do saldo** na compra. Isso permite direcionar auditoria de semântica para o PC e o store 8 PAL sem leituras guest adicionais.
2. Não aplicar automaticamente política `max(previous, written)` nem NOP do store 8 em release: impedir o débito pode interferir no estado da compra, no save ou no resultado da transação. Analisar ramos de débito, crédito, outras operações e rollback.
3. Em um teste posterior, com save respaldado, conferir o preço do carro e saldo exibido (espera-se diferença de 27.000) e observar **recebimento de recompensa ou crédito**; verificar se usam um dos outros 7 stores ou este mesmo.
4. Somente depois preparar protótipo **reversível, desligado por padrão** em build futura V38 (sem autorização de compilação ainda), com assinatura permanente original, package `io.github.nfsmwrecomp`, `versionCode >= 38`, backup de saves. Nenhum ganho de FPS ou cheat funcional comprovado.
5. Registrar esta evidência no contexto histórico canônico `CONTEXTO_NFSMW.md` **com backup primeiro**; o estado de referência atualizado deve distinguir **V37 instalada e testada no aparelho**, `1` redução real de saldo observada, C3 e watchdog pendentes.

## Certificado permanente
SHA-256 `1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b`. Nunca recriar chave nem tocar em credenciais.
