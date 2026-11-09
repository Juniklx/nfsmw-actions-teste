# PRE543_BMW_TUNING_PRE541_PRE542_GUEST_ATTRIBUTE_FLOAT_CHAIN_20261108

**Data:** 2026-11-08 local (as execuções CI podem constar como 2026-11-09 UTC). **Projeto:** NFSMW-Recompiled-Mobile, Need for Speed: Most Wanted (2005), PAL Xbox 360 para Android. **Objetivo persistente:** tunagem comprável, instalável e persistente da BMW M3 GTR carreira (type 41), sem alterar a baseline funcional.

**Baseline preservada:** APK V48 PRE452 assinada, package `io.github.nfsmwrecomp`, versionCode 48, APK SHA256 `c642f95b4a60b9ccf5d8fbd98802afffc0a2247ec5a0783b54cd8083ec55bd35`; `lib/arm64-v8a/libmain.so` PAL SHA256 `f39870144295c98cb05b9e8649a378e968fccb5bf479b653d0654158e92316a3`; Nitro infinito PRE398, controle físico iPega PG-9076 e touch, gráficos/shaders/efeitos/física, resolução interna 1920×1080, máximo 120 FPS, respeito ao thermal, save `MARCEK` não tocado. Chave/certificado de release permanente SHA-256 `1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b` não acessado.

## PRE541 — prova na fonte PPC guest original PAL, sem recompilar

- [GitHub Actions PRE541 run 42539950488](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42539950488), `AUDIT_OK`, `docs/PRE541_PAL_GUEST_823EAE40_FOUR_DEPS_PPC_READONLY.json`.
- Origem: TAR histórico PRE99 SHA256 `af8e82e198d00656814477fd64b8cc791fada21d937c1aa1cc583e5d37768b39`, 874.780.689 bytes, validado antes da leitura. Varredura dos 129 shards C++ PAL gerados; seis funções numéricas analisadas e source SHA256 fixados.
- `sub_823EAE40` está em `nfsmw_recomp.85.cpp`, SHA256 `e8c85788d811c0cb9390c35705ea4e60bb7dbd4210ce73d19d6d03358e5cfbf3`, corpo de 493 linhas geradas e 180 comentários de instruções PPC. Em seu corpo: `lfs` 32, `stfs` 24, `fmadds` 15, `fadds` 9, `fsubs` 9, `fdivs` 6, `fmuls` 6, entre outros. Possui 32 loads e 25 stores `REX_U32`.
- Quatro chamadas diretas guest confirmadas na ordem original: `sub_823EB290`, `sub_823EB3B0`, `sub_823E4130`, `sub_823E4588`. As duas primeiras chamam `sub_823EA300`; `sub_823E4588` chama `sub_82148818`.
- `sub_823E4130` (arquivo `nfsmw_recomp.3.cpp`, SHA256 `baa3b79ea54b3aab4f4afd9db4d501e32e29a970cdd84c6a945a91fe56842e03`) chama a rotina de contagem/leitura de atributos `sub_823E5988` e `sub_823E41C0`. Tem `fdivs` e instruções PPC de conversão aritmética `fcfid`. `sub_823E5988` é âncora já investigada PRE446–PRE528 (consulta atributo/níveis).
- Estes dados comprovam **código gerado PAL histórico** e **cadeia direta de chamadas**, mas não o papel semântico da matemática para a BMW.

## PRE542 — confirmação independentemente no ELF PAL assinado V48

- [GitHub Actions PRE542 run 42540238097](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42540238097) `AUDIT_OK`, `docs/PRE542_ORIGINAL_V48_PAL_FLOAT_ATTRIBUTE_COUNT_PATH_READONLY.json`.
- APK V48 e `libmain.so` PAL reautenticados por SHA256. `.rela.plt` original ARM64 usado para resolver destinos efetivos `BL` dos seis símbolos, com 15.598 realocações guest numéricas. Nenhuma execução Android ou modificação do ELF foi feita.
- Cadeia estática guest **diretamente confirmada na V48**:
  `sub_823EAE40 → sub_823E4130 → sub_823E5988 → {sub_8214B858,sub_8214EDA8}`.
  As listas de chamadas guest das **seis** funções examinadas coincidiram em multiplicidade com as da PRE541 (cada correspondência `source_and_original_V48_numeric_guest_call_multisets_match=true`).
- Na função `sub_823EAE40` do ELF V48: **2.964 bytes ARM64**, **741 instruções**. Foram contadas **226 instruções relacionadas a ponto flutuante**, decompostas em `fcvt` 112, `fmov` 56, `fmadd` 15, `fcmp` 13, `fadd` 9, `fsub` 9, `fdiv` 6, `fmul` 6. O número 226 inclui **conversões/movimentação e comparação**; não significa 226 operações físicas ou 226 upgrades. `sub_823E4130` tem 9 instruções float-relacionadas, incluindo um `fdiv` e 2 `scvtf`.
- **Conclusão comprovada:** existe na biblioteca PAL V48 publicada um caminho de cálculos de ponto flutuante que chama, por duas arestas de função, a rotina de consulta dos níveis/atributos usados na investigação da oficina. **Inferência ainda não comprovada:** isso participa da interpolação dos motores, aceita a coleção nova, altera torque, aplica `SetPackage` ou é executado na sessão do Galaxy S24 FE.

## Gate posterior prioritário

1. PRE544: investigar estruturalmente os acessos a dados de entrada/saída e chaves de atributos da função `sub_823EAE40` e das dependências para distinguir *cálculo genérico*, *interpolação de atributos de performance* ou *física do carro*. Confirmar operações sobre parâmetros identificáveis do motor sem adivinhar nomes PC a partir dos endereços guest.
2. Em paralelo, planejar **teste de carregamento não transacional e reversível** do VPAK experimental PRE502/PRE518 em **cópia isolada**, antes da compra: a coleção `engine/bmwm3gtr_upgrade_engine_pre499` de torque +5% e contador `engine_upgrades=1` foi gerada apenas em memória, checksum e tamanho/padding PAL validados, porém **guest loader ainda não demonstrado**. Não assumir comportamento da V48 com nova coleção ou engine package ativo.
3. Continuam requisitos antes de uma V49: comprovar seleção/instalação pela implementação real guest `Physics::Upgrades::SetPackage`, fluxo de preço e cashback/rollback, efeito real em jogabilidade e persistência em **save descartável**. Não cobrar/instalar no perfil `MARCEK`.
4. Não modificar ISO/ZIP/ZDIR/ZZDATA originais, V48 estável, saves reais, Nitro PRE398, controle PG-9076, gráfico/física, assinatura permanente ou proteções térmicas. Não publicar assets ou código recompilado do jogo.

**Status:** PRE541/PRE542 `AUDIT_OK`; cadeia PPC/V48 para contagem + aritmética confirmada, **SetPackage guest ainda desconhecido**, nenhuma tunagem BMW habilitada, nenhuma V49 compilada, nenhuma compra/persistência/física/FPS validada.
