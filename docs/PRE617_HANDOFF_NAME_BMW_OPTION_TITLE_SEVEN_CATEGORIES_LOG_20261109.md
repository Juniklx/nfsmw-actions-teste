# PRE617 — NOVO LOG BMW NAME / PRE607: SEIS CATEGORIAS DE DESEMPENHO ZERADAS, SÓ NITRO=3 (2026-11-09)

## Evidência real enviada pelo usuário

O usuário relatou **"Ainda continua a mesma coisa, todos exceto nitro aparece \"option title\""** após importar o ZIP PRE614 com a BMW normal no perfil novo `NAME`. O `nfsmw.log` anexado foi **lido localmente**; **não publicar o log inteiro ou os arquivos MC02 pessoais no GitHub ou Drive**. Hash SHA256 **`dc9fc0bb08ba943ede3e7675570c1c1fb15ddb5db743cee74edda4393109de0e`**, **3.937.714 bytes**, **15.827 linhas**, **8 sessões concatenadas**. A última sessão começa na **linha 6258, às 14:08:12.565**, termina na última linha às **15:06:40.003**. Não confundir ocorrências de sessões antigas (04:27, 07:53, 07:58, 08:06, 08:25, 08:30) com o teste mais recente.

## Resultado da BMW no último teste (15:06:07–15:06:36)

- Às **15:06:07.278**, log `NFSMW_PRE429_ENTRY manager=0x82C5D9E8 tuning_car=0xAD68FA50 pvehicle=0x00000000`; às **15:06:07.279**, `NFSMW_PRE292_BMW_MENU callsite=0x82578988 type=41 event=1` confirma caminho do menu **BMW M3 GTR**. O valor `pvehicle=0` nessa instrumentação de *entrada* não demonstra que todo lookup subsequente teve pvehicle ausente e **também apareceu em dados anteriores do Punto**; não declarar causa.
- Sete pares `NFSMW_PRE447_ROUTE` e `NFSMW_PRE429_LEVEL`, sempre com `caller=0x8256F83C` e `reason=2`. Categorias internas do código PAL conforme PRE441B/PRE442:
  - **4 Motor:** 0 às 15:06:11.397;
  - **3 Transmissão:** 0 às 15:06:16.732;
  - **2 Suspensão:** 0 às 15:06:21.012;
  - **6 Nitro:** **3** às 15:06:25.582;
  - **0 Pneus:** 0 às 15:06:29.965;
  - **1 Freios:** 0 às 15:06:33.315;
  - **5 Indução forçada/turbo:** 0 às 15:06:36.583.
- Os sete eventos `NFSMW_PRE283_BMW_VTABLE` sucedem as consultas de lista com `target=0x82582A40` e mesmo `screen_guest=0xAD4D9AA0`; não provar o conteúdo de cada item nem instalação.
- `PRE447 reason=2` **não significa erro nem ausência de descritor**: no PRE447 o marcador 2 é a rota que leu um valor de atributo resolvido, **que pode ser zero ou positivo**. Como Nitro retorna 3 pela mesma rota, a discriminação é pelo valor/catálogo do carro, e não por um ramo geral de erro no menu.
- O texto de tela `Option Title` **não aparece literalmente em qualquer linha do `nfsmw.log`**. O vínculo entre placeholder UI e catálogos zerados é inferência com forte suporte na simultaneidade, não prova do identificador/string específico. Não recomendar falsificar nomes/títulos sem conteúdo de peças.
- O **mesmo vetor de resultados 0/0/0/3/0/0/0** já constava nos logs V47/PRE444 para BMW (enquanto Fiat Punto possuía 4/4/3/3/3/4/3). Assim, **o novo save por si só e a variante PRE607 não demonstraram tornar o catálogo de desempenho comprável**. Abrir e dirigir a BMW da PRE614 é diferente de haver pacotes FE válidos.
- A sessão recente contém **379 linhas `[error]`** entre 14:08 e 15:06, principalmente por watchdog e diagnósticos de threads a partir de 14:13, além do erro de fallback gráfico C3 às **14:08:34.460**; zero `[critical]` ou `[fatal]` literais. **Não afirmar execução sem erros** nem causalidade com catálogo BMW; o menu continuou até 15:06. O limite configurado no começo da sessão é **60 FPS, resolução interna 1920×1080**.
- O log contém somente leituras de `NFS/ZZDATA4.BIN` com offsets de outros recursos, **sem hash do VPAK nem um marcador de leitura explícita de `GLOBAL/ATTRIBUTES.BIN` pelo caminho empacotado**. `D:\\GLOBAL\\ATTRIBUTES.BIN` como arquivo avulso falha com `0xc000000f`, comportamento também visto nos testes que carregaram. Portanto **não há readback do binário ativo PRE607 no telefone**. Isto precisa ser confirmado por hash (somente leitura) antes de descartar o experimento ou construir V49.
- Compare os hashes do par ativo de `/storage/emulated/0/NFSMW_PTBR/NFS` com a PRE606/PRE607 esperada:
  - `ZDIR.BIN`: **`f15d5da54148e0e762f65004d534092dbf3c08d12b0f8b710d6cf599235a32e2`**;
  - `ZZDATA4.BIN` completo 401.068.032 B: **`1ed79d0f031d400002da8db6153ee84188d717e33f093a501f7a6bdfc0e5e146`**.
  - Fontes PTBR originais: ZDIR `832a20dfdca663233f4559236048f21d5ff4e6f65780d1aa18e58b72005245bf`, ZZDATA4 `7dd33d214ac45f4b67005685bc0c2b8555eca98a33d24216c934f077d5054951`. PRE592 (contador 0) ZDIR `f5ba2b4d007f7ace0aa63429dd9f973d2b9f4924db1ab9695e5569038b0715da`, ZZDATA4 `522e15940379c8b746ab3c77e771fd22352b0b408cbf6264cf64e99f8a378c29`.

## Interpretação e próxima ação

- **Fato operacional:** BMW agora pode acessar sete menus de desempenho após importação do carro; **seis retornos zero, Nitro 3**, replicando padrão anterior. **BMW tunagem funcional não está implementada**. Nem a correção de parent PRE606 nem a criação de `NAME` demonstraram disponibilidade de peças ou compra.
- **Limite da prova:** o script PRE607 foi informado como aplicado em turnos anteriores, mas não houve nesta sessão leitura de hashes do par ativo. Não concluir ainda que o motor abriu o VPAK corrigido ou leu a nova coleção. O game pode usar outro caminho ou atributos default; exige trace próprio.
- **Próximo gate primário:** obter hashes **somente leitura** no Shevery para confirmar o estado ativo dos recursos; não restaurar ou aplicar fragmentos durante o jogo e não editar o save de novo. **Se** ambos corresponderem à PRE607 e persistirem 6 zeros, instrumentar a função de consulta `sub_823E5988`/helper `sub_8256F818` com log passivo de retorno já calculado, descritor/contexto e categoria, distinguindo `lookup retornou zero` de `pacotes válidos`, antes de projetar valores de catálogo. Sem `GetMaxLevel` verificado, não prometer compra.
- **Não** trocar todos `candidate_count=0` por 4, forçar preço, instalar entrada `Option Title` ou reusar opção Nitro para outras categorias. O estudo PRE526 demonstrou risco de cobrança sem instalação se `SetPackage` falhar no fluxo PC; não foi comprovado idêntico no Xbox guest.
- V48 PRE452 `io.github.nfsmwrecomp` intacta, certificado release permanente SHA256 `1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b`; manter Nitro PRE398, touch/PG9076, 1920×1080, efeitos/shaders/física e proteções térmicas. Não compilar V49 ou atualizar assinatura sem gate de código.

**Status PRE617:** `NFSMW_LOG_SETE_CATEGORIAS_AUDITADO` (leitura local), `PRE607_BINARIO_ATIVO_PENDENTE_HASH`, `BMW_TUNING_PENDENTE`. Nenhum arquivo APK, jogo, save ou credencial alterado nesta etapa de análise.
