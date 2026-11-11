# PRE688 real no S24 FE — SurfaceFlinger x Swaps internos (2026-11-11)

## Estado comprovado

**PRE688_REAL_CAPTURE=PASS; PRE688_ACTIONS_AUDIT=PASS; CAUSA_DA_CADÊNCIA=DESCONHECIDA.**

O usuário executou no Samsung Galaxy S24 FE o coletor ADB sem fio, sem chamadas do script ao Shevery. A saída informa uma única SurfaceView NFSMW e um histograma present2present com rótulo preservado. Captura **00:34:18–00:35:48** (-0300), 90 segundos.

**GitHub Actions:** [run 42955099751](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42955099751), job **130308198549**, `completed/success`; o workflow `.github/workflows/nfsmw-pre688-real-surfaceflinger-audit.yml` leu os três arquivos privados do Drive, conferiu SHA-256 e tamanho, reconstituiu as contagens e gravou relatório privado com readback. Commit de solicitação `49dc1ae5734d9de76684b6d2f2b75e2bb809c707`.

## Evidências quantitativas

A camada `SurfaceView[io.github.nfsmwrecomp/...GameActivity]` registra `displayRefreshRate = 120 fps`, `totalFrames = 5412`, `averageFPS = 62.226`, `droppedFrames = 0`, `lateAcquireFrames = 0`, `badDesiredPresentFrames = 0`.

Histograma `present2present`, verificável pela soma dos buckets:

| Intervalo | Ocorrências | % |
|---|---:|---:|
| 8 ms | 597 | 11,031 |
| 16 ms | 4.184 | 77,310 |
| 24 e 25 ms | 569 | 10,514 |
| Outros intervalos | 62 | 1,146 |
| **Total** | **5.412** | **100** |

Somando 8 e 24–25 ms = 1.166 intervalos, **21,545%**. A média dos buckets arredondados reproduz 62,226 FPS; isso não é calculado como quadros / 90 segundos. O histograma agregado não informa a ordem temporal dos quadros nem atesta alternância 8–24. Os contadores `droppedFrames=0` não comprovam uniformidade.

O `nfsmw.log` anexado tem **duas sessões**. A PRE688 começa às **00:32:33.214** (a anterior PRE687, interrompida, começa em 10/11 às 23:50). Após a primeira cinemática, retorna à jogabilidade com carro parado às **00:33:43.419**. APK V51, Vulkan MAILBOX com quatro imagens, 1920×1080 internos, cap 60 FPS. Nas quatro janelas do motor encerradas durante a captura (~00:34:33–00:35:33), C2 registra 4.800 intervalos, sendo 4.685 em 15–18 ms, 92 em 18–25 ms, 23 menores que 15 ms, **zero acima de 25 ms**; cada intervalo completo de relatório acumulado equivale a ~60 FPS. GPU 8,86–8,95 ms/Swap nas quatro janelas. Nenhum `surface has become outdated` encontrado na sessão PRE688.

**Outro achado:** proteção C3 conhecida desativa a thread de enlaces às 00:32:55 com `copia_duplicada=true`. Não houve correção; não relacionar causalmente ao pacing. Após terminar a captura (**00:35:48**), o vigia registra, às **00:36:36.144**, **5 s sem progresso dos 17 hilos do jogo**. Não há alerta de 20 s nessa sessão; o log termina em seguida. O aviso ocorre ~48 s depois da coleta, portanto **é indispensável esclarecer se o usuário abriu Termux ou deixou o jogo em primeiro plano ao redor de 00:36:31**. Sem essa informação, não classificar como deadlock autônomo, problema causado por Shevery ou crash.

## Privacidade, artefatos e contexto

- Arquivo original `nfsmw.log` no Drive privado: ID `15xO-DGiB-rOUL-TqD3BtCr0arC9ff5YH`, 1.635.318 bytes, SHA256 `ec8cc88753c6dad79d28bc3550316007119f8f4639ecbcb985dcd2470c90229d`.
- Captura `PRE688_CAPTURE.status.txt`: ID `1RmAoFCEeO057KmraclfDeryoCDusEkhr`, 320 bytes, SHA256 `30cc15952b72b265c014505cb21cfbe9c7ba8df7ddd92cbdb206fd63afeb69e6`.
- Histograma `PRE688_PRESENT2PRESENT.txt`: ID `1gHbmHPjp_2Wji9sVWrv49-apZYulxhkv`, 1.348 bytes, SHA256 `a8a004c19613fd381cb612e68dc8623ae186bac14c9e934c44d8db6fdc41da63`.
- Relatório ZIP local privado: ID `1S4cN3qmNCXfQQETFZI0Ts9OhpXkUCF-r`, SHA256 `da7e30e46b3f3dd0d3d4e5dd01cd80cb9830b70c0cffc80ccf81cedb69e51c89`, CRC PASS.
- ZIP de reexecução automatizada: ID `1kCSUi8MVX4ZbjPaB11wE2dZRMIDCWw4C`, SHA256 `b45bd45fa29cf45fe82365100a7bad08c55368b05c30d913cbd7a847eb1470eb`, CRC PASS.
- Contexto canônico atualizado **in place** no Drive, ID `1dRoE3qjSWZ4AwOaBQo97IINyecIFh6eB`, SHA256 após readback `c447b398212fbc55df42f22a6027009e1486345eaa38ad22944d0dd88591985c` (1.151.015 bytes). Backup prévio byte-identical ID `1WcCgjEnC9mS3BDyMagzCcZnTKQO3VfEk`, SHA256 `754fbc7bb8868f01b264feb03ab700b7cace921ec8f299d0c121696dffbf46c8`.

Nenhuma APK nova ou alteração de chave, package `io.github.nfsmwrecomp`, versionCode 51, controles, gráficos, Vulkan, saves ou proteções térmicas; não há ganho de FPS comprovado.

**Próximo gate PRE689:** separar irregularidade da apresentação (idealmente FrameTimeline ordenado/Perfetto em sessão controlada) do alerta watchdog ocorrido após captura, mantendo S24 FE em primeiro plano e verificando ação do usuário. Evitar otimização prematura ou alteração de modo de apresentação.
