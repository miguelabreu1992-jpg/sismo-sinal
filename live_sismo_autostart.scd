// Receptor OSC com escolha de saida de audio antes do arranque.

(
var devices = ServerOptions.devices;
var window = Window("Saida de audio - Sismo Orchestra", Rect(300, 300, 620, 150)).front;
var menu = PopUpMenu(window, Rect(20, 35, 580, 30));
var startButton = Button(window, Rect(20, 85, 580, 35));

menu.items_(devices);
menu.value_(0);
StaticText(window, Rect(20, 10, 580, 20))
    .string_("Escolhe as colunas do portatil ou a placa de som externa:");
startButton.states_([["Iniciar audio"]]);
startButton.action_({
    var selectedDevice = menu.items[menu.value];
    s.options.outDevice = selectedDevice;
    ("Saida escolhida: " ++ selectedDevice).postln;
    window.close;

    s.waitForBoot({
        SynthDef(\sismoNota, { |freq = 440, amp = 0.3, dur = 0.3, out = 16|
            var env = EnvGen.kr(Env.perc(0.012, dur), doneAction: 2);
            var sig = SinOsc.ar(freq) * env * amp * 0.22;
            Out.ar(out, sig ! 2);
        }).add;

        SynthDef(\sismoMaster, { |in = 16, out = 0|
            var sig = In.ar(in, 2);
            sig = LeakDC.ar(sig);
            sig = Limiter.ar(sig, 0.82, 0.01);
            Out.ar(out, sig);
        }).add;

        OSCdef(\sismoListener, { |msg|
            var freq = msg[1];
            var amp = msg[2];
            ("OSC recebido: " ++ freq.round(0.1) ++ " Hz, amp " ++ amp.round(0.01)).postln;
            Synth(\sismoNota, [\freq, freq, \amp, amp, \dur, 0.3]);
        }, '/sismo');

        s.sync;
        Synth(\sismoMaster, [], addAction: \addToTail);
        Synth(\sismoNota, [\freq, 440, \amp, 0.2, \dur, 0.8]);
        "Receptor sismo ativo em /sismo".postln;
    });
    s.boot;
});
)
