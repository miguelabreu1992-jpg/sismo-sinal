// Receptor alternativo: timbres diferentes por grupo de estacoes.

(
var makeSynth;
var window;
var menu;
var startButton;
var iniciarAudio;

makeSynth = { |name, body|
    SynthDef(name, { |freq = 440, amp = 0.3, dur = 0.3, out = 0|
        var env = EnvGen.kr(Env.perc(0.012, dur), doneAction: 2);
        var sig = body.value(freq, amp) * env * 0.08;
        Out.ar(out, sig ! 2);
    }).add;
};

makeSynth.(\sismoNorte, { |freq, amp| Pulse.ar(freq, 0.25) * amp });
makeSynth.(\sismoSul, { |freq, amp| Saw.ar(freq) * amp });
makeSynth.(\sismoEuropa, { |freq, amp| SinOsc.ar(freq) * (1 + SinOsc.kr(3).range(-0.25, 0.25)) * amp });
makeSynth.(\sismoAsia, { |freq, amp| PMOsc.ar(freq, freq * 1.5, 1.5) * amp });
makeSynth.(\sismoAfrica, { |freq, amp| (PinkNoise.ar(0.35) + SinOsc.ar(freq)) * amp });
makeSynth.(\sismoOceania, { |freq, amp| SinOsc.ar(freq, SinOsc.kr(2).range(-1, 1)) * amp });
makeSynth.(\sismoAntartida, { |freq, amp| SinOsc.ar(freq) * amp });

iniciarAudio = {
    s.waitForBoot({
        OSCdef(\sismoEstacaoListener, { |msg|
        var freq = msg[1].asFloat;
        var amp = msg[2].asFloat;
        var station = msg[3].asString;
        var synthName =
            if(["ANMO", "COLA", "HRV"].includes(station)) { \sismoNorte } {
            if(["RCBR", "LCO", "BOCO"].includes(station)) { \sismoSul } {
            if(["KONO", "KEV", "ANTO"].includes(station)) { \sismoEuropa } {
            if(["MAJO", "MAKZ", "TATO"].includes(station)) { \sismoAsia } {
            if(["TSUM", "LSZ", "MACI"].includes(station)) { \sismoAfrica } {
            if(["CTAO", "SNZO", "NWAO"].includes(station)) { \sismoOceania } { \sismoAntartida }}}}}};
        Synth(synthName, [\freq, freq, \amp, amp, \dur, 0.3]);
        ("Estacao: " ++ station ++ " | synth: " ++ synthName).postln;
        }, '/sismoEstacao');

        OSCdef(\sismoFallbackListener, { |msg|
            var freq = msg[1].asFloat;
            var amp = msg[2].asFloat;
            Synth(\sismoNorte, [\freq, freq, \amp, amp, \dur, 0.3]);
            ("OSC fallback: " ++ freq ++ " Hz").postln;
        }, '/sismo');

        s.sync;
        Synth(\sismoNorte, [\freq, 440, \amp, 0.8, \dur, 0.8]);
        "Receptor de synths por estacao ativo em /sismoEstacao".postln;
    });
};

window = Window("Saida de audio - Synths por estacao", Rect(300, 300, 620, 150)).front;
menu = PopUpMenu(window, Rect(20, 35, 580, 30));
startButton = Button(window, Rect(20, 85, 580, 35));
menu.items_(ServerOptions.outDevices);
menu.value_(0);
StaticText(window, Rect(20, 10, 580, 20))
    .string_("Escolhe as colunas do portatil ou a placa de som externa:");
startButton.states_([["Iniciar audio"]]);
startButton.action_({
    s.options.outDevice = menu.items[menu.value];
    ("Saida escolhida: " ++ menu.items[menu.value]).postln;
    window.close;
    iniciarAudio.value;
});

)
