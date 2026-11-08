# NFSMW — PRE453: V48 PRE452 assinada, APK comparada e protocolo de teste (2026-11-08)

## Resultado de build e artefatos verificados

- **GitHub Actions**: https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42498853924, `completed/success` às 16:35:06 UTC. Log final: `PRE452_STATUS VERIFIED`, `PRE452_VERSION 48`, `PRE452_CERT_POLICY EXISTING_PERMANENT_CERT_ONLY`.
- **Relatório do artefato** `nfsmw-pre452-v48-zero-route-42498853924`, id 13625337410, contém `pre452-v48-report.json` (19.022 bytes) e `nfsmw-v48-bmw-route-verified.apk` (47.104.233 bytes), `status=PRE452_V48_SIGNED_ZERO_ROUTE_DIAGNOSTIC_VERIFIED`, `signed_apk_verified=true`, `permanent_certificate_verified=true`, `drive_upload_success=true`, `gradle_release_succeeded=true`. ZIP do artifact SHA-256 `ca5b729edef1652f22237b4e0eaa12dee35406b89f4e52dd137a508e3144db38`.
- **APK no Google Drive**: `NFSMW_V48_PRE452_BMW_ZERO_ROUTE_DIAGNOSTIC.apk` id `1xPJ0er2h5CJ6Syxx89hdkbIFrbjrfI0C`, URL https://drive.google.com/file/d/1xPJ0er2h5CJ6Syxx89hdkbIFrbjrfI0C/view . Pasta pai id `1ac3fI_ahnp3yp7kU4JvsgDdsKkpy5tBh`. Versão `48`, pacote `io.github.nfsmwrecomp`, tamanho **47.104.233 bytes**, SHA-256 **`c642f95b4a60b9ccf5d8fbd98802afffc0a2247ec5a0783b54cd8083ec55bd35`**.
- Baixada a APK do Google Drive e comparada byte a byte com a APK dentro do artefato do GitHub: **iguais**; SHA-256 acima em ambas, ZIP com **872 entradas** e `testzip() == None` (CRC íntegro). `lib/arm64-v8a/libmain.so` SHA-256 `f39870144295c98cb05b9e8649a378e968fccb5bf479b653d0654158e92316a3`.
- Certificado permanente verificado pelo relatório de assinatura v2 da APK: SHA-256 **`1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b`**, idêntico às versões V46/V47. `apk_validation.signed_certificate_sha256_match=true`, `signed_schemes_verified=true`, `apk_validation.version_code=48`.
- `pre452_bmw_zero_route_diagnostic.signed_apk_has_all_three_callbacks_once=true`, um símbolo ELF para `NFSMW_PRE429_TRACE_ENTRY`, um para `NFSMW_PRE429_TRACE_LEVEL` e um para `NFSMW_PRE447_ROUTE`. Quatro marcadores localizados em `libmain.so`: `NFSMW_PRE429_ENTRY`, `NFSMW_PRE429_LEVEL`, `NFSMW_PRE447_ROUTE`, `NFSMW_PRE398_GLOBAL_NITRO_FULL`.
- **Não** desconsiderar a natureza do artefato: compilação/assinatura/Drive/ZIP/callbacks aprovados, mas **instalação e funcionamento real da V48 no S24 FE ainda NÃO confirmados**. Nitro infinito dentro da V48 não foi retestado em corrida. Nenhuma correção de tunagem ou ganho FPS demonstrados.

## Objetivo diagnóstico e protocolo conservador

1. Antes de instalar, realizar **backup verificado do save MARCEK**, preservar cópia da V47 e demais versões; instalar a V48 como atualização `io.github.nfsmwrecomp` sem desinstalar nem apagar dados. O downgrade V48→V47 não é normalmente instalável sobre versão de código maior sem processo específico; nunca sacrificar save para reverter.
2. Fazer **duas sessões isoladas** com a V48 no S24 FE: BMW M3 GTR de carreira (type 41) e Fiat Punto (type 74), encerra-se completamente o app entre elas. Em cada sessão navegar as sete categorias de Desempenho normalmente, **sem comprar** opções `Option title`, `20/20`, `999.999.999`; preservar um `nfsmw.log` por carro.
3. Procurar `NFSMW_PRE429_ENTRY`, `NFSMW_PRE429_LEVEL` e o novo `NFSMW_PRE447_ROUTE`. Campo `reason=1` significa rota sem descritor; `reason=2` significa caminho de leitura de atributo; `reason=3` significa fallback de múltiplas causas. Comparar `category`, `reason`, `candidate_count` entre carros. Rota 2 pode retornar zero ou positivo; **não assumir que rota 3 significa carro inválido nem que rota 1 seja específica da BMW**. O logger captura somente a primeira chamada normal filtrada pelo endereço de retorno original.
4. Relatar instalação, inicialização do jogo, observações visuais e os **dois logs originais** (em privado), sem tocar no save, físicas, shaders, controles PG-9076 ou medidas térmicas.
5. Se não surgir `PRE447_ROUTE` nos logs, não declarar ausência de rotas nem consertar construindo upgrade fictício. Conferir primeiro que a APK instalada é versionCode 48 e que a sessão passou pela rotina alvo.

## Referências preservadas

- V46 PRE401 `versionCode 46`, SHA256 `ac3676127d922b3c981aac6fffb87690c64bb9c0139fb983bd3ad8e017459eb7`: baseline Nitro infinito global efetivamente testado PRE407.
- V47 PRE434 `versionCode 47`, SHA256 `ce2de9311b80670f7f4700e426ad1a77d6cd87a836df5ae3b36d4ec872cc7461`: diagnóstico de sete categorias.
- BMW V47 `candidate_count` = 0,0,0,3,0,0,0; Punto V47 = 4,4,3,3,3,4,3; contagens candidatas, não itens garantidos.
- PRE448 fonte-equivalente ARM64 nativo sem APK aprovado `42496806174`; PRE452 V48 assinada `42498853924`. Preservar resolução interna 1920×1080 e controles térmicos; não alterar gráficos, física, save MARCEK ou chave permanente.

## Atualização de contexto
Adicionar ao `CONTEXTO_NFSMW.md` canônico no Drive em modo append-only, após cópia integral e leitura de verificação. Registrar resultados PRE452 com id/URL do artefato e ressalvas de instalação pendente. Nunca compartilhar credenciais.
