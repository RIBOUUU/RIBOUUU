# Mise en ligne YouTube : le combat de bonhommes

## Fichiers
| Fichier | Rôle |
|---|---|
| `COMBAT_FINAL_YouTube_1080x1920_60fps.mp4` | La vidéo à mettre en ligne (Short vertical, environ 35 s) |
| `miniature_verticale_1080x1920.jpg` | Image de couverture verticale |
| `miniature_1280x720.jpg` | Miniature 16:9, si tu la réutilises ailleurs (compilation, version longue) |
| `combat_base_1080p60.mp4` | Rendu brut, sans textes ni accroche (pour retravailler) |

## Règles appliquées, et poussées plus loin

### 1. Technique (aide YouTube : paramètres d'encodage recommandés)
| Règle YouTube | Ce que j'ai fait |
|---|---|
| H.264, profil High, progressif, CABAC | H.264 High, progressif, CABAC (`-coder 1`), 2 images B |
| Résolution la plus haute disponible | Rendu natif en **1080×1920**, pas d'agrandissement : chaque image est recalculée à cette taille |
| 1080p à 60 i/s : environ 12 Mbit/s | **60 i/s** natif. Qualité constante très haute (CRF 16), plafond à 30 Mbit/s, soit au-dessus de la recommandation pour garder les étincelles et les particules nettes après la recompression YouTube |
| Son stéréo à 384 kbit/s | AAC stéréo à **384 kbit/s, 48 kHz** |
| Format | Fichier MP4 avec `faststart` (la lecture démarre plus vite) et couleurs déclarées en **BT.709**, pour éviter le décalage de couleurs |
| Short : vertical ou carré, 3 min maximum | **9:16**, environ 35 s |

### 2. Satisfaction (système de recommandation YouTube)
| Principe | Ce que j'ai fait |
|---|---|
| Clic, puis temps de visionnage | **Accroche dans la première seconde** : un aperçu de 1,3 s de la fin (le rayon qui perce, l'explosion) avec le texte « À LA FIN... ». On sait tout de suite ce qu'on va voir |
| Tenir la promesse | L'aperçu montre exactement le moment final de la vidéo : pas de piège à clics |
| Garder l'attention | « QUI VA GAGNER ? » au début, barres de vie, K.O., rage, transformation, rayon : une question ouverte jusqu'au bout |
| Faire revenir les spectateurs | Appel à l'action à la fin : « LA SUITE ? ABONNE-TOI ↓ » |
| Partages et « j'aime » | La fin explosive pousse à commenter qui aurait dû gagner |

## Titre (à coller)
**Il se transforme en plein combat... 😳 #Shorts**

Autres choix :
- Le combat ultime de bonhommes (fin inattendue) #Shorts
- Bleu vs Rouge : qui va gagner ? ⚡ #Shorts

## Description (à coller)
```
Bleu vs Rouge : rebonds, K.O., rage et transformation... jusqu'au rayon final ⚡
Qui aurait dû gagner ? Dis-le en commentaire 👇
Abonne-toi pour la partie 2 !

Animation créée en code (Python).
Musique : [NOM DU BEAT] — prod. [NOM DU PRODUCTEUR] (beat « free for profit » : vérifie sa licence et crédite le producteur)

#Shorts #animation #stickman #combat #anime
```

## À vérifier avant de publier
- **La licence du beat.** « Free for profit » veut souvent dire « gratuit avec crédit obligatoire ». Lis les conditions du producteur et remplace les crochets ci-dessus.
- Public : « Non, ce n'est pas conçu pour les enfants » (combat stylisé).
- Ensuite, regarde dans YouTube Studio la **rétention des 3 premières secondes** et le **taux de spectateurs qui reviennent** : ce sont les meilleurs indicateurs de satisfaction disponibles.
