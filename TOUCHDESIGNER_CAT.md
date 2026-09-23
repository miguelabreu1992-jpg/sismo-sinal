# Janela do gato no TouchDesigner

A orquestra envia os eventos OSC do SuperCollider para `57120` e duplica-os para o TouchDesigner em `57121`.

Mensagem recebida:

```text
address: /sismo
values: [frequency_hz, amplitude]
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

Como o desenho é uma imagem única, as pupilas são sobrepostas como duas pequenas formas pretas. Para uma animação mais rigorosa, prepara depois uma versão com olhos e pupilas em camadas transparentes.

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

## Movimento dos olhos

Cria dois `LFO CHOP`, um para cada olho:

- Forma: `Sine`
- Frequency: entre `0.3` e `0.6`
- Amplitude: pequena, entre `0.01` e `0.025`

Liga cada LFO a um `Math CHOP` e depois exporta para os parâmetros `Translate X` dos Transform TOP dos olhos.

Para o movimento vertical, usa um segundo LFO mais lento ou um `Noise CHOP`.

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

## Teste

1. Abre o loop do TouchDesigner.
2. Inicia o projeto com `start_visualizer.bat`.
3. No TouchDesigner, confirma que o `OSC In CHOP` está a receber dados em `57121`.
4. Move temporariamente o threshold para baixo no visualizer principal se quiseres mais eventos.
5. Observa as pupilas: devem oscilar normalmente e parar quando chegar um pico.

O SuperCollider continua a usar `57120`; o TouchDesigner usa `57121`, evitando conflito entre os dois receptores OSC.
