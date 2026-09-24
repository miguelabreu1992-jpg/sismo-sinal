# Janela do gato no TouchDesigner

Este guia cria a versão física do gato: as pupilas fazem um movimento lento e orgânico, recebem eventos sísmicos por OSC e ficam paradas durante 1,8 segundos após um pico.

O TouchDesigner está instalado neste computador. A rede abaixo é a receita para montar e guardar o projeto nativo como `sismo_cat.toe`.

A orquestra envia os eventos OSC do SuperCollider para `57120` e duplica-os para o TouchDesigner em `57121`.

Mensagem recebida:

```text
address: /sismo
values: [frequency_hz, amplitude]
```

Para controlar o olhar por estação, a orquestra também envia:

```text
address: /sismoPoligono
values: [station_index, amplitude, local_activity]
```

O Python já aplica o threshold atual antes de colocar o evento na fila. Portanto, cada mensagem recebida no TouchDesigner representa um input acima do threshold.

## Imagem

O desenho atual é `gato.png`. A composição já está horizontal: cabeça à esquerda, corpo e cauda à direita. Não é necessário rodar a imagem.

## Rede de nós

Cria estes nós dentro de um `Base COMP` chamado `cat_visual`:

```text
filein_gato (File In TOP)
        |
transform_gato (Transform TOP)
        |
        +-----------------------------+
                                      Composite TOP -> Null TOP -> Out TOP
circle_olho_esquerdo -> transform_olho_esquerdo -+
circle_olho_direito  -> transform_olho_direito  -+
```

Configuração:

- `filein_gato`: carregar `gato.png`.
- `transform_gato`: `Rotate = 0`, `Fit = Fit`. Se a imagem aparecer invertida, usa `Rotate = 180`.
- `circle_olho_esquerdo` e `circle_olho_direito`: círculos pretos pequenos, usados como pupilas.
- Os dois `Transform TOP` dos olhos recebem movimento em `Translate X/Y`.
- `Composite TOP`: modo `Over`.
- `Out TOP`: saída final para o ecrã.

Como o desenho é uma imagem única, as pupilas são sobrepostas como duas pequenas formas pretas. Se a posição inicial não coincidir, abre `visualizer_gato.html`, usa `Calibrar olhos` e copia as posições normalizadas para os Transform TOP.

## Entrada OSC

Cria:

```text
OSC In CHOP -> Select CHOP -> Math CHOP -> Logic CHOP
```

No `OSC In CHOP`:

- `Network Port`: `57121`
- `Active`: ligado
- Endereço: `/sismo`

No `Select CHOP`, escolhe o canal que contém a amplitude. Normalmente será `chan2`; confirma no viewer do CHOP, porque o nome pode variar conforme a versão do TouchDesigner.

No `Math CHOP`:

- `From Range`: `0` a `1`
- `To Range`: `0` a `1`

No `Logic CHOP`:

- `Convert Input`: `Off When Zero, On When Positive`
- `Off to On` como evento
- Threshold: `0.08`

## Movimento físico dos olhos

Cria dois `LFO CHOP`, um para cada olho:

- Forma: `Sine`
- Frequency: `0.35` para X esquerdo, `0.47` para X direito
- Amplitude: pequena, entre `0.01` e `0.025`

Liga cada LFO a um `Math CHOP` e depois exporta para os parâmetros `Translate X` dos Transform TOP dos olhos.

Para o movimento vertical, usa um segundo `LFO CHOP` mais lento, entre `0.15` e `0.22` Hz. Combina X e Y com um `Merge CHOP` e limita ambos com `Math CHOP`, para que as pupilas não saiam da íris. Usa `Filter CHOP` com `Filter Width = 0.15` para retirar mudanças bruscas.

Para um comportamento mais natural, usa frequências ligeiramente diferentes em cada olho e amplitude vertical menor que a horizontal. O resultado é um olhar que vagueia lentamente, em vez de uma oscilação perfeitamente sincronizada.

## Parar os olhos quando há input

Cria um `CHOP Execute DAT` ligado ao `Logic CHOP` e usa este código no callback `onOffToOn`:

```python
def onOffToOn(channel, sampleIndex, val, prev):
    parent().fetch('frozen_until', 0)
    parent().store('frozen_until', absTime.seconds + 1.8)
    return
```

Depois, no movimento dos olhos, usa um `Switch CHOP` entre:

```text
movimento normal
movimento zero
```

Controla o índice do `Switch CHOP` com um `Script CHOP` ou expressão nos parâmetros:

```python
1 if absTime.seconds < parent().fetch('frozen_until', 0) else 0
```

Quando chega um evento acima do threshold, o índice passa temporariamente para o movimento zero. Após 1,8 segundos, os olhos retomam o movimento.

Para preservar a última posição antes do congelamento, coloca um `Hold CHOP` antes do `Switch CHOP`. O caminho normal alimenta o `Hold CHOP`; o `Logic CHOP` dispara o hold quando há um evento. Assim, os olhos não saltam para o centro ao congelar.

## Abrir o TouchDesigner neste computador

1. Abre o menu Iniciar e procura `TouchDesigner`.
2. Abre a aplicação instalada em `C:\Program Files\Derivative\TouchDesigner\bin\TouchDesigner.exe`.
3. Escolhe `Create New` ou abre um projeto `.toe` existente.
4. Mantém este ficheiro aberto no VS Code como referência enquanto montas a rede.

## Criar automaticamente a rede sem Python Console

O ficheiro `build_sismo_cat_toe.py` contém o construtor da rede. O TouchDesigner pode executá-lo através de um `Execute DAT`.

1. Abre o TouchDesigner e escolhe `File > New Project`.
2. Guarda imediatamente como `sismo_cat.toe` dentro da pasta do projeto.
3. No espaço vazio da rede, pressiona `Tab`, procura `Execute DAT` e cria-o.
4. Abre o `Execute DAT` com duplo clique e substitui o conteúdo por:

```python
def onStart():
        script_path = r'C:\Users\migue\Desktop\Sismo SInal\vscodeSismoSinal\build_sismo_cat_toe.py'
        with open(script_path, encoding='utf-8') as script_file:
                exec(script_file.read(), globals())
```

5. Seleciona o `Execute DAT`, abre o painel `Parameters` e, na página `Execute`, ativa `Start`.
6. Guarda o projeto, fecha-o e abre novamente. O `onStart()` cria a rede `cat_visual` e guarda `sismo_cat.toe` na pasta do projeto.
7. Se aparecer um erro, abre o `Textport` em `Dialogs > Textport` e copia a mensagem vermelha.

## Montagem passo a passo

1. Abre o TouchDesigner e cria um projeto vazio.
2. Cria um `Base COMP` chamado `cat_visual`.
3. Dentro dele, cria `File In TOP`, dois `Circle TOP`, três `Transform TOP`, um `Composite TOP`, um `Null TOP` e um `Out TOP`.
4. Carrega `gato.png` no `File In TOP`.
5. Usa os dois `Circle TOP` como pupilas e coloca-os por cima do `File In TOP` através do `Composite TOP` em modo `Over`.
6. Cria os `LFO CHOP`, `Merge CHOP`, `Filter CHOP`, `Hold CHOP` e `Switch CHOP` para o movimento descrito acima.
7. Cria `OSC In CHOP`, `Select CHOP`, `Math CHOP` e `Logic CHOP` para a entrada sísmica.
8. No `OSC In CHOP`, define a porta `57121`. No `Select CHOP`, escolhe o canal da amplitude, normalmente `chan2`.
9. No `Logic CHOP`, usa threshold `0.08` e configuração `Off When Zero, On When Positive`.
10. Liga `start_visualizer.bat` no Windows. Confirma que o viewer do `OSC In CHOP` mostra mensagens `/sismo`.
11. Ajusta a posição dos olhos no viewer e usa `File > Save As...` para guardar o projeto como `sismo_cat.toe` na pasta do projeto.

## Teste

1. Abre o projeto `sismo_cat.toe` no TouchDesigner.
2. Inicia o projeto com `start_visualizer.bat`.
3. No TouchDesigner, confirma que o `OSC In CHOP` está a receber dados em `57121`.
4. Move temporariamente o threshold para baixo no visualizer principal se quiseres mais eventos.
5. Observa as pupilas: devem oscilar normalmente e parar quando chegar um pico.

O SuperCollider continua a usar `57120`; o TouchDesigner usa `57121`, evitando conflito entre os dois receptores OSC.

## Movimento por polígono de 21 estações

O ficheiro `touchdesigner_cat_polygon_motion.py` contém os 21 vértices e a lógica de atividade.

1. Cria um `OSC In DAT` na porta `57121`.
2. No callback OSC, lê a mensagem `/sismoPoligono`.
3. Executa:

```python
from touchdesigner_cat_polygon_motion import handle_seismic_event

handle_seismic_event(station_index, amplitude, local_activity)
```

Os vértices são atribuídos pela ordem das 21 estações no Python. O olhar aproxima-se do vértice da estação que acabou de produzir o evento.

Usa estas expressões nos Transform TOP das pupilas:

```python
# Translate X do olho esquerdo
mod.touchdesigner_cat_polygon_motion.eye_x(-0.46)

# Translate X do olho direito
mod.touchdesigner_cat_polygon_motion.eye_x(-0.31)

# Translate Y de ambos os olhos
mod.touchdesigner_cat_polygon_motion.eye_y(0.18)
```

Quando `local_activity > 1.0`, o alvo passa automaticamente para o centro `(0, 0)` e fica congelado durante 1,8 segundos. O valor `local_activity` é a soma da atividade dos eventos próximos no tempo, não apenas a amplitude de uma estação.
