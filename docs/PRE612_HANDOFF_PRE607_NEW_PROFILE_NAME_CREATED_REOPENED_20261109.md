# PRE612 — NOVO PERFIL CRIADO E REABERTO COM PRE607 ATIVA: COMPATIBILIDADE COM SAVE NOVO (2026-11-09)

**Fonte real:** o usuário afirmou **"Criei um novo perfil e funcionou"** após a comparação PRE607, e anexou `nfsmw.log` nesta mesma mensagem. O arquivo foi aberto e examinado localmente, **639.975 bytes, 3.664 linhas, SHA256 `02473a0141b29b04277ecb2febd5a390937e16f421c29d7e51096e06ba7f90ee`**. O log integral **não** foi publicado no GitHub/Drive; só este checkpoint sanitizado.

## Contexto do teste e resultado de fato

- O usuário **não informou que restaurou PRE607** entre a captura anterior de `MARCEK está corrompido` e o novo perfil. Portanto, classificar o teste como **com PRE607 presumivelmente ainda ativa pela sequência**, não como leitura remota dos hashes de `NFS/ZDIR.BIN` e `NFS/ZZDATA4.BIN` no telefone. A PRE607 é a variante PRE606, VPAK de 698.004 bytes, segundo motor BMW novo com parent `cd88083f` (BMW stock), `RefSpec` ativo de dois motores e `pvehicle.engine_upgrades=1`.
- O log acumulado contém **cinco sessões**, com inicializações às `04:27:55`, `07:53:21`, `07:58:37`, `08:06:02` e `08:06:51`. Sessões anteriores 04:27 e 07:53 estavam presentes em uploads antigos; **não atribuir seus eventos à criação do perfil novo**.
- **Quarta sessão, 08:06:39.572 (linha 2828):** `[guardado] crear «NAME» (raiz rmcsave)` no armazenamento privado Android do mesmo pacote. **08:06:39.574 (linha 2831):** `XamContentCreate ... contenido «NAME» tipo 00000001 modo 2 -> crear (resultado 00000000)`. **08:06:39.656 (linha 2835):** fechamento do conteúdo recém-criado com **1 arquivo de 62.688 bytes**. **08:06:39.664 (linha 2836):** cópia interna ao caminho de trabalho `saves/NAME/actual`. O nome efetivamente registrado é `NAME`; o nome `TESTE607` sugerido anteriormente **não aparece** no arquivo.
- **Quinta sessão, começa 08:06:51.430:** o log lista **dois perfis** — `MARCEK` e `NAME` — às 08:07:03.749 e às 08:07:04.305. Abre `NAME` com **62.688 bytes** e `XamContentCreate ... resultado 00000000` às **08:07:04.318**, **08:07:06.072** e **08:07:09.202**, cada qual com fechamento e cópia interna. Isso fornece **evidência de criação persistente de contêiner e sua reabertura após nova sessão**. A afirmação de que o perfil funcionou dentro do jogo provém do usuário; o código de sucesso de abertura isoladamente não valida todo o conteúdo semântico da carreira.
- A última sessão, de `08:06:51.430` a `08:07:23.245`, montou o game root `/storage/emulated/0/NFSMW_PTBR` em modo somente leitura, **32 entradas**. O log **não demonstra hash dos fragmentos PRE606 ativos** nem leitura explicita do VPAK modificado. Também não tem marcador `NFSMW_PRE292_BMW_MENU` nessa sessão; **BMW M3 GTR ainda não teve menu de tunagem nem compra/install testados com o perfil novo**.
- Existe uma ocorrência de watchdog: às **08:07:12.450**, o app registrou pausa por ir ao segundo plano; às **08:07:18.239**, o watchdog reportou 5 s sem progresso; às **08:07:23.245**, registrou retorno do progresso depois de aproximadamente 9 s de parada. As **18 linhas `[error]` da quinta sessão** correspondem ao watchdog e detalhes de threads, não a uma prova de erro do save ou de falha fatal do jogo. NÃO dizer que a sessão ficou sem erros. Sem `[critical]`/`[fatal]` textuais confirmados. A pausa foi registrada **antes** do watchdog; causalidade completa não comprovada.
- Cap de FPS **60** observado em log, resolução interna **1920x1080**. Nenhuma mudança de gráficos, físicas, limite térmico ou ganho de FPS foi efetuada/provada.

## Comparação: os dois perfis sob dados experimentais

| Caso | Resultado |
| --- | --- |
| PT-BR originais (V48) e perfil antigo MARCEK | Carregamento confirmado pelo usuário depois de rollback anterior (PRE579). |
| PRE573 combinado, motor BMW +1, parent default e MARCEK antigo | Mensagem `MARCEK está corrompido` em screenshot (PRE575/PRE577). |
| PRE592 com RefSpec ativo mas motor +0, MARCEK antigo | Carregou, confirmado pelo usuário com log (PRE595). |
| PRE607 com nova coleção parent corrigido (BMW stock), motor +1, MARCEK antigo | Mensagem `MARCEK está corrompido` em screenshot, log de 07:53 (PRE610). |
| **PRE607 presumivelmente ainda aplicada, perfil NOVO NAME** | **Usuário confirmou funcionamento; log comprova criação e reabertura na sessão seguinte.** |

**Conclusão revisada:** os resultados são **fortemente compatíveis com incompatibilidade de um perfil criado antes das alterações de catálogos/atributos**. A PRE607 **não é inviável em todos os saves**, pois um perfil novo funcionou sob o mesmo estado de jogo comunicado. **Não está provado** que a PRE607 tenha sistema de melhorias BMW funcional nem que todos os saves novos sejam estáveis, ou que o perfil novo tenha salvado progresso após uma corrida. A falta de readback dos ativos no aparelho também impede classificar o resultado como validação de bytes em guest para o VPAK corrigido.

## Próximo protocolo — sem patches adicionais

1. **Não restaurar PRE607 automaticamente ainda**, se a meta for testar a nova carreira: usuário pode prosseguir no mesmo perfil `NAME`. **Não aplicar novos fragmentos em cima da PRE607**, não apagar `MARCEK`, não limpar dados da aplicação.
2. Com a V48 normal, entrar na carreira `NAME`, realizar uma pequena ação de progresso que gere salvamento, sair pelo menu e reiniciar app; conferir se `NAME` abre e se o progresso realmente persiste. Recolher o novo `nfsmw.log` para comparar. A criação e reabertura de contêiner já foram verificadas, mas progresso/dados de carreira ainda não.
3. Quando estiver disponível no novo perfil, entrar na garagem/oficina com BMW M3 GTR **se o carro existir e estiver acessível**. Verificar se aparece desempenho/motor, preço de peça, opção de compra, instalação, efeito físico e persistência separadamente. Nunca afirmar tunagem habilitada apenas por novo save funcionar.
4. Se outro erro `corrompido` surgir até com o perfil novo, ou falha de persistência, coletar captura e log e restaurar os binários com `pre607_restore_bmw_child_parent_corrected_shevery.sh` somente depois de fechar o jogo, exigindo `PRE607_RESTORE=ORIGINAIS_VERIFICADOS` e salvando backups.
5. Para diagnóstico de compatibilidade de saves antigos, comparar atributos de perfil entre versões com cuidado e sem expor saves pessoais. O usuário já aceitou começar novo save, sem autorização para apagamento automático do antigo.

## Preservação

APK V48 PRE452 package `io.github.nfsmwrecomp`, certificado permanente SHA256 `1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b`; Nitro PRE398, controle iPega PG9076/touch, 1920×1080, FPS meta 120, shaders/efeitos/física completos, proteções térmicas. Nenhuma APK nova foi construída nem chave alterada. **Estado dispositivo comunicado:** PRE607 aplicada, perfil `NAME` criado e funcionando; `MARCEK` antigo incompatível nesse teste; nenhum rollback PRE607 relatado.
