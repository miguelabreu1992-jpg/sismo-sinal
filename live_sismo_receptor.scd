// ================================================================
// RECETOR OSC — toca os picos sísmicos em tempo real
// Recebe mensagens do script Python (live_sismo_osc.py) e dispara
// uma nota por cada pico sísmico detetado, à medida que acontece.
// ================================================================


// ---------------------------------------------------------------
// PASSO 1 — LIGAR O SERVIDOR DE ÁUDIO
// ---------------------------------------------------------------
(
s.boot;
)


// ---------------------------------------------------------------
// PASSO 2 — O INSTRUMENTO (igual ao da versão offline)
// ---------------------------------------------------------------
(
SynthDef(\sismoNota, { |freq = 440, amp = 0.3, dur = 0.3, out = 0|
	var env = EnvGen.kr(Env.perc(0.005, dur), doneAction: 2);
	var sig = SinOsc.ar(freq) * env * amp;
	Out.ar(out, sig ! 2);
}).add;
)


// ---------------------------------------------------------------
// PASSO 3 — OUVIR AS MENSAGENS OSC DO PYTHON
// ---------------------------------------------------------------
// O Python envia para o endereço "/sismo" com dois argumentos:
// [freq, amp]. Cada mensagem recebida dispara imediatamente uma nota.

(
OSCdef(\sismoListener, { |msg|
	var freq = msg[1];
	var amp  = msg[2];
	Synth(\sismoNota, [\freq, freq, \amp, amp, \dur, 0.3]);
}, '/sismo');

"À escuta de picos sísmicos em '/sismo' ... (mantém este bloco ativo)".postln;
)


// ---------------------------------------------------------------
// Para parar de escutar (se quiseres desligar sem fechar o SC):
// ---------------------------------------------------------------
// OSCdef(\sismoListener).free;
