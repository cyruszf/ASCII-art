from session import Session;

USAGE = {
    "load": "load image <filename> [as <alias>] | load session <filename>",
    "render": "render [img] | render <img> to <filename>",
    "set": "set <img> width|height|brightness|contrast <value>  eller  set width|height|brightness|contrast <value>",
    "save": "save session as <filename>",
    "help": "Kommandon: load, info, render, set, save, quit"
};

def cmd_load(sess, args):
    '''
    Ladda en bild eller session.
    '''
    if len(args) < 1:
        print(USAGE["load"]);
        return;
    sub = args[0].lower();
    if sub == "image":
        if len(args) < 2:
            print("load image <filename> [as <alias>]");
            return;
        filename = args[1];
        # Om det står "as <alias>" så plockar vi aliaset, annars None
        # alias gör att användaren kan ladda samma fil flera gånger med olika namn
        alias = args[3] if len(args) >= 4 and args[2].lower() == "as" else None;
        img = sess.add_image(filename, alias);
        disp = img.alias or img.filename;
        print(f"Laddade '{img.filename}' som {disp}.");
    elif sub == "session":
        if len(args) < 2:
            print("load session <filename>");
            return;
        try:
            sess.load_session(args[1]);
            print("Session laddad.");
        except RuntimeError as w:
            print(f"Session laddad (med varningar): {w}");
    else:
        print("Okänt load-kommando.");

def cmd_info(sess, args):
    '''Lista info om alla bilder i sessionen'''
    for ln in sess.info_lines():
        print(ln);

def cmd_render(sess, args):
    '''
    Rendera bild – antingen direkt i terminalen eller spara till fil.
    '''
    if not args:
        #uppdaterar current när en specifik bild renderas
        print(sess.render(None));
    # Kolla om syntaxen är "render <img> to <fil>"
    elif len(args) >= 3 and args[1].lower() == "to":
        sess.render_to_file(args[0], args[2]);
        print(f"Sparade ASCII till '{args[2]}'.");
    else:
        # Annars: dumpa bilden direkt här
        print(sess.render(args[0]));

def cmd_set(sess, args):
    '''
    Ändra storlek eller justering för en bild.
    Funkar både med bildnamn först, eller utan (på current).
    '''
    if len(args) < 2:
        print(USAGE["set"]);
        return;
    if len(args) >= 3:
        # Varianten med bildnamn först
        name, attr, val = args[0], args[1].lower(), args[2];
    else:
        # säkerställer att vi inte råkar ändra en obestämd bild
        if not sess.current:
            print("Ingen aktuell bild. Ladda eller ange bildnamn.");
            return;
        name, attr, val = sess.current, args[0].lower(), args[1];
    img = sess.get_by_name(name);
    if not img:
        print("Okänd bild.");
        return;
    try:
        if attr == "width":
            img.set_width(val);
            print(f"Width för '{name}' satt till {img.width}. Höjd → {img.height}.");
        elif attr == "height":
            img.set_height(val);
            print(f"Height för '{name}' satt till {img.height}. Bredd → {img.width}.");
        elif attr == "brightness":
            img.set_brightness(val);
            print(f"Brightness för '{name}' satt till {img.brightness}.");
        elif attr == "contrast":
            img.set_contrast(val);
            print(f"Contrast för '{name}' satt till {img.contrast}.");
        else:
            print("Okänt attribut. width | height | brightness | contrast gäller.");
    except ValueError as e:
        # fångar oväntade fel i kommandon och fortsätter loopen
        print(f"Fel: {e}");

def cmd_save(sess, args):
    '''
    Spara sessionen till fil (save session as <fil>)
    '''
    if len(args) >= 3 and args[0].lower() == "session" and args[1].lower() == "as":
        sess.save_session(args[2]);
        print(f"Session sparad som '{args[2]}'.");
    else:
        print(USAGE["save"]);

def cmd_help(sess, args):
    '''Visa snabbhjälp'''
    print(USAGE["help"]);
    for k in ["load", "render", "set", "save"]:
        print(f" - {USAGE[k]}");

def cmd_quit(sess, args):
    '''Hejdå och stäng ner'''
    print("Bye!");
    raise SystemExit;

# Mappar kommandosträngar till funktioner
COMMANDS = {
    "help": cmd_help,
    "load": cmd_load,
    "info": cmd_info,
    "render": cmd_render,
    "set": cmd_set,
    "save": cmd_save,
    "quit": cmd_quit,
    "q": cmd_quit
};

def main():
    '''
    Själva loopen för ASCII Art Studio
    Läser in rader från användaren, tolkar första ordet som kommando
    och skickar vidare till rätt funktion i COMMANDS.
    Fortsätter tills användaren väljer att avsluta
    '''
    print("Welcome to ASCII Art Studio!");
    sess = Session();
    prompt = "AAS: ";
    while True:
        line = input(prompt).strip().lower();
        if line in ("quit", "q"):
            print("Bye!");
            break;
        if not line:
            continue;

        parts = line.split();
        cmd, args = parts[0], parts[1:];
        if cmd in COMMANDS:
            try:
                COMMANDS[cmd](sess, args);
            except Exception as e:
                print(f"Fel: {e}");
        else:
            print("Okänt kommando. Skriv 'help'.");

if __name__ == "__main__":
    main();
