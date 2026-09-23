"""Narrator copy per teaching language. `{...}` fields are filled by the planner."""
from __future__ import annotations

LEVEL_NAME = {"en": "Level 1", "es": "Nivel 1"}

NARRATOR: dict[str, dict[str, str]] = {
    "en": {
        "intro": "This is Maaya T'aan, {level}, lesson {n}.",
        "l1_welcome": "Maaya T'aan is Yucatec Maya, the language of the Yucatán Peninsula, spoken today by nearly a million people. "
                      "Listen to this conversation between two speakers. Don't try to understand it yet, just listen to the sounds.",
        "l1_method": "In the next thirty minutes you're not only going to understand this conversation, you're going to be able to take part in one like it yourself. "
                     "Yucatec Maya has some sounds English doesn't have. Don't worry about how anything is spelled. Just listen, and imitate what you hear. "
                     "Whenever you hear a pause, that's your turn. Say the words out loud, in a full voice, even if you're not sure. "
                     "Listen to the conversation once more.",
        "once_more": "Listen to it once more.",
        "with_meaning": "Now, listen again, and this time you'll hear the meaning of each line first.",
        "by_end": "By the end of this lesson you'll be able to say every line yourself. Let's begin.",
        "first_item": "Let's begin with how to say, {meaning}. Listen.",
        "next_item": "Now how to say, {meaning}. Listen.",
        "word_for_word": "Word for word, that's, {literal}.",
        "build_up": "We'll build it up from the end, one sound at a time. Listen and repeat.",
        "listen_repeat": "Listen and repeat.",
        "say": "Say, {meaning}.",
        "how_do_you_say": "How do you say, {meaning}?",
        "reconstruct": "{setting} This time you say each line. I'll give you the meaning.",
        "repeat_lines": "Now repeat each line of the conversation after the speaker.",
        "repeat_round": "Listen and repeat each phrase, first slowly, then at normal speed.",
        "closing": "Now listen to a whole conversation. {setting} See how much you understand.",
        "end": "This is the end of lesson {n}.",
    },
    "es": {
        "intro": "Esto es Maaya T'aan, {level}, lección {n}.",
        "l1_welcome": "Maaya T'aan es el maya yucateco, la lengua de la península de Yucatán, hablada hoy por casi un millón de personas. "
                      "Escucha esta conversación entre dos hablantes. No intentes entenderla todavía; solo escucha los sonidos.",
        "l1_method": "En los próximos treinta minutos no solo vas a entender esta conversación: vas a poder participar en una como esta. "
                     "El maya tiene algunos sonidos que el español no tiene. No te preocupes por cómo se escribe nada. Solo escucha e imita lo que oyes. "
                     "Cada vez que oigas una pausa, es tu turno. Di las palabras en voz alta, con voz plena, aunque no estés seguro. "
                     "Escucha la conversación una vez más.",
        "once_more": "Escúchala una vez más.",
        "with_meaning": "Ahora escucha de nuevo; esta vez oirás primero el significado de cada línea.",
        "by_end": "Al final de esta lección vas a poder decir cada línea por tu cuenta. Empecemos.",
        "first_item": "Empecemos con cómo se dice, {meaning}. Escucha.",
        "next_item": "Ahora, cómo se dice, {meaning}. Escucha.",
        "word_for_word": "Palabra por palabra, es, {literal}.",
        "build_up": "Vamos a construirla desde el final, sonido por sonido. Escucha y repite.",
        "listen_repeat": "Escucha y repite.",
        "say": "Di, {meaning}.",
        "how_do_you_say": "¿Cómo se dice, {meaning}?",
        "reconstruct": "{setting} Esta vez tú dices cada línea. Yo te doy el significado.",
        "repeat_lines": "Ahora repite cada línea de la conversación después del hablante.",
        "repeat_round": "Escucha y repite cada frase, primero despacio y luego a velocidad normal.",
        "closing": "Ahora escucha una conversación completa. {setting} Fíjate en cuánto entiendes.",
        "end": "Este es el final de la lección {n}.",
    },
}

NARRATOR_VOICE = {"en": ("a", "af_heart"), "es": ("e", "ef_dora")}  # Kokoro (lang_code, voice)
