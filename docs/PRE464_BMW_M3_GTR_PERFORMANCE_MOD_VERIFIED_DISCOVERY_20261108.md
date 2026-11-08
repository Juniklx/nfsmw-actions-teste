# NFSMW — PRE464: início verificável da mod de tunagem BMW M3 GTR (8 nov. 2026)

## Objetivo confirmado pelo usuário
Desenvolver um modo de instalar e ajustar peças reais de desempenho na BMW M3 GTR da carreira, dentro da recompilação Xbox 360 PAL para Android, sem alterar a BMW original indiscriminadamente. Desenho fail-closed: modificador experimental OFF por padrão e alteração somente após catálogo e persistência validados.

## Evidências de runtime V48 (PRE455)
- BMW M3 GTR type=41: Motor0, Transmissão0, Suspensão0, Nitro3, Pneus0, Freios0, Indução0.
- Fiat Punto type=74: Motor4, Transmissão4, Suspensão3, Nitro3, Pneus3, Freios4, Indução3.
- PRE447_ROUTE reason=2 em 16 consultas; candidatos não equivalem a peças válidas. PRE456 #42502772448 comprovou três subcaminhos possíveis do atributo, nenhum medido individualmente em runtime.
- Não forçar zero->4 nem reutilizar IDs do Punto. Não comprar títulos inválidos.

## PRE458 — fontes C++ autenticadas
- GitHub Actions [#42504047334](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42504047334): AUDIT_OK.
- Confirmadas seis invariantes de controle de fluxo do código de menu e consulta. O backup PRE99 contém fontes da recompilação, **não contém catálogo bruto da BMW identificável por nome**.
- Relatório: `docs/PRE458_BMW_TUNING_CATALOG_INVENTORY_READONLY.json`.

## PRE459–461 — identificação real de recursos PAL
- Fonte do usuário: `NFSMW_PAL.zip` no Google Drive, 5.567.403.879 bytes, arquivo existente, não alterado.
- PRE459 [#42504474760](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42504474760) / PRE459B [#42504560586](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42504560586): 53 membros ZIP, incluindo `NFS/ZDIR.BIN` (33.360 bytes) e `NFS/ZZDATA0..9.BIN`; diretório ZIP sha256 `a74f69e40ec0cc84ff58fcbf9fcccdd7353996c75592779ec63f09cf7dfdc7d6`.
- PRE460 [#42504694525](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42504694525): `ZDIR.BIN` descompactado e validado por CRC32 `1572a136`, sha256 `7f37d29f958454ec73d5dbd30068a6acb23cf92d5056fa2d944ca5c87c6637ee`.
- PRE461 [#42505058024](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42505058024): **1390 registros ZDIR de 24 bytes; 1390 localizações estruturalmente válidas; 1386 hashes coincidem com candidatos de nomes públicos** (lista Ekey/NFS.BIN.Tool), não com conteúdo extraído.
- Candidatos PAL:
  - `GLOBAL\\ATTRIBUTES.BIN` em `ZZDATA4.BIN` offset lógico **355.932.160**, tamanho **697.856**.
  - `GLOBAL\\GLOBALB.LZC` em `ZZDATA4.BIN` offset lógico **393.830.400**, tamanho **5.018.060**.
  - `GLOBAL\\FE_ATTRIB.BIN` em `ZZDATA0.BIN` offset lógico **162.392.064**, tamanho **113.856**.
  - `CARS\\BMWM3GTR\\GEOMETRY.BIN` em `ZZDATA1.BIN` offset lógico **149.428.224**, tamanho **1.640.640**.
  - `CARS\\BMWM3GTRE46\\GEOMETRY.BIN` em `ZZDATA1.BIN` offset lógico **180.596.736**, tamanho **1.866.176**.
- **Atenção crucial**: PAL ZIP contém os ZZDATA comprimidos como membros Deflate; os offsets lógicos não autorizam leitura aleatória de 697.856 bytes diretamente do arquivo ZIP sem descompactar/streamar o membro correspondente. A PRE461 não leu conteúdos de ATTRIBUTES.BIN PAL.

## PRE462–463 — referência binária USA acessada com segurança
- Outra fonte do usuário: `NFSMW.iso` USA original em Drive, 7.834.892.288 bytes.
- PRE462 [#42505438361](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42505438361): valida XDVDFS com root SHA PRE216, encontra 1390 entradas ZDIR USA válidas; `GLOBAL\\ATTRIBUTES.BIN` em ZZDATA4 USA offset lógico **287.117.312**, tamanho **697.856**. Conteúdo inicia `VPAK`.
- PRE463 [#42505578668](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42505578668): inspecionou **697.856 bytes** da USA ATTRIBUTES.BIN exclusivamente em runner temporário (reporte metadados apenas), SHA256 `9f4b04a221232e614b927a870e25da7db100477a7e425114b87082f46e8b99ad`.
- Estrutura USA comprovada: `VPAK`, uma vault de nome `db`, string region offset 64/tamanho3, BIN offset **128**/tamanho **354.959**, VLT offset **355.136**/tamanho **342.720**. Limites internos consistentes. Prefixos observados: BIN `5374724500007860`, VLT `4465704e00000030`.
- Na USA foram encontrados os nomes `BMWM3GTR`, `BMWM3GTRE46`, `m3gtre46careerstart`, `UpgradeSpecs`, `eFEPartUpgradeLevels`, `JunkmanMod`; presença textual não demonstra conexão de um carro específico a upgrade comprável. **USA não equivale comprovadamente à PAL**, embora ATTRIBUTES.BIN tenha o mesmo tamanho; diferenças de edição e TU devem ser respeitadas.

## Conclusão de engenharia
**O projeto já localizou, identificou e conseguiu inspecionar um VPAK real com identificadores relevantes de BMW e upgrade**. A funcionalidade de tunagem ainda NÃO foi implementada. Não há prova de que uma tabela específica autorize as seis categorias na BMW nem de que o fluxo de compra/salvamento seja seguro.

## Gates seguintes (sem suposições)
1. Analisar a estrutura VLT `db` do ATTRIBUTES.BIN USA e localizar a relação precisa entre `m3gtre46`, `UpgradeSpecs`, `eFEPartUpgradeLevels` e classes de partes. Usar documentação pública apenas como hipótese e verificar offsets contra bytes reais.
2. Confirmar equivalência **na edição PAL do aparelho**, idealmente por leitura controlada do membro Deflate `ZZDATA4.BIN` do ZIP PAL e extração efêmera de `GLOBAL\\ATTRIBUTES.BIN` com SHA256/CRC do contêiner. Não baixar/aplicar saves ou arquivos sem necessidade.
3. Mapear IDs de peças e níveis genuínos específicos da M3 GTR; distinguir carro de carreira e prólogo; verificar preço, localização, efeito, UI e flags de restrição. Para registro ausente, projetar dados compatíveis explícitos em overlay isolado, em vez de fabricar `candidate_count`.
4. Validar fluxo de compra/instalação e persistência apenas em save descartável, com recurso desligável e recuperação segura. Compatibilidade com save original NÃO presumida.
5. Somente após gates passar, compilar experimentalmente módulo ARM64 e APK assinada com certificado original, sem modificar Nitro infinito PRE398, outros carros, controle PG-9076, shaders/física, resolução1920×1080 ou proteção térmica.

**Segurança:** nenhum stage PRE458–PRE463 construiu APK, alterou pacote assinado, editou save `MARCEK`, publicou game assets ou reempacotou a ISO; o trabalho ficou em scripts de leitura de fonte/binários e metadados no GitHub privado. Nunca publicar logs de usuário, saves ou bytes de jogos em repositório público.

## Fontes de formato
- Ekey/NFS.BIN.Tool: https://github.com/Ekey/NFS.BIN.Tool
- MWEncyclopedia capítulo VPAK: https://github.com/TsyVM/MWEncyclopedia/blob/main/C11-Attribute-Vaults/C11-Attribute-Vaults.md (guia baseado em PC; Xbox pode diferir)
