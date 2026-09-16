// Arranque automatico do receptor OSC para o launcher do Windows.

s.waitForBoot({
    SynthDef(\sismoNota, { |freq = 440, amp = 0.3, dur = 0.3, out = 0|
        var env = EnvGen.kr(Env.perc(0.005, dur), doneAction: 2);
        var sig = SinOsc.ar(freq) * env * amp;
        Out.ar(out, sig ! 2);
    }).add;

    OSCdef(\sismoListener, { |msg|
        var freq = msg[1];
        var amp = msg[2];
        ("OSC recebido: " ++ freq.round(0.1) ++ " Hz, amp " ++ amp.round(0.01)).postln;
        Synth(\sismoNota, [\freq, freq, \amp, amp, \dur, 0.3]);
    }, '/sismo');

    s.sync;
    Synth(\sismoNota, [\freq, 440, \amp, 0.2, \dur, 0.8]);
    "Receptor sismo ativo em /sismo".postln;
});

s.boot;
