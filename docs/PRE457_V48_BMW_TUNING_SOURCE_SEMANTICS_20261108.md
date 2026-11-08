# NFSMW — PRE457: interpretação consolidada V48/PRE456 e tunagem BMW (08/11/2026)

## Estado e escopo
- **PRE455**: análise local privada de `BMW.log` e `punto.log`; não publicar arquivos brutos.
  - BMW.log: SHA-256 `2998b018b92e5934a3ce2624da17b2a69ca6e2733ca2823043378d9c2de9f8b8`.
  - punto.log: SHA-256 `ad122e88dcbf49e594a49d23d16328c937161a5fb6c82488fb37673ae1b5ad5c`.
  - BMW M3 GTR (type=41): contagens candidatas por Motor, Transmissão, Suspensão, Nitro, Pneus, Freios, Indução = 0,0,0,3,0,0,0. Punto (type=74): 4,4,3,3,3,4,3. 8 eventos por sessão (BMW repetiu Nitro; Punto repetiu Pneus). Os 16 eventos PRE447_ROUTE foram reason=2. Não são peças instaláveis comprovadas.
- **PRE456**: GitHub Actions [run 42502772448](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42502772448), job audit success, `PRE456_STATUS AUDIT_OK`. Backup PRE99 (874.780.689 bytes) validado por hash SHA-256 `af8e82e198d00656814477fd64b8cc791fada21d937c1aa1cc583e5d37768b39`. Quatro fontes PAL verificadas por SHA fixo. Evidências restritas no arquivo `docs/PRE456_V48_ROUTE2_ATTRIBUTE_PROVENANCE_READONLY.json`. Apenas leitura, sem APK, sem escrita de save ou chave.
- **PRE452 V48** ainda é diagnóstica. Apesar de marcadores executarem nos logs, `versionCode` não é registrado por eles. Nitro infinito V48 não foi revalidado em corrida; V46 PRE401 continua referência real.

## Novo conhecimento estático: três subrotas dentro de reason=2
Em `sub_823E5988` (PAL gerado `nfsmw_recomp.28.cpp`, SHA-256 `11eec8fe3d20dc5d53e262525a4cf31021c2bbfb28e2690b6372c6c3cbea4aad`), no caminho de um descritor encontrado:
1. O campo `[descriptor+12]` é usado no resolvedor `sub_8214B858`. A rota 2 só é atingida após este resolvedor sinalizar sucesso (comparação de `r3 & 0xFF` diferente de 0). Sucesso aqui **não garante valor positivo**.
2. Após a resolução, se `[stack+92]` contém ponteiro não nulo, esse ponteiro chega diretamente à instrução final.
3. Se nulo, `sub_8214EDA8` tenta resolver a origem. Se retorna ponteiro não nulo, esse é usado na instrução final.
4. Se ambos os ponteiros são nulos, o PAL escolhe um endereço constante `0x82C5F590`. **O conteúdo 32-bit nesse endereço não foi medido pela PRE456**, de modo que não se deve afirmar que seja zero.
5. As três alternativas convergem em `ctx.r3.u64 = REX_LOAD_U32(ctx.r11.u32 + 0)` (linha relativa 104); em todos os casos o logger PRE447 marca `reason=2`, sem distinguir origem.
6. A função envolve decrementos de referência guest; jamais invocá-la artificialmente para teste. O construtor `sub_8256F818` usa o primeiro resultado e não entra no laço normal de opções quando `candidate_count<=0`.

## Confronto com o comportamento histórico do jogo
- Referências comunitárias independentes descrevem a BMW M3 GTR obtida após a campanha como não tunável no desempenho:
  - Need for Speed Wiki, *Need for Speed: Most Wanted / Performance Tuning*: https://nfs.fandom.com/wiki/Need_for_Speed%3A_Most_Wanted/Performance_Tuning
  - NFSUnlimited, FAQ do *Most Wanted*: https://www.nfsunlimited.net/mostwanted/faq
  - Neoseeker, *BMW M3 GTR*: https://needforspeed.neoseeker.com/wiki/BMW_M3_GTR
- **Inferência, não prova causal:** seis categorias zeradas podem ser uma restrição intencional original da BMW, e não regressão Android. Nitro=3 é contagem de consulta, não prova de pacote vendável.
- Não confundir o histórico de regras do jogo com verificação do valor específico do atributo no runtime PAL; a PRE456 não identifica qual das três subrotas produziu os zeros.

## Decisão técnica conservadora
- Considerar a V48/PRE455/PRE456 como diagnóstico concluído até o limite da evidência, sem declarar defeito do APK ou autorizar tunagem forçada.
- Se o objetivo é preservar o comportamento original, **não corrigir** uma possível restrição intencional da M3 GTR.
- Se o objetivo futuro é uma BMW tunável como mod, tratar como recurso separado, condicionado a suporte de peças e catálogo válidos, com backup `MARCEK`, teste isolado e fallback reversível. Não trocar zeros por `4`, não comprar `Option title`, `20/20` ou `999.999.999`, nem reutilizar perfil do Punto como verdade da BMW.
- Caso ainda seja necessário provar a subrota de runtime antes de qualquer mod, projetar uma prévia **somente leitura** de logger passivo de origem A/B/C, sem novas leituras/escritas guest, sem nova chamada da função, validar C++/ARM64 antes de eventual nova APK. Não criar V49 para alterar upgrades com os dados disponíveis.
- Preservar V46/V47/V48, assinatura permanente SHA-256 `1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b`, Nitro PRE398, shaders/efeitos/física, controles PG-9076, 1920×1080 e proteções térmicas.

**Nota:** este relatório não representa execução de uma nova APK ou mudança no save. Logs brutos continuam apenas no ambiente privado da conversa.
