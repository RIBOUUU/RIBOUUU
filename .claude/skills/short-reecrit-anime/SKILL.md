---
name: short-reecrit-anime
description: Transformer une vidéo courte (TikTok/Short/Reel) envoyée par l'utilisateur en un Short original pour sa chaîne. Transcription, réécriture plus choc en argot de jeunes (en gardant les 5 premières secondes), voix off ElevenLabs, animation verticale dans son style sombre avec la mise en scène de la vidéo de référence, assemblage, puis miniature dessinée en code sans crédits. À utiliser quand l'utilisateur envoie une vidéo et demande de la transcrire, de la reformuler, d'en faire un Short animé ou une miniature de Short.
---

# Short réécrit et animé (style de la chaîne Sorido)

Ce skill reprend exactement le processus validé par l'utilisateur. Tout se fait **en français**, pour une audience **France**. On demande l'avis de l'utilisateur à chaque étape et on n'enchaîne pas sans son accord.

## Règles générales (à respecter tout le temps)

- **Économiser les crédits ElevenLabs.** L'utilisateur a dit « pas autant ». Seules dépenses normales : la voix off (≈ 1 crédit par caractère, ≈ 1 300 pour un Short) et le montage dans le bac à sable (quelques centaines). La transcription (scribe) est gratuite. **Jamais de génération d'image payante sans demande explicite** : miniatures et visuels sont dessinés en code, donc gratuits. Avant toute dépense de plus de 500 crédits, faire un `estimate_only` et demander.
- **Pas de copie de la vidéo source** : on garde la structure, pas les dessins ni les engagements personnels de l'autre créateur (par exemple ses appels aux dons). On les remplace par un simple « Abonne-toi ».
- Personnages **originaux** (style de l'utilisateur), jamais la mascotte d'une autre chaîne.
- À chaque livrable : envoyer le fichier avec `SendUserFile`, faire un commit sur la branche de travail et un push.

## Étape 1 — Transcrire la vidéo envoyée

1. Inspecter le fichier : `ffprobe` (durée, format ; un Short est en général en 576×1024 ou 1080×1920).
2. Essayer `pip install faster-whisper` puis le modèle `small` en `language='fr'`. **Le téléchargement du modèle depuis HuggingFace est bloqué par le proxy** : si ça échoue, ne pas insister.
3. **Solution de repli éprouvée** : lire les sous-titres incrustés image par image.
   ```bash
   ffmpeg -i VIDEO -vf "fps=3,crop=576:240:0:590,scale=360:-1,drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf:text='%{pts\:hms}':x=4:y=4:fontsize=14:fontcolor=white:box=1:boxcolor=black,tile=4x13" c_%02d.png
   ```
   Ajuster `crop` sur la zone des sous-titres. Lire chaque planche avec Read, puis reconstruire le texte avec ses minutages.
4. Rendre la transcription propre, par blocs `[m:ss]`, et noter à part les textes affichés à l'écran (gros titres, bulles).
5. Signaler les passages incertains et préciser que la transcription vient des sous-titres. Rappeler que le dépôt GitHub est public si on y enregistre le texte d'un autre créateur.

## Étape 2 — Réécrire en plus choc, avec l'argot des jeunes

- **Garder mot pour mot les 5 premières secondes** du texte d'origine (l'accroche), puis enchaîner.
- Ton : **choc et émotion**. Contrastes brutaux, phrases courtes, tutoiement, questions qui piquent l'ego (« Tu crois que… ? »).
- **Argot et expressions de jeunes** : daronne / daron, frère / frérot, t'es en mode, tqt / t'inquiète, t'as le seum, genre, c'est abusé, tu fais le chaud, tu la ghostes, vu pas répondu, en sprint, claquettes, zéro bruit, tu fais l'avocat, en vrai, saouler.
- Structure qui a marché :
  1. l'accroche d'origine (5 s) ;
  2. 3 ou 4 contrastes concrets du quotidien ;
  3. un **« Abonne-toi, parce que la suite elle va piquer »** vers 20-25 s ;
  4. le retournement émotionnel (« en vrai, frère… pourquoi tu fais ça ? ») ;
  5. une fin qui fait mal (« un jour ton tel va plus sonner… ») ;
  6. un dernier ordre en un mot (« décroche, frère »).
- Longueur : 190-240 mots, soit 60-75 s. Proposer une coupe pour tenir en 60 s.
- Ne pas présenter une formule comme une vraie statistique (par exemple « 99 % ») sans le signaler.
- Livrer le texte, les **textes à l'écran** proposés et la durée estimée, puis demander validation.

## Étape 3 — Voix off (ElevenLabs)

- Voix validée : **« Hugo – Punchy French Creator »**, `voice_id 3Tp5mYhT9wrfnry9pzvV`, modèle `eleven_v4`, **`generations_count: 1`**, en mettant le script dans un flow (`creative_create_flow` ou le flow existant).
- Écrire les nombres en lettres (« quinze ») et les abréviations en entier (« t'inquiète »).
- Enregistrer le script dans `<projet>/script.txt`.
- Transcrire ensuite la voix générée avec `creative_transcribe_audio` (`eleven_scribe_v1`, gratuit), puis recopier les mots avec leur début dans `<projet>/words.txt`, une ligne `mot début_en_s` par mot.

## Étape 4 — Animation verticale (style de l'utilisateur + mise en scène de la référence)

**Étudier la vidéo de référence image par image** avant d'animer :
```bash
ffmpeg -i VIDEO -vf "fps=1,scale=216:-1,drawtext=...:text='%{pts\:hms}',tile=8x4" f_%02d.png
```
Relever, pour chaque phrase, quel plan est utilisé, où sont placés les personnages et où sont les textes.

**Règles de mise en scène** (tirées de la référence) :
- **Plan à deux** : parent à gauche (x≈280) avec une étiquette « DARONNE » rose ou « DARON » bleue au-dessus de la tête, le fils à droite (x≈800), sol visible, bulle au-dessus de celui qui parle.
- **Gros plan** : un personnage centré et coupé à la taille, la tête vers 55-60 % de la hauteur, avec un **gros mot-titre en haut** (« T'ES EN MODE : », « *SOUPIR* », « EN SPRINT », « DIRECT ! », « L'AVOCAT », « TOUT SAGE »).
- **Écrans de téléphone** pour les appels (« 15 appels manqués » avec une croix rouge, « 1 appel entrant » avec une coche verte) et pour les messages (« T'as mangé ? »).
- **Fond rouge à rayons** quand quelqu'un s'énerve. Fond nuit étoilé pour les moments tristes.
- **Un nouveau plan toutes les 1 à 3 s** (environ 24 plans pour 67 s).
- Légendes au mot près, en majuscules, Inter Black avec contour noir, **mots d'argot et mots clés en jaune**, placées vers y=1330.

**Style de l'utilisateur** (celui de la vidéo longue) : fond sombre bleu-pétrole, rose, violet ou nuit avec de grands cercles doux, grain et vignettage, personnages vectoriels à **tête noire ronde et grands yeux blancs** :
- le fils : sweat orange à capuche (`SON`) ;
- la daronne : cheveux longs bruns, boucles d'oreilles, haut rose (`MOM`) ;
- le daron : cheveux courts, moustache, chemise bleue (`DAD`).

**Code à réutiliser** (ne pas repartir de zéro) :
- `video_superpouvoirs/anim/engine.py` : moteur (personnages, poses, expressions, bulles, étiquettes, légendes, finition).
- `short_daronne/short.py` : **modèle complet du Short**. Copier ce fichier, puis remplacer la liste `PLANS` (début de plan, fonction, couleur de fond, sol visible) et les fonctions de plan `pXX`.
- Commandes :
  - `python3 short.py sheet 1.5,4,7,…  sortie.png` : planche de contrôle à faire **avant** le rendu complet. La lire et corriger les chevauchements de textes, les personnages hors cadre et les glyphes manquants (dessiner les croix avec des traits, pas avec « ✕ »).
  - `python3 short.py full` : rendu 1080×1920 à 30 i/s, sans son, dans `out/<nom>_muet.mp4` (environ 1 minute pour 67 s).

## Étape 5 — Assemblage avec la voix

L'environnement ne peut pas télécharger les fichiers d'ElevenLabs (`elevenlabsusercontent.com` est bloqué), donc on passe par GitHub :
1. Commit et push de la vidéo muette sur la branche (le dépôt est public). Récupérer le hash du commit.
2. `creative_attach_reference_file` avec `https://raw.githubusercontent.com/RIBOUUU/RIBOUUU/<commit>/<chemin>.mp4`.
3. `creative_execute_sandbox` avec comme entrées le nœud vidéo et l'`generation_id` de la voix :
   ```bash
   ffmpeg -i in/v.mp4 -i in/voix.mp3 -filter_complex "[1:a]loudnorm=I=-14:TP=-1.5:LRA=11,apad[a]" -map 0:v -map "[a]" -c:v copy -c:a aac -b:a 192k -shortest -movflags +faststart "$OUT/<nom>.mp4"
   ```
   Le bac à sable coupe chaque commande à 180 s et un appel d'outil expire à 60 s : utiliser `wait_seconds` 55 puis `creative_get_sandbox_run`.
4. Donner le **lien complet** du nœud, avec `?mode=switchWorkspace&oobCode=…&node=<id>`, sinon le site affiche « Flux introuvable ». Conseiller de l'ouvrir dans Chrome ou sur ordinateur.
5. Envoyer aussi l'aperçu muet avec `SendUserFile` pour que l'utilisateur voie l'animation tout de suite.

## Étape 6 — Miniature du Short (gratuite)

- Format **vertical 1080×1920**, dessinée avec le moteur, donc **0 crédit**.
- **Titre = la question d'accroche** de la vidéo, en très gros en haut sur 3 lignes (Inter Black, contour noir de 12 px, le mot clé en jaune). Exemple : « POURQUOI TU / PARLES MAL / À TA MÈRE ? ».
- Sous le titre : la scène qui résume le conflit (par exemple la daronne qui pleure avec son téléphone et une bulle rouge « 15 APPELS », le fils tranquille à côté), fond rose sombre avec un halo.
- Lire le rendu, vérifier qu'aucun élément ne se chevauche, puis l'envoyer.

## Étape 7 — Fin

- Récapituler les crédits dépensés avec `account_get_usage` : comparer avant et après, et détailler poste par poste.
- **Publication YouTube** : vidIQ (chaîne « Sorido », `UCCy5qYisFirS5U5xBXOeqIA`) peut publier, mais il lui faut un lien public vers le fichier final. Ce lien n'est disponible que si l'utilisateur autorise `elevenlabsusercontent.com` dans l'environnement. **Cette autorisation ne peut pas être validée depuis l'application mobile** : lui demander de le faire sur claude.ai depuis un ordinateur, ou dans les réglages de l'environnement (Accès réseau, domaines autorisés).
- Proposer ensuite des titres de Short qui piquent la curiosité et touchent l'ego.
