# PRE331 — Critérios para comprovar owner do Nitro antes de qualquer patch (2026-11-07)

## Evidências existentes
- PRE323: `sub_82424AF0`, `r31=ctx.r3`; gravações em `r31 + 252`, sem identificação semântica do objeto.
- PRE329: no grupo V41 de 15:47, sites Nitro 1–4 compartilharam destino `0xBFA9E7FC`.
- PRE330: quatro grupos temporais separados observados no `nfsmw.log`, **192** amostras PRE247 Nitro (12/site/grupo) e o mesmo endereço nos quatro grupos. O agrupamento usa lacuna temporal de 90 s; **não comprova quatro processos distintos**.
- PRE325: cinco referências estruturais; nenhuma named direct call PAL. PRE327: só binário `sdk/thirdparty/sdl3/test/moose.dat` foi analisado, resultado inconclusivo.
- Nenhuma dessas evidências demonstra que o objeto é o carro do jogador.

## Hipótese a testar — NÃO é fato
A função `sub_82424AF0` recebe como primeiro argumento um objeto de componente de recurso/veículo e a instância observada em jogo pertence ao jogador. O mesmo valor de endereço não distingue objeto estático, layout repetido, pooling nem endereço virtual fixo por inicialização.

## Próximo experimento seguro, condicionado a encontrar referência independente
1. Em **snapshot PRE99 autenticado** e descartável, localizar referência de runtime identificável como **veículo controlado pelo jogador** (não escolher por endereço fixo, nome de função hipotético ou exemplo de PC). Exigir trecho de código PAL e fluxo de dados verificáveis.
2. Só então desenhar sonda passiva associando `ctx.r3` e essa referência, com cap, sem dereferenciar ponteiros guest arbitrários, e com marcador explícito do estado jogador/outro/indeterminado.
3. Mock de estados **jogador**, **NPC**, **desconhecido**, **ponteiro mudado**, **resolução falhou**, além de `OFF=original`. Qualquer ambiguidade deve permanecer **indeterminado**, nunca ativar modificação.
4. Instrumentação eventual em APK **diagnóstica incremental**, após revisão das fontes e confirmação do builder/certificado/versionCode. Sem novas gravações guest; jamais mexer no save `MARCEK`, controles, gráficos ou térmica. Verificar assinatura permanente e testar na S24 FE.
5. Só quando a comparação runtime e testes negativos forem suficientes, discutir e testar em etapa distinta um cheat Nitro **opt-in, OFF por padrão e reversível**, com modo OFF exatamente igual ao jogo.

## Condição de parada técnica
Sem uma **referência independente e autenticada** do veículo do jogador, repetir buscas pelo endereço `0xBFA9E7FC` ou forçar o valor do float não resolve owner nem garante segurança. Não criar V42 somente pela PRE330.

## Estado
Documento de planejamento probatório, **não uma implementação ou build**. Próximo gate é investigação de player pointer em fontes verificadas, e nenhum modo Nitro infinito está funcional na V41.
