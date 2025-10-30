import json;
from asciiartimage import AsciiArtImage;

class Session:
    '''
    Håller ihop en ASCII Art Studio-session.
    Vet vilka bilder som finns, vilken som är "current",
    och kan spara/ladda sessioner eller spotta ut renderingar.
    '''

    def __init__(self):
        '''Startar på noll – inga bilder, ingen current.'''
        self.images = {};
        self.current = None;

    def add_image(self, filename, alias=None):
        '''
        Laddar in en ny bild och gör den till current.

        :param filename: Sökväg till bildfilen
        :param alias: Valfritt alias att använda som nyckel
        :return: AsciiArtImage-objektet
        '''
        img = AsciiArtImage(filename, alias);
        #laddar bilden i minnet så att efterföljande operationer kan göras
        img.load();  # faktiska pixlar in
        key = alias if alias else filename;
        self.images[key] = img;
        #så att den senast inladdade bilden alltid blir aktiv automatiskt
        self.current = key;
        return img;

    def get_by_name(self, name):
        '''
        Hitta bildobjekt från alias eller filnamn.
        Byter även 'current' till den här bilden om den hittas.
        '''
        if not name:
            return None;
        if name in self.images:
            self.current = name;
            return self.images[name];
        # Leta igenom alla om vi inte hittar på nyckeln direkt
        for img in self.images.values():
            if img.filename == name or img.alias == name:
                self.current = img.alias if img.alias else img.filename;
                return img;
        return None;

    def render(self, name=None):
        '''
        Returnerar en ASCII-sträng av bilden.
        Om inget namn görs på på current.
        '''
        img = self.get_by_name(name) if name else self.images.get(self.current);
        if not img:
            raise ValueError("Ingen bild att rendera.");
        return img.render_to_string();

    def render_to_file(self, name, out_filename):
        '''
        Rendera och spara till textfil.
        '''
        art = self.render(name);
        with open(out_filename, "w", encoding="utf-8") as f:
            f.write(art + "\n");

    def info_lines(self):
        '''
        Returnerar en lista med infotext om alla bilder
        och vem som är current just nu.
        '''
        lines = ["=== Current session"];
        for img in self.images.values():
            lines.append(img.info_string());
        cur = self.current if self.current else "(ingen)";
        lines.append(f"Current image: {cur}");
        return lines;

    def save_session(self, filename):
        '''
        Sparar sessionens metadata till JSON.
        Obs: ingen pixeldata, bara info från to_dict().
        '''
        data = {
            "images": [img.to_dict() for img in self.images.values()],
            "current": self.current
        };
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2);

    def load_session(self, filename):
        '''
        Laddar in en session från JSON-fil.
        Skapar nya AsciiArtImage-objekt från sparad metadata.
        '''
        with open(filename, "r", encoding="utf-8") as f:
            data = json.load(f);
        self.images = {};
        for d in data.get("images", []):
            try:
                img = AsciiArtImage.from_dict(d);
                key = img.alias if img.alias else img.filename;
                self.images[key] = img;
            except Exception:
                # Om nåt gick fel med just den bilden – hoppa vidare
                print(f"Kunde inte ladda '{d.get('filename')}'");
        self.current = data.get("current");
