# 🧟 Zombie War : Filles vs Garçons (jeu pour live TikTok)

Le jeu tient dans un seul fichier : `index.html`. Il s'affiche en vertical (1080×1920). Le bas de l'écran reste libre pour le chat TikTok.

## Tester sans être en live
Ouvre `index.html` dans Chrome en ajoutant `?test` à la fin de l'adresse. Par exemple :
`file:///C:/.../zombie-war/index.html?test`

| Touche | Team Filles | Touche | Team Garçons |
|---|---|---|---|
| 1 | commentaire → zombie | A | commentaire → zombie |
| 2 | cadeau 1 pièce → zombie rapide | Z | zombie rapide |
| 3 | cadeau 5 pièces → tourelle | E | tourelle |
| 4 | cadeau 30 pièces → mur | R | mur |
| 5 | cadeau 100 pièces → zombie géant | T | zombie géant |
| 6 | cadeau 500 pièces → météores | Y | météores |
| 7 | +50 likes | U | +50 likes |

Autres touches :
- **D** : démo automatique (de faux spectateurs jouent)
- **N** : nouvelle manche
- **M** : couper le son
- **H** : afficher ou masquer l'aide

Ajoute `?demo` à l'adresse pour lancer la démo dès l'ouverture.

## Brancher sur TikTok (avec TikFinity)
1. Installe **TikFinity** sur le PC, connecte ton compte TikTok et lance-le.
2. Dans **OBS** (ou TikTok LIVE Studio) : ajoute une source **Navigateur**.
   - Coche « Fichier local » et choisis `index.html`.
   - Largeur **1080**, hauteur **1920**.
   - Coche « Contrôler l'audio via OBS » pour avoir les sons.
3. Le jeu se connecte tout seul à TikFinity (`ws://localhost:21213`). En bas à droite, le point devient vert avec « TikFinity connecté ».
4. Si ton TikFinity utilise un autre port, ajoute `?ws=ws://localhost:PORT/` à l'adresse.

## Règles du jeu
- Les spectateurs écrivent **F** (ou « filles », 👧) ou **G** (ou « garçons », 👦) pour choisir leur team. Ceux qui n'ont pas choisi sont placés dans la team la plus petite.
- **1 commentaire = 1 zombie**, avec un maximum d'un toutes les 2 secondes par personne.
- **100 likes = une vague** de 8 zombies.
- **Les cadeaux** déclenchent des pouvoirs selon leur valeur en pièces : zombie rapide, tourelle (améliorée jusqu'au niveau 3), mur, zombie géant, pluie de météores.
- Une base qui passe sous 20 % de vie entre en **RAGE** : ses tirs sont doublés pendant 30 s, une fois par manche.
- Une manche dure 4 minutes, ou s'arrête dès qu'une base tombe. Le score s'additionne d'une manche à l'autre.
- Rien n'est à gagner : les cadeaux déclenchent seulement des actions à l'écran.

## Réglages
Tout est dans le bloc `CONFIG`, en haut du script de `index.html` : durée des manches, vie des bases, paliers des cadeaux, nombre de likes par vague, etc.
