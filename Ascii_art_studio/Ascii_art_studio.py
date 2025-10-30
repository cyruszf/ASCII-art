from PIL import Image, ImageEnhance;
import json;

ASCII_CHARS = "@%#*+=-:. ";  # Från mörkt till ljus
DEFAULT_WIDTH = 50;           # Standardbredd (krav)
STRETCH = 0.5;                # Höjdkorrigering för monospace


class AsciiArtImage:
    """
    Håller data och inställningar för en bild och kan rendera till ASCII.
    Stöder storlek (width/height med proportion), brightness och contrast.
    """
    def __init__(self, filename, alias=None):
        self.filename = filename;
        self.alias = alias;
        self.image = None;          # Gråskalebild (Pillow)
        self.orig_size = None;      # (w,h)
        self.width = DEFAULT_WIDTH; # Target-bredd i tecken
        self.height = None;         # Target-höjd i rader (beräknas)
        self.brightness = 1.0;      # 1.0 = oförändrad
        self.contrast = 1.0;        # 1.0 = oförändrad

    def load(self):
        '''
        Laddar bilden från disk och konverterar till gråskala.
        '''
        try:
            with Image.open(self.filename) as img:
                self.image = img.convert("L");
                self.orig_size = self.image.size;
            if self.width is None:
                self.width = DEFAULT_WIDTH;
            self._calc_height_from_width();
        except Exception as e:
            print(f"Fel vid laddning av bild '{self.filename}': {e}");
            self.image = None;

    def _aspect(self):
        '''
        Returnerar höjd/bredd för originalbild (float).
        '''
        if not self.orig_size or self.orig_size[0] == 0:
            return 1.0;
        return self.orig_size[1] / self.orig_size[0];

    def _calc_height_from_width(self):
        '''
        Beräknar height utifrån width och proportioner (inkl STRETCH).
        '''
        ar = self._aspect();
        self.height = max(1, int(round(self.width * ar * STRETCH)));

    def _calc_width_from_height(self):
        '''
        Beräknar width utifrån height och proportioner (inkl STRETCH).
        '''
        ar = self._aspect();
        denom = ar * STRETCH if ar * STRETCH != 0 else 1.0;
        self.width = max(1, int(round(self.height / denom)));

    def set_width(self, w):
        '''
        Sätter bredd (positivt heltal) och räknar om höjd.
        '''
        try:
            w = int(w);
            if w <= 0:
                raise ValueError;
            self.width = w;
            self._calc_height_from_width();
        except Exception:
            raise ValueError("Width måste vara ett positivt heltal.");

    def set_height(self, h):
        '''
        Sätter höjd (positivt heltal) och räknar om bredd.
        '''
        try:
            h = int(h);
            if h <= 0:
                raise ValueError;
            self.height = h;
            self._calc_width_from_height();
        except Exception:
            raise ValueError("Height måste vara ett positivt heltal.");

    def set_brightness(self, b):
        '''
        Sätter ljusstyrka (float > 0).
        '''
        try:
            b = float(b);
            if b <= 0:
                raise ValueError;
            self.brightness = b;
        except Exception:
            raise ValueError("Brightness måste vara ett positivt tal (t.ex. 0.8, 1.0, 1.2).");

    def set_contrast(self, c):
        '''
        Sätter kontrast (float > 0).
        '''
        try:
            c = float(c);
            if c <= 0:
                raise ValueError;
            self.contrast = c;
        except Exception:
            raise ValueError("Contrast måste vara ett positivt tal (t.ex. 0.8, 1.0, 1.2).");

    def _enhanced_resized(self):
        '''
        Returnerar justerad (brightness/contrast) och skalad kopia enligt target size.
        '''
        if not self.image:
            raise RuntimeError("Ingen bild laddad.");
        if not self.height or self.height <= 0:
            self._calc_height_from_width();
        img = self.image;
        if self.brightness != 1.0:
            img = ImageEnhance.Brightness(img).enhance(self.brightness);
        if self.contrast != 1.0:
            img = ImageEnhance.Contrast(img).enhance(self.contrast);
        return img.resize((self.width, self.height), resample=Image.BILINEAR);

    def render_to_string(self):
        '''
        Skapar ASCII-konst och returnerar som sträng.
        '''
        img = self._enhanced_resized();
        pixels = img.getdata();
        n = len(ASCII_CHARS) - 1;
        chars = [ASCII_CHARS[(p * n) // 255] for p in pixels];
        lines = [];
        for i in range(0, len(chars), self.width):
            lines.append(''.join(chars[i:i + self.width]));
        return '\n'.join(lines);

    def render_print(self):
        '''
        Skriver ut ASCII-konst direkt.
        '''
        try:
            art = self.render_to_string();
            print(art);
        except Exception as e:
            print(f"Fel vid rendering: {e}");

    def info_string(self):
        '''
        Returnerar informationsrad(er) om bilden.
        '''
        size_str = f"{self.orig_size}" if self.orig_size else "(okänd)";
        return (
            f"{self.alias if self.alias else self.filename} "
            f"filename: {self.filename} "
            f"size: {size_str} "
            f"target size: ({self.width}, {self.height}) "
            f"brightness: {self.brightness} "
            f"contrast: {self.contrast}"
        );

    def to_dict(self):
        '''
        Exporterar metadata (utan pixlar) för session.
        '''
        return {
            "filename": self.filename,
            "alias": self.alias,
            "width": self.width,
            "height": self.height,
            "brightness": self.brightness,
            "contrast": self.contrast
        };

    @staticmethod
    def from_dict(d):
        '''
        Skapar instans från sparad metadata och laddar bild från fil.
        '''
        img = AsciiArtImage(d["filename"], d.get("alias"));
        img.width = int(d.get("width", DEFAULT_WIDTH));
        img.height = int(d["height"]) if d.get("height") else None;
        img.brightness = float(d.get("brightness", 1.0));
        img.contrast = float(d.get("contrast", 1.0));
        img.load();
        return img;


class Session:
    '''
    Håller alla bilder i en session och spårar current.
    '''
    def __init__(self):
        self.images = {};   # key: alias eller filnamn → AsciiArtImage
        self.current = None;

    def add_image(self, filename, alias=None):
        '''
        Laddar bild och lägger till i sessionen. Returnerar instansen.
        '''
        img = AsciiArtImage(filename, alias);
        img.load();
        key = alias if alias else filename;
        self.images[key] = img;
        self.current = key;
        return img;

    def get_by_name(self, name):
        '''
        Hämtar bild via alias eller filnamn. Sätter current till denna.
        '''
        if not name:
            return None;
        # exakt träff på alias-nyckel
        if name in self.images:
            self.current = name;
            return self.images[name];
        # sök via filename match
        for img in self.images.values():
            if img.filename == name or img.alias == name:
                self.current = img.alias if img.alias else img.filename;
                return img;
        return None;

    def render(self, name=None):
        '''
        Returnerar ASCII-sträng för given bild eller current.
        '''
        img = self.get_by_name(name) if name else (self.images.get(self.current) if self.current else None);
        if not img:
            raise ValueError("Ingen bild att rendera.");
        return img.render_to_string();

    def render_to_file(self, name, out_filename):
        '''
        Skriver ASCII till fil.
        '''
        art = self.render(name);
        with open(out_filename, "w", encoding="utf-8") as f:
            f.write(art + "\n");

    def info_lines(self):
        '''
        Returnerar lista med informationsrader + current.
        '''
        lines = ["=== Current session"];
        for img in self.images.values():
            lines.append(img.info_string());
        cur = self.current if self.current else "(ingen)";
        lines.append(f"Current image: {cur}");
        return lines;

    def save_session(self, filename):
        '''
        Sparar session till JSON (utan pikseldata).
        '''
        data = {
            "images": [img.to_dict() for img in self.images.values()],
            "current": self.current
        };
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2);

    def load_session(self, filename):
        '''
        Läser in session från JSON, laddar om bildfiler, sätter current.
        '''
        with open(filename, "r", encoding="utf-8") as f:
            data = json.load(f);
        self.images = {};
        for d in data.get("images", []):
            try:
                img = AsciiArtImage.from_dict(d);
                key = img.alias if img.alias else img.filename;
                self.images[key] = img;
            except Exception as e:
                print(f"Varning: kunde inte ladda '{d.get('filename')}': {e}");
        self.current = data.get("current");


def main():
    print("Welcome to ASCII Art Studio!");  # Håller oss nära exempeltexten
    sess = Session();
    prompt = "AAS: ";

    while True:
        try:
            line = input(prompt).strip();
        except (EOFError, KeyboardInterrupt):
            print("\nBye!");
            break;

        if not line:
            continue;

        parts = line.split();
        cmd = parts[0].lower();

        try:
            if cmd == "load" and len(parts) >= 2:
                # load image filename [as alias]
                if parts[1].lower() == "image":
                    if len(parts) < 3:
                        print("Användning: load image <filename> [as <alias>]");
                        continue;
                    filename = parts[2];
                    alias = None;
                    if len(parts) >= 5 and parts[3].lower() == "as":
                        alias = parts[4];
                    img = sess.add_image(filename, alias);
                    disp = img.alias if img.alias else img.filename;
                    print(f"Laddade '{img.filename}' som {disp}.");
                elif parts[1].lower() == "session":
                    if len(parts) < 3:
                        print("Användning: load session <filename>");
                        continue;
                    sess.load_session(parts[2]);
                    print("Session laddad.");
                else:
                    print("Ogiltigt load-kommando. Använd 'load image' eller 'load session'.");

            elif cmd == "info":
                for ln in sess.info_lines():
                    print(ln);

            elif cmd == "render":
                # render | render img | render img to filename
                if len(parts) == 1:
                    art = sess.render(None);
                    print(art);
                elif len(parts) >= 2 and (len(parts) < 4 or parts[2].lower() != "to"):
                    name = parts[1];
                    art = sess.render(name);
                    print(art);
                elif len(parts) >= 4 and parts[2].lower() == "to":
                    name = parts[1];
                    outfn = parts[3];
                    sess.render_to_file(name, outfn);
                    print(f"Sparade ASCII till '{outfn}'.");
                else:
                    print("Användning: render [img] | render <img> to <filename>");

            elif cmd == "set" and len(parts) >= 4:
                # set img width/height/brightness/contrast num
                name = parts[1];
                attr = parts[2].lower();
                val = parts[3];
                img = sess.get_by_name(name);
                if not img:
                    print("Okänd bild.");
                    continue;
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
                    print("Okänt attribut. Använd width | height | brightness | contrast.");

            elif cmd == "save" and len(parts) >= 2:
                # save session as filename
                if parts[1].lower() == "session":
                    if len(parts) >= 4 and parts[2].lower() == "as":
                        sess.save_session(parts[3]);
                        print(f"Session sparad som '{parts[3]}'.");
                    else:
                        print("Användning: save session as <filename>");
                else:
                    print("Okänt save-kommando. Använd 'save session as <filename>'.");

            elif cmd == "quit":
                print("Bye!");
                break;

            else:
                print("Okänt kommando.");
        except Exception as e:
            print(f"Fel: {e}");

if __name__ == "__main__":
    main();
