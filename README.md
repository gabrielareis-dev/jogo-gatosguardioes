# Gatos Guardiões: Miaus contra Morce-ratos

## Sobre o jogo

Jogo de ação 2D feito em Python com Pygame. Controle o gato guardião e proteja a vizinhança dos morce-ratos. Mire com o mouse e atire bolas de lã vermelhas enquanto se movimenta para escapar dos inimigos.

Os inimigos perseguem a posição atual do gato. As fases iniciais são mais tranquilas; os morce-ratos ficam mais rápidos e resistentes conforme você avança. O mesmo cenário de rua aparece em todas as fases, enquanto a aparência dos inimigos muda. Os níveis 4 e 5 usam a mesma imagem de inimigo.

## Controles

- **Mover o gato:** `W`, `A`, `S`, `D` ou as setas.
- **Mirar:** mouse.
- **Atirar:** clique esquerdo ou `Espaço`.
- **Pausar e voltar ao menu:** `Esc` durante a partida. Clique em **CONTINUAR JOGANDO** para retomar.
- **Começar ou reiniciar:** clique no botão da tela ou pressione `Enter` no menu ou na tela final.
- **Sair:** pressione `Esc` no menu ou na tela final, ou feche a janela.

## Fases e progressão

Derrote inimigos para ganhar pontos. A cada 500 pontos, você avança de fase. O dano de cada bola de lã aumenta junto com o nível do gato.

| Fase | Meta de pontos | Vida do morce-rato comum | Dano da bola |
| --- | ---: | ---: | ---: |
| 1 | 500 | 1 | 1 |
| 2 | 1.000 | 2 | 2 |
| 3 | 1.500 | 5 | 3 |
| 4 | 2.000 | 8 | 4 |
| 5 | 2.500 | 12 | 5 |

Os inimigos grandes têm 2 pontos de vida extras e valem 250 pontos; os comuns valem 100. Todos os inimigos têm uma barra de vida visível.

O gato começa com **3 pontos de vida**. Ao passar de fase, a vida máxima aumenta em 1 e ele recupera 1 ponto. As barras sobre o gato e os inimigos mostram a vida restante. Depois de receber dano, ele fica brevemente invulnerável.

Durante a partida, o HUD mostra o retrato e a vida do gato, a pontuação, a fase, o dano atual e o progresso até a próxima meta.

- **Vitória:** alcance 2.500 pontos.
- **Derrota:** a vida do gato chega a zero.

## Executar a versão para Windows

O jogo já está compilado para Windows e pode ser iniciado diretamente pelo executável. Não é necessário instalar Python, abrir o terminal ou executar o processo de build para jogar.

1. Baixe o pacote ZIP do jogo e escolha **Extrair tudo** no Windows. Não execute o jogo de dentro do ZIP.
2. Na pasta extraída, dê dois cliques em `GatosGuardioes.exe`.

O executável precisa ficar junto da pasta `assets`, que contém os personagens, o cenário, os efeitos sonoros e as músicas. Mantenha essa pasta no mesmo local e com o nome `assets`. Se o Windows exibir um aviso de segurança para um aplicativo baixado, confira se o arquivo veio do ZIP deste projeto antes de permitir a execução. O jogo continua funcionando sem áudio se não houver um dispositivo de som disponível.

## Executar pelo código-fonte

Requer Python 3.10 ou mais recente. No terminal, dentro da pasta do projeto, execute:

```powershell
python -m pip install -r requirements.txt
python main.py
```

## Opcional: recompilar ou gerar outro pacote para Windows

Esta etapa só é necessária para alterar o código ou criar uma nova compilação. Em um computador com Windows e Python instalado, execute `build_windows.bat`. O script instala as dependências, cria o executável e gera um ZIP com o `.exe` e os assets necessários. Para apenas jogar, use o executável que já vem no pacote distribuído.
