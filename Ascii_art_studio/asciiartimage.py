from PIL import Image, ImageEnhance;
from constants import ASCII_CHARS, DEFAULT_WIDTH, STRETCH;

class AsciiArtImage:
    '''Hanterar en bilds metadata och kan generera ASCII‑konst av den.'''

    def __init__(self, filename, alias=None):
        '''Initiera med filnamn och ev. alias, sätter startvärden.'''
        self.filename = filename;
        self.alias = alias;
        self.image = None;
        self.orig_size = None;
        self.width = DEFAULT_WIDTH;
        self.height = None;
        self.brightness = 1.0;
        self.contrast = 1.0;

    def load(self):
        '''Läs in bilden från disk, konvertera till gråskala och beräkna höjd.'''
        try:
            with Image.open(self.filename) as img:
                self.image = img.convert("L");
                # sparar originalstorleken så att proportionerna kan beräknas vid resize
                self.orig_size = self.image.size;
        except Exception as e:
            raise FileNotFoundError(f"Kunde inte ladda bild '{self.filename}': {e}");
        if self.width is None:
            self.width = DEFAULT_WIDTH;
        #ser till att höjden alltid matchar bredden med bibehållen aspect ratio och STRETCH
        self._calc_height_from_width();

    def _aspect(self):
        '''Returnera höjd/bredd-förhållandet för originalet.'''
        if not self.orig_size or self.orig_size[0] == 0:
            return 1.0;
        return self.orig_size[1] / self.orig_size[0];

    def _calc_height_from_width(self):
        '''Beräkna höjd baserat på nuvarande bredd och proportioner.'''
        ar = self._aspect();
        self.height = max(1, int(round(self.width * ar * STRETCH)));

    def _calc_width_from_height(self):
        '''Beräkna bredd baserat på nuvarande höjd och proportioner.'''
        ar = self._aspect();
        denom = ar * STRETCH if ar * STRETCH != 0 else 1.0;
        self.width = max(1, int(round(self.height / denom)));

    def set_width(self, w):
        '''
        Sätt ny bredd och räkna om höjd.
        :param w: positivt heltal i antal tecken
        :raises ValueError: om w inte är ett positivt heltal
        '''
        try:
            w = int(w);
            if w <= 0:
                raise ValueError;
        except Exception:
            raise ValueError("Width måste vara ett positivt heltal");
        self.width = w;
        self._calc_height_from_width();

    def set_height(self, h):
        '''Sätt ny höjd (positivt heltal) och räkna om bredd.'''
        try:
            h = int(h);
            if h <= 0:
                raise ValueError;
        except Exception:
            raise ValueError("Height måste vara ett positivt heltal");
        self.height = h;
        self._calc_width_from_height();

    def set_brightness(self, b):
        '''Sätt ljusstyrkan (>1 ljusare, <1 mörkare).'''
        try:
            b = float(b);
            if b <= 0:
                raise ValueError;
        except Exception:
            raise ValueError("Brightness måste vara ett positivt tal");
        self.brightness = b;

    def set_contrast(self, c):
        '''Sätt kontrastnivån (>1 hårdare kontrast, <1 mjukare).'''
        try:
            c = float(c);
            if c <= 0:
                raise ValueError;
        except Exception:
            raise ValueError("Contrast måste vara ett positivt tal");
        self.contrast = c;

    def _enhanced_resized(self):
        '''Returnera kopia av bilden med ljus/kontrast-justering och rätt storlek.'''
        if not self.image:
            raise RuntimeError("Ingen bild laddad");
        if not self.height or self.height <= 0:
            self._calc_height_from_width();
        img = self.image;
        if self.brightness != 1.0:
            img = ImageEnhance.Brightness(img).enhance(self.brightness);
        if self.contrast != 1.0:
            img = ImageEnhance.Contrast(img).enhance(self.contrast);
        return img.resize((self.width, self.height), resample=Image.BILINEAR);

    def render_to_string(self):
        '''Konvertera bilden till ASCII-konst som sträng.'''
        img = self._enhanced_resized();
        pixels = img.getdata();
        n = len(ASCII_CHARS) - 1;
        chars = [ASCII_CHARS[(p * n) // 255] for p in pixels];
        lines = [''.join(chars[i:i + self.width]) for i in range(0, len(chars), self.width)];
        return '\n'.join(lines);

    def info_string(self):
        '''Returnera en rad text med bildens inställningar och metadata.'''
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
        '''Exportera metadata till en dict (för sparning i session).'''
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
        '''Skapa AsciiArtImage från sparad metadata och ladda bilden.'''
        img = AsciiArtImage(d["filename"], d.get("alias"));
        img.width = int(d.get("width", DEFAULT_WIDTH));
        img.height = int(d["height"]) if d.get("height") else None;
        img.brightness = float(d.get("brightness", 1.0));
        img.contrast = float(d.get("contrast", 1.0));
        img.load();
        return img;
