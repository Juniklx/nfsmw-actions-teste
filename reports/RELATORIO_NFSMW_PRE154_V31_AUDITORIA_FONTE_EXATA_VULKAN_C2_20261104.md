# NFSMW PRE154 — Auditoria de procedência do código V31, Vulkan Presenter e métricas C2

**Sessões de referência:** Galaxy S24 FE, V31 `versionCode=31`, coleta PRE152 de 04/11/2026 às 21:12–21:17 (UTC−03:00), análise PRE153. **Modo:** exclusivamente leitura de fonte e logs; nenhuma alteração na APK, código ativo, configurações, certificados ou proteções térmicas.

## 1. Procedência comprovada e limites

1. **Compilação V31 PRE138:** GitHub Actions run `41896331611` terminou com sucesso, commit de execução `e39d516f95c68982bb2d214dd084eedab576112d`; o script de build nesse commit tem Git blob SHA `bc4d6673988fc3805a3d4c64546b9d250637b8f2`. Relatório de build verificado indica `versionCode=31`, SHA-256 APK `bf9a01f1c82c06f585385a0e2a547ffed77ce267b56eade1a7b20aa68cc46611`, assinatura permanente `1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b` e fonte PRE99 restaurada por hash. Os patches PRE117, PRE128, PRE131 e PRE133 foram aplicados no runner sobre os arquivos de interface/configuração indicados no script; **não há patch explícito do apresentador Vulkan ou do C2** nessa sequência.
2. **Verificação independente PRE154/PRE154B:** GitHub Actions `41942687947` e `41942998961`, ambos concluídos com sucesso. A execução PRE154B baixou apenas para um runner temporário o snapshot PRE99 de 874.780.689 bytes e validou SHA-256 `af8e82e198d00656814477fd64b8cc791fada21d937c1aa1cc583e5d37768b39`. Foram lidos somente 11 arquivos-alvo com hashes individualizados; nenhum projeto completo foi restaurado, nenhuma assinatura acessada e nenhuma compilação efetuada.
3. **Grau de certeza:** a combinação do script PRE138 arquivado e do PRE99 autenticado fundamenta a correspondência desses arquivos com o código-fonte usado na V31. **Não foi realizado um build reprodutível byte-a-byte da biblioteca instalada**; não confundir procedência documentada com equivalência de binário demonstrada.
4. **ZIP histórico não é substituto exato:** `NFSMW-Recompiled-Mobile-main.zip` SHA-256 `0ab7c949e62d377f444fb7b2489bc66d6387bd49b1798f184c4a953314064231` difere do PRE99 em `vulkan_presenter.cpp`, `windowed_app_context_sdl.cpp` e `nfsmw_nativo_sistema.cpp`. Por exemplo, o hash PRE99 do apresentador é `68998a1db81e9743197e446a5f8dacbf8d3dbcc2a51e4a7e6dac476b87d88c48`, enquanto o do ZIP é `eada548b2f683707a14ab8e6dd2c49b0381ac6542e901413fc94e5801fba74d5`. Uma diferença visível é a condição do perfilador por padrão no Android, mas **não foi demonstrado que essa seja a única diferença**.

### Hashes SHA-256 do PRE99 autenticado

| Arquivo no snapshot | SHA-256 |
|---|---|
| `nativo/sdk/src/ui/vulkan/vulkan_presenter.cpp` | `68998a1db81e9743197e446a5f8dacbf8d3dbcc2a51e4a7e6dac476b87d88c48` |
| `nativo/sdk/src/ui/presenter.cpp` | `e4db870dbeae984f9ef28957dafff6c4758471780fe1ac108b5501ebd341c208` |
| `nativo/sdk/src/graphics/vulkan/command_processor.cpp` | `b723f9480c3f4909dcc469d74ad42b154e1c700597cae4050504770700bf0058` |
| `nativo/sdk/src/ui/vulkan/vulkan_device.cpp` | `24b04ab68d6300977756a1cb55a805b9654963696e7102af8ce1be4e9f072a38` |
| `nativo/sdk/src/ui/vulkan/vulkan_submission_tracker.cpp` | `ae776d6e76d324c035b1c1c6e9083d4fdf94b7bb53a329f82f58650399b9a478` |
| `nativo/app/src/nfsmw_nativo_sistema.cpp` | `b8bc3f3cfbd9e53755387cdb3aca61961093873bb995dea8648a753920d09be2` |
| `nativo/app/src/nfsmw_nativo_destinos.cpp` | `b70497df49440b469018e7ef7a0e007d39ab5df13aa979edc91f37e1d2d42385` |
| `nativo/app/src/nfsmw_nativo_destinos.h` | `daceccb4a5d88fb0584f847ce64c439d579cb9770fa45e7aa1a363746745032f` |

Outros três arquivos (headers `rex/ui/presenter.h`, `rex/ui/vulkan/presenter.h` e `windowed_app_context_sdl.cpp`) possuem seus hashes no JSON PRE154B; os hashes de `vulkan_presenter.cpp` e `command_processor.cpp` foram comparados também com o resultado PRE136 e coincidiram.

## 2. Caminho identificado do Swap ao SurfaceFlinger

- `nativo/sdk/src/graphics/vulkan/command_processor.cpp`, linha 2442 do PRE99: chama `presenter->RefreshGuestOutput(...)` ao preparar a saída nativa. O número C2 de `presentados` se origina de `destinos_->Estadisticas(...)` em `nativo/app/src/nfsmw_nativo_sistema.cpp` (aprox. linhas 4089–4098), **não da camada SurfaceView do Android**.
- `nativo/sdk/src/ui/presenter.cpp`, linhas 675–772: `RefreshGuestOutput` prepara a saída do jogo, atualiza um *mailbox* **interno de três imagens** (pode substituir a imagem ainda não consumida) e solicita apresentação no host. Esse mailbox interno não deve ser confundido com o modo **Vulkan MAILBOX** do swapchain Android confirmado nos logs.
- `nativo/sdk/src/ui/vulkan/vulkan_presenter.cpp`, linha 2021: `PaintAndPresentImpl` espera uma submissão antiga conforme o número de slots; depois adquire a imagem, grava comandos, sincroniza por semáforos, submete com `vkQueueSubmit` e chama `vkQueuePresentKHR` (aprox. linha 2807). A chamada `vkQueuePresentKHR` é cronometrada no lado **CPU**, pelo trecho `kTrozoPresentar`. Um tempo elevado dentro dela **não prova trabalho equivalente de GPU** nem que retirar a espera seja correto.
- O estado configurável `present_hilo_propio` é **desligado por padrão no código PRE99**, mas **a configuração privada efetiva durante a sessão não foi auditada**. `present_refresco_sellado_perezoso` também vem desligado por padrão; quando desligado, há submissão de fence vazia após refresh. Habilitar tais opções mudaria sincronização/ordem de comandos, então não é uma otimização segura apenas por analogia com testes históricos no Nintendo Switch.

## 3. O significado de “GPU real por Swap”

- `nativo/app/src/nfsmw_nativo_destinos.cpp` (aprox. linhas 1022–1049 e 2765–2770) usa os recursos Vulkan de timestamp, `vkGetQueryPoolResults`, `timestampValidBits` e `timestampPeriod` quando disponíveis para acumular tempo de trabalhos e a marca final. Trata-se de uma métrica de execução de trabalhos, **não porcentagem de utilização da GPU nem tempo completo do quadro**.
- `nativo/app/src/nfsmw_nativo_sistema.cpp` (aprox. linhas 4089–4098): `GPU ms por Swap` = delta dos tempos acumulados dividido pelo delta de `presentados`. Por volta das linhas 4273–4287, o relatório “GPU real por Swap” multiplica esse valor por `escala_real_ns_ / escala_marcas_ns_`, razão acumulada entre relógio de parede e avanço das marcas GPU.
- A leitura direta do log PRE153, SHA-256 `30715ef0f76367452f6128651a696627e0afb7420a46fcd94b64d21895d55d71`, encontrou **13 relatórios C2 e 12 calibrações** na sessão de 21:12:50–21:17:12. **Todos os 12 fatores acumulados foram registrados como `1.000`**, e os trabalhos com marcas precisas coincidiram numericamente com o total de trabalhos medidos em cada relatório. O aumento medido de 6,61 ms/Swap às 21:13:31 para 9,47 ms/Swap às 21:17:11 **não resulta de uma mudança do fator de calibração exibido**. Ressalva: valores com três casas decimais têm arredondamento.

## 4. Pareamento com tempos de apresentação e térmica já medidos

| Janela C2 | FPS C2 estimados | GPU real / Swap | `RefreshGuestOutput: depois` |
|---|---:|---:|---:|
| 21:13:31 | 106,45 | 6,61 ms | 0,62 ms |
| 21:14:31 | 118,80 | 6,86 ms | 0,78 ms |
| 21:15:31 | 108,65 | 7,75 ms | 2,75 ms |
| 21:16:31 | 96,30 | 8,76 ms | 4,59 ms |
| 21:17:11 | 87,75 | 9,47 ms | 5,23 ms |

Os dados da PRE153 indicam queda simultânea da taxa de quadros apresentados pela camada `SurfaceView` nos intervalos finais e aumento de `vkQueuePresentKHR` até 5,47 ms na última janela de perfil. **Não somar** `RefreshGuestOutput: depois` com `vkQueuePresentKHR`: são regiões de execução parcialmente sobrepostas e de cadências de amostragem distintas. A situação térmica subiu de 0 a 2 e `SKIN` chegou a 44,5 °C na PRE152; os tetos de clock GPU caíram em leituras instantâneas, mas não se controlou o cenário do jogo.

## 5. Decisão técnica e próximo passo

**PRE154 concluída:** o código e o registro real concordam na origem das métricas. Há degradação de FPS na apresentação observada, custo GPU por Swap crescente e maior latência de chamada de apresentação; **não foi isolada uma falha específica do SurfaceFlinger ou bug de Vulkan**. Recomenda-se não aplicar patches de fila, modo imediato, thread de apresentação, número de imagens, desligamento de fence ou bypass térmico sem evidência controlada.

**PRE155 sugerida:** auditoria somente leitura da configuração efetiva do presentador no log e da sobreposição temporal dos tempos C2/SurfaceFlinger, seguida de desenho de um teste A/A na V31 sob a mesma cena e temperatura inicial. Não pedir nova execução física até fechar a análise offline. Não mudar resolução 1920×1080, limite 120 FPS, shaders, física, PG-9076, apps ou proteções térmicas. Próximo release eventual `versionCode>=32` preservando certificado SHA-256 `1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b`.

## 6. Artefatos e resultados reprodutíveis

- Execuções GitHub Actions PRE154 `41942687947` e PRE154B `41942998961`, sucesso; scripts de auditoria e requisições preservados no repositório privado `Juniklx/nfsmw-actions-teste`.
- `NFSMW_PRE154B_V31_FONTE_PRE99_PROVENIENCIA.json`: proveniência SHA-256 e trechos selecionados dos 11 arquivos, extraídos do PRE99 íntegro. O JSON documenta o trabalho, **não deve ser tomado como uma cópia completa dos arquivos C++**.
- `nfsmw_pre154_resumir_c2_v31.py`: analisador offline somente leitura; `NFSMW_PRE154_C2_ESCALA_FPS_REFRESH_V31_20261104.csv`: 13 janelas C2, sem misturar sessões. Arquivo `nfsmw.log` original arquivado na PRE153: https://drive.google.com/file/d/1CtEjIIeIr0Jtor_8ZgLEHAT2qbaZsvaO/view .
- A PRE154 **não gerou uma nova APK**, não validou aumento de FPS e não alterou a fonte ativa, assinatura ou dados privados do celular.
