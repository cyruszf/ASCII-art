# Globala konstanter som används i hela programmet:
# - Samlade på ett ställe för att undvika hårdkodade värden utspridda i koden
# - Gör koden tydligare, enklare att underhålla och justera vid behov
# - Har fasta värden som inte ändras under programmets körning
ASCII_CHARS = "@%#*+=-:. ";   # Från mörkast (@) till ljusast (mellanslag)
DEFAULT_WIDTH = 50;           # Standardbredd på ASCII-bilder (antal tecken)
STRETCH = 0.5;                 # Höjdkorrigering för att kompensera monospace-proportioner
