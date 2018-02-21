# coding=utf-8

speechoutput_en = {
    'launch' : "Squeezebox is online. Please try some commands.",
    'session_ended': "Hasta la vista. Baby.",
    'unknown_intent': "Sorry, I don't know how to process \"{0}\"",
    'previous': "Rewind!",
    'next': "Yep, pretty lame.",
    'current': "Currently playing: \"{0}\"" ,
    'current_by': ",by {0}",
    'current_none': "Nothing playing",
    'inc_vol': "Pumped it up",
    'dec_vol': "OK, quieter now.",
    'select_player': "Selected {1}",
    'select_player_nf': "I only found these players:{0}. Could you try again?",
    'shuffle_on': "Shuffle is now on",
    'shuffle_off': "Shuffle is now off",
    'loop_on': "Repeat is now on",
    'loop_off': "Repeat is now off",
    'player_on': "{0} is now on",
    'player_on_select': ", and is selected.",
    'player_off': "{0} is now off",
    'all_on': "Ready to rock",
    'all_off': "Silence",
    'play_random_mix_nf': "Can't find genres: {0}",
    'set_vol_nf': "Select a volume value between 0 and 10",
    'set_vol': "Volume set to {0}"
}

titleoutput_en = {
    'launch': "Welcome",
    'session_ended': "Session Ended",
    'select_player': "Selected player {0}",
    'select_player_nf': "No player called \"{0}\"",
    'select_player_nk': "Didn't recognise a player name",
    'player_on' : "Switched {0} on",
    'player_off' : "Switched {0} off"
}

textoutput_en = {
    'unknown_intent': "Unknown intent: \"{0}\"",
    'current': "Now playing: \"{0}\"",
    'inc_vol': "Increase Volume",
    'dec_vol': "Decrease Volume",
    'shuffle_on' : "Shuffle on",
    'shuffle_off' : "Shuffle off",
    'loop_on' : "Repeat on",
    'loop_off' : "Repeat off",
    'player_on' : "Switched {0} on",
    'player_off' : "Switched {1} off",
    'all_off': "Players all off",
    'all_on': "All On.",
    'play_playlist_nh_none': "There are no playlists",
    'play_playlist_nh': "Didn't hear a playlist there. "
                        "You could try the \"{0}\" playlist?",
    'play_playlist_none': "No Squeezebox playlists found",
    'play_playlist' : "Playing \"{0}\" playlist",
    'play_playlist_nf' : "Couldn't find a playlist matching \"{0}\"."
                     "How about the \"{1}\" playlist?",
    'play_random_mix': "Playing mix of {0}",
    'play_random_mix_nf': "Don't understand requested genres {0}"
}

repromptoutput_en = {
    'launch': "Try resume, pause, next, previous " \
                        "or ask Squeezebox to turn it up or down"
}

speechoutput_de = {
    'launch' : "Hier ist die Squeezebox. Was kann ich für dich tun?",
    'session_ended': "Alles klar, bis dann.",
    'unknown_intent': "Tut mit Leid, Ich weiß nicht wie ich \"{0}\" bearbeite",
    'previous': "Zurückgespult!",
    'next': "Stimmt, die Musik passt nicht.",
    'current': "Gerade läuft: \"{0}\"" ,
    'current_by': ",von {0}",
    'current_none': "Hier läuft keine Musik",
    'inc_vol': "Alles klar: lauter",
    'dec_vol': "Jetzt ist es leiser",
    'select_player': "{1} ausgewählt",
    'select_player_nf': "Ich kann nur die folgenden Geräte finden::{0}. Welches willst du?",
    'shuffle_on': "Zufallswiedergabe angeschaltet",
    'shuffle_off': "Zufallswiedergabe ausgeschaltet",
    'loop_on': "Wiederholung angeschaltet",
    'loop_off': "Wiederholung ausgeschaltet",
    'player_on': "{0} ist jetzt an",
    'player_on_select': ", und ausgewählt.",
    'player_off': "{0} ist jetzt aus",
    'all_on': "Volle Pulle angeschaltet",
    'all_off': "Genieße die Stille",
    'play_random_mix_nf': "Ich kann das Genre {0} nicht finden",
    'set_vol_nf': "Wähle eine Lautstärke zwischen 0 und 10",
    'set_vol': "Volume set to {0}"
}

titleoutput_de = {
    'launch': "Willkommen",
    'session_ended': "Session beended",
    'select_player': "Player {0} ausgewählt",
    'select_player_nf': "Player \"{0}\" nicht gefunden",
    'select_player_nk': "Player nicht verstanden",
    'player_on' : "{0} angeschaltet",
    'player_off' : "{0} ausgeschaltet"
}

textoutput_de = {
    'unknown_intent': "Unbekannte Anfrage: \"{0}\"",
    'current': "Es spielt: \"{0}\"",
    'inc_vol': "Lautstärke erhöhen",
    'dec_vol': "Lautstärke erniedrigt",
    'shuffle_on' : "Zufallswiedergabe an",
    'shuffle_off' : "Zufallswiedergabe aus",
    'loop_on' : "Wiederholung an",
    'loop_off' : "Wiederholung aus",
    'player_on' : "Player {0} angeschaltet",
    'player_off' : "Player {1} ausgeschaltet",
    'all_off': "Alle Players aus",
    'all_on': "Alle Player an",
    'play_playlist_nh_none': "Keine Wiedergabelisten gefunden",
    'play_playlist_nh': "Keine Wiedergabeliste gehört"
                        "Probiers mal mit der \"{0}\" Wiedergabeliste?",
    'play_playlist_none': "Keine Wiedergabeliste auf deiner Squeezbox gefunden",
    'play_playlist' : "Spiele die Wiedergabeliste \"{0}\"",
    'play_playlist_nf' : "Keine Wiedergabeliste \"{0}\" gefunden"
                     "Wie wäre es mit der \"{1}\" Wiedergabeliste?",
    'play_random_mix': "Spiele eine Mischung aus {0}",
    'play_random_mix_nf': "Ich hab das Ganre {0} nicht gefunden"
}


repromptoutput_de = {
    'launch': "Versuchs mal mit fortsetzten, pause, nächstes, zurück " \
                        "oder frage danach die Lautstärke zu erhöhen"
}


speechoutput = {
    'EN' : speechoutput_en,
    'DE' : speechoutput_de
}

titleoutput = {
    'EN' : titleoutput_en,
    'DE' : titleoutput_de
}

textoutput = {
    'EN' : textoutput_en,
    'DE' : textoutput_de
}

repromptoutput = {
    'EN': repromptoutput_en,
    'DE': repromptoutput_de
}
