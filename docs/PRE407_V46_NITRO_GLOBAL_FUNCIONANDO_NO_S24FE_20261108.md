# PRE407 — V46: Nitro infinito global comprovado no Galaxy S24 FE (2026-11-08)

## Comprovação de funcionamento real

- Usuário relatou expressamente: **"Deu certo"** após instalar/testar V46 PRE401 com Nitro global para todos os carros. A experiência do jogador está confirmada por seu relato.
- Novo `nfsmw.log` recebido nesta conversa e analisado como bytes locais: **529.809 bytes, 2.238 linhas**, SHA-256 **`f7955f5e7dcd69dec69660e3c2a50ceb41dd779b9952f3f2c1169713e338fbd7`**; log inicia **2026-11-08 00:14:05.210** e termina **00:16:06.986**.
- Marcador `NFSMW_PRE398_GLOBAL_NITRO_FULL` presente **uma vez**, 00:14:30.053: `active=1 affects_all_objects=1 full_bits=0x3F800000`. Este registro é marcador do patch global, não identificação semântica individual de veículos.
- `NFSMW_PRE348_NITRO_SLOT_VALUES`: **82 amostras de 82 com `written_f32_bits=0x3F800000` (float 1,0 = 100%)**. Não há qualquer checkpoint PRE348 abaixo de 100% neste log.
- Distribuição: **quatro slots efêmeros** identificados pela PRE336, `distinct=4`, `overflow=false`; sites 1 e 2 para cada slot. Slot 1: 10+10 checkpoints; slot 2: 11+11; slot 3: 10+10; slot 4: 10+10. Os dois sites são do Nitro. Observações ao longo do período 00:14:30.053–00:16:06.599. Isso comprova múltiplos destinos recebendo 100% e corrobora efeito global, sem provar que cada um dos 4 é um adversário específico.
- `NFSMW_PRE316_NITRO_CYCLE`: 24 registros; min, max e último valor amostrado todos `0x3F800000` nos sites Nitro apresentados. PRE383 44 registros de LR, PRE364 65 eventos XInput, incluindo 6 eventos de `buttons=0x2000`.
- **Conclusão qualificada:** **Nitro infinito global funcional no jogo para o usuário, confirmado por relato e logs**. Os quatro destinos observados receberam 100% no código alterado. **Não comprovado** que todos os veículos possíveis/IA em cada situação tenham sido individualmente testados ou que não existam rotas alternativas de Nitro em outros contextos.

## Outras observações e ressalvas

- Aviso **PRE194 C3** continua, às **00:14:26.183**: `copia_duplicada=true`, e o hilo de enlaces de texturas ficou desligado no restante da sessão. A ocorrência é de texturas e deve ser tratada em investigação separada; **não atribuir ao patch Nitro sem evidência**. Não houve `FATAL EXCEPTION` ou `SIGSEGV` textual no arquivo, o que não garante ausência de outros problemas.
- O jogo reporta **resolução interna 1920×1080** e **limite de 60 FPS**, não há ganho FPS comprovado nem meta de 120 atingida.
- A compilação, integridade ZIP, assinatura permanente e upload APK já tinham sido validados na PRE405: V46, `versionCode=46`, pacote `io.github.nfsmwrecomp`, certificado SHA256 `1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b`, APK SHA256 `ac3676127d922b3c981aac6fffb87690c64bb9c0139fb983bd3ad8e017459eb7`, Drive `1UEmKsia6yhGBleO9eCFkeLbRz54myj4M`.
- Nenhuma evidência de alteração de save `MARCEK` no log; isso é diferente de comprovar seu backup. V45 segue fallback. Não criar chave ou mudar controles, shaders, resolução, física, thermal.

## Decisão e continuidade

- **Encerrar investigação de owner player-only para Nitro**, porque o usuário aceitou efeito global e esse cheat foi agora testado com sucesso. Não prometer que a IA será beneficiada em todo cenário sem observação específica.
- **Não é necessário uma V47 apenas para Nitro**. Próximo trabalho opcional pode focar problemas independentes (C3 texturas) ou outras funcionalidades **somente conforme pedido do usuário**, mantendo PRE398 como baseline funcional.
- Relatório local detalhado: `PRE407_V46_NITRO_GLOBAL_TESTE_REAL.json` gerado com as contagens e hash do novo log.
