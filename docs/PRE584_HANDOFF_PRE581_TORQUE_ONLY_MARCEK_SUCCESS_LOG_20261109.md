# PRE584 — TESTE REAL POSITIVO COM PRE581 TORQUE-ONLY E MARCEK (2026-11-09)

**Relato direto do usuário:** após executar o script PRE581 no Shevery e obter `PRE581_RESULTADO=ARQUIVOS_EXPERIMENTAIS_APLICADOS` (dados de saída fornecidos no chat), o usuário confirmou **"Consegui carregar agora"** e anexou um novo arquivo `nfsmw.log`. A conclusão de que a carreira carregou vem do usuário; `XamContentCreate` sozinho somente confirma abertura do contêiner.

## Log inspecionado nesta etapa

- Arquivo recebido no chat `nfsmw.log`: **217.837 bytes**, **1.303 linhas**, SHA256 `c7f3cf03d26c35b3f51a4dda1109034dc0ffe31de5e5f7f4e6ac32e760265af1`. **Não publicado como binário no GitHub/Drive.**
- O arquivo contém **DUAS sessões concatenadas**: primeira a partir de `01:42:45` (baseline de PRE579), segunda começa em `2026-11-09 01:58:25.385` (V48 com PRE581 aplicado pelo usuário). Não contar eventos da sessão anterior como se fossem da PRE581.
- Sessão nova: linha 669: resolução interna **1920×1080** e limite ativo **60 FPS**, não 120.
- Sessão nova: linha 792: `/storage/emulated/0/NFSMW_PTBR` montada em `\\Device\\Harddisk0\\Partition1`, **24 entradas**, `solo lectura`. Baseline anterior registrava 22 entradas, mas **não inferir quais são os dois arquivos extras sem listagem**.
- Sessão nova: linha 883, às `01:58:27.266`: leitura de **697.856 bytes de `NFS\\ZZDATA4.BIN` a partir do offset zero**. É exatamente a região/quantidade original do recurso `GLOBAL/ATTRIBUTES.BIN` cuja faixa inicial foi alterada na PRE580. Isso comprova *uma leitura de arquivo pelo runtime*, não revalida diretamente o hash do conteúdo nem o valor físico em memória.
- Sessão nova: linhas 1092, 1104, 1112 e 1127: `MARCEK`, **62.688 bytes**, em `rmcsave`; linhas 1094, 1106, 1114 e 1129 mostram `XamContentCreate ... resultado 00000000` nas quatro aberturas. Não há diagnóstico explícito no log de falha do perfil; usuário confirmou carregamento efetivo.
- Não foram observadas linhas `[error]` ou `[critical]`. Warnings `NtCreateFile` e registro `[pausa] juego y audio en pausa` às 01:58:40 não são demonstração de crash decorrente do pacote.
- A sessão PRE581 encerrou log enquanto o aplicativo entrava em segundo plano; isso não confirma aumento medido de potência, preço de oficina ou persistência.

## Comparação das variantes

| Dados da V48 / PT-BR | Evidência |
| --- | --- |
| Originais pós rollback PRE573 | O usuário confirmou a carreira `MARCEK` carregando; log de 112.350 B PRE579. |
| PRE573 / PRE572 sintético combinado: BMW counter 0→1, nova coleção, RefSpec, ExpN, PtrN, novo layout + motor +5% | Captura exibe `MARCEK está corrompido`. Não há prova de dano permanente ao save. |
| PRE580 / PRE581: mesma arquitetura VPAK original de **697.856 B**, `VLT` original byte a byte, motor BMW stock nove amostras ×1,05, sem nova coleção/nível/RefSpec/PtrN | **Usuário confirmou carregar `MARCEK` com os dados aplicados; log registra leitura de 697.856 B no offset 0.** |

**Interpretação:** a V48 não rejeita automaticamente qualquer mudança de valores no recurso `GLOBAL/ATTRIBUTES.BIN` (ao menos neste teste de carregamento). O conjunto mais amplo de alterações estruturais da PRE573 continua principal suspeito, mas não se isolou a causa específica (contador `pvehicle`, RefSpec, Export, PtrN, nova coleção/nome, tamanho do recurso, ou combinação). `BMW_tuning_buyable=false`, `physical_torque_gain_measured=false`, `save_persistence_after_new_gameplay_save_unverified=true`. Não declarar que +5% de motor foi comprovado, somente **vetor sintético no arquivo**.

## Próximos passos

1. Não reaplicar a PRE573 combinada. Usar o carregamento positivo PRE581 como **controle** e manter o arquivo `nfsmw.log` dessa sessão disponível.
2. Depois da coleta, fechar V48 e, se for iniciar novo ensaio, restaurar PRE581 usando `automation/device/pre581_restore_bmw_torque_only_shevery.sh` para voltar aos hashes originais, conferindo `PRE581_RESTORE=ORIGINAIS_VERIFICADOS`. **Não executar o rollback remotamente sem participação do usuário.** Os backups originais tinham sufixo `.pre581_original_backup`, conforme saída da aplicação.
3. Próxima hipótese a isolar: exportação/registro de **nova coleção VLT não ligada ao `pvehicle`** versus alteração do contador e do `RefSpec`; produzir primeiro diagnóstico estático e fragmentos próprios sob novos nomes e hashes, nunca reaproveitar fragmentos PRE573.
4. Após compatibilidade estrutural, retomar catálogo `FECarPartInfo`, itens compráveis, instalação e teste físico de mudança em carros BMW da carreira. Ainda não produzir V49.

**Preservações:** APK V48 PRE452 package `io.github.nfsmwrecomp`, certificado permanente SHA256 `1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b`, Nitro PRE398, controle PG-9076/touch, resolução 1920×1080, meta cap 120 FPS (cap efetivo log 60), qualidade/shaders/física geral e proteção térmica. Salvar relatório sem expor credenciais nem o conteúdo de save. O usuário aceita recriar uma carreira, mas não ordenou exclusão de `MARCEK`.
