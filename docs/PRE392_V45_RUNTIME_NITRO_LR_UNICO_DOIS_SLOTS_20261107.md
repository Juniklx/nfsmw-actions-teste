# PRE392 — V45: LR de chamada Nitro em runtime, 2026-11-07

## Material analisado

- `nfsmw.log` recebido pelo usuário, lido diretamente em modo somente leitura.
- SHA-256 `60101bab4e30ba36b5ddc6f44bc19f6fd0dd495af0ac01cd4f08e48fd42140e7`; 1.746.331 bytes; 7.446 linhas.
- Log concatenado com **três sessões distintas**, iniciadas em 20:19:41.098 (V43), 22:04:03.721 (V44) e **23:17:38.348 (V45)**. Contagens abaixo são da terceira sessão apenas.
- Nesta terceira sessão há 20 linhas PRE383, 60 PRE348, 38 PRE336, 71 PRE364 e 60 PRE316, até a última linha às 23:18:47.338.

## Achado decisivo: o LR observado não distingue os dois objetos

| Slot efêmero | Primeiro registro `PRE383` | Checkpoints de LR | LR distinto |
|---|---|---:|---|
| 1 | 23:18:12.741 | 11 | `0x824252DC` |
| 2 | 23:18:40.040 | 9 | `0x824252DC` |

- **20 de 20 registros PRE383** mostram o mesmo `guest_lr=0x824252DC`.
- A PRE336 encontrou somente **2 destinos Nitro distintos**, `distinct=2`, `overflow=false`, ambos com sites 1/2 de consumo e 3/4 de recarga.
- O teste **não** demonstra se um objeto é o jogador e o outro IA, nem quantos veículos estavam presentes. LR idêntico entre slots nesta sessão implica que **LR isolado NÃO serve como filtro player-only** com estes dados.
- Ademais, o valor de LR pode representar o endereço corrente preservado pela função e não necessariamente a identidade de quem a chamou, a depender da semântica recompilada do `ctx.lr`. Não promover os rótulos `guest_lr` ou `caller` a prova semântica adicional.

## Correlação temporal do comando
- PRE364 `buttons=0x2000` às **23:18:12.705**, primeiro consumo PRE348 site1/slot1 às **23:18:12.721**: **16 ms**.
- PRE364 `buttons=0x2000` às **23:18:40.008**, primeiro consumo PRE348 site1/slot2 às **23:18:40.025**: **17 ms**.
- Isso reproduz a proximidade temporal de PRE372 na V44. Entretanto a origem/identidade dos slots, o modo de jogo nesta sessão e a contagem de adversários **não são comprovados pelo log**.
- A PRE383 usa checkpoints 1,2,4,...,1024 por slot e não registra todo evento. Isso impede afirmar LR constante em chamadas não amostradas; a conclusão aplica-se aos 20 checkpoints registrados.

## Qualidade e limites
- Marcador PRE383 em execução: instalação da V45 e callback ARM64 ativo **confirmados no dispositivo**, sem afirmar todos os recursos totalmente testados.
- Uma mensagem PRE194 C3 textual nesta terceira sessão, às 23:18:06.123; tratá-la separadamente do Nitro. Sem ocorrências textuais `FATAL EXCEPTION`/`SIGSEGV` no log, não garante estabilidade permanente.
- Resolução interna 1920×1080 e cap configurado 60 FPS na inicialização V45, sem comprovação de 120 FPS ou ganhos.
- Sem alteração de stores Nitro, save `MARCEK`, shaders, física, controle ou proteções térmicas durante a auditoria.
- **`owner_verified=false`, `cheat_enabled=false`**, Nitro infinito ainda não funcional.

## Próximo passo recomendado
A hipótese de discriminação **somente por LR foi rejeitada para estes dois slots**. Antes de criar V46, investigar metadados estruturais associados a `ctx.r3`/referência `+296` e referência de veículo do jogador em outra rotina de direção/câmera/input. Fazer uma auditoria estática passiva, com integridade SHA e prova negativa contra NPC; não selecionar player por primeiro slot, LR, endereço guest fixo ou acionamento temporário do botão sem identidade independente.

Documento do log resumido: `PRE392_V45_NITRO_LR_AUDITORIA.json`. A V45 fica como última APK diagnóstica funcional; preservar V44 e assinatura permanente SHA-256 `1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b`. Próximo APK deverá incrementar versionCode e manter pacote `io.github.nfsmwrecomp`.
