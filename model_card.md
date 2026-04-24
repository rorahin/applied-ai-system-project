# 🎧 Model Card: Music Recommender Simulation

## 1. Model Name  

**VibeMatch 1.0**

A weighted feature recommender that matches songs to a listener's taste profile one score at a time.

---

## 2. Intended Use  

VibeMatch 1.0 suggests songs from a small catalog that fit a listener's stated preferences for genre, mood, energy level, and acoustic texture. It is designed for classroom exploration — to show how a simple rule-based system can produce recommendations that feel personal. This is a student project, not a real product, and it is intended to be read, inspected, and questioned rather than deployed to real users.

This system should not be used to make music recommendations for actual listeners on a platform or app. It operates on 20 songs, makes no use of listening history, and cannot adapt over time. One realistic misuse case would be using this formula in a real catalog: a user whose preferred genre is underrepresented (for example, Afrobeats or bossa nova) would consistently receive irrelevant recommendations because the formula has no fallback beyond energy and acousticness proximity.

---

## 3. How the Model Works  

The system asks a listener nine questions, grouped into preferences: What is your favorite genre and mood? How energetic do you want the music, on a scale from 0 (very calm) to 1 (very intense)? Do you prefer acoustic or electronic-sounding music? How fast should the tempo be? How danceable? Do you prefer popular mainstream tracks or niche underground ones? Do you prefer instrumental or vocal-forward music? How much spoken-word content is acceptable? Every song in the catalog is graded on each of those nine dimensions. Genre and mood are pass-or-fail — a song either matches exactly and earns full credit, or earns nothing. The remaining seven features are all scored by closeness: the nearer the song is to the listener's stated preference, the higher that sub-score.

The nine sub-scores are combined into one final number using named weight sets called scoring modes. In the default mode, called BALANCED, the weights are: genre 35%, mood 25%, energy 15%, acousticness 8%, tempo 7%, danceability 4%, popularity 2%, instrumentalness 2%, and speechiness 2%. Four additional modes exist — GENRE_FIRST, MOOD_FIRST, ENERGY_FOCUSED, and DISCOVERY — each shifting weight toward a different listening context. The active mode can be switched with a single variable in the configuration file, without touching the scoring logic. Every song receives a final number, all 20 are sorted from highest to lowest, and the top five are returned. Each recommendation also comes with a plain-English explanation — for example, "genre matches your favorite (hip-hop), energy level is close to your target (0.80)" — so the listener can see exactly why a song was chosen.

---

## 4. Data  

The catalog contains 20 songs, expanded from an original 10 during the design phase to provide broader genre and mood coverage. The songs span 14 genres — including hip-hop, pop, jazz, lofi, classical, rock, electronic, synthwave, indie folk, ambient, country, r&b, and metal — and 7 moods: focused, chill, intense, relaxed, happy, moody, and melancholy. Each song has five features used in scoring: genre, mood, energy level (0 to 1), acousticness (0 to 1), and an acoustic preference flag. Features that exist in the dataset but are not used in scoring include tempo in BPM, valence, and danceability — these were tracked but left out to keep the formula simple and auditable. What is missing entirely: no lyrics, no listening history, no user-to-user similarity data, and no contextual signals like time of day or current activity.

---

## 5. Strengths  

The system works best for listeners whose preferred genre appears more than once in the catalog. For those users — hip-hop, pop, lofi, classical, and indie folk listeners — the top result is consistently strong and matches what a real person would expect. The explanation string is one of the clearest parts of the system: every recommendation comes with a sentence naming exactly which features drove the score, making the logic fully transparent and easy to question or debug. Because the formula has only four inputs and fixed weights, any result can be traced manually in under a minute, which makes this a reliable teaching tool even when it fails to produce the best possible recommendation.

---

## 6. Limitations and Bias 

The recommender assigns 40% of each song's total score to a single genre match, which creates a structural advantage for users whose preferred genre appears multiple times in the catalog — hip-hop, pop, lofi, classical, and indie folk each have two representatives, while ten other genres have only one. A user who prefers jazz will receive one genre-matched result at most, after which all remaining recommendations are drawn from cross-genre fallback scoring that the formula was not designed to optimize. The system also applies binary matching for both genre and mood, meaning an r&b song earns zero genre credit for a hip-hop listener, even though these genres share tempo patterns, production style, and cultural context that a real user might enjoy. Users with extreme energy preferences — either very low, like a classical ambient listener targeting 0.20, or very high, like a metal listener targeting 0.95 — receive fewer competitive options from the catalog's energy distribution, and the energy sub-score's 20% weight is too small to compensate meaningfully when both genre and mood also fail to match. Finally, a new user who has not yet declared a genre or mood preference loses 70% of the available scoring weight immediately, leaving the system to rank songs almost entirely by energy proximity and acousticness — a degraded mode that produces technically valid but practically meaningless recommendations without any warning to the user.

---

## 7. Evaluation  

The recommender was tested against five distinct user profiles: a late-night hip-hop worker seeking focused, high-energy tracks; a coffeehouse jazz listener preferring relaxed, acoustic-heavy music; a gym user seeking maximum-energy pop; and two adversarial profiles designed to expose scoring gaps — a moody electronic listener whose exact profile exists nowhere in the catalog, and a cold-start user with no genre or mood declared. The hip-hop and jazz profiles produced sensible rank-1 results (Bassline Therapy at 0.984 and Coffee Shop Stories at 0.989 respectively), but ranks 2–5 for both profiles quickly fell back to cross-genre songs ranked by energy and acousticness proximity rather than musical relevance, revealing how thin the catalog is beneath the top result. An unexpected pattern emerged during the moody electronic test: because no song in the catalog matches both "electronic" genre and "moody" mood simultaneously, the formula defaulted to a genre-match song with the wrong mood over a mood-match song with the wrong genre, exposing that the 0.35 genre weight in BALANCED mode will always override mood when the two signals conflict. A controlled weight shift experiment confirmed that the formula's top result is stable but that the weight distribution shapes diversity in ranks 2–5. The experiment modified the `SCORING_WEIGHTS["BALANCED"]` dictionary in `recommender.py` — the same dict consumed by the `score_song()` function — without touching any scoring logic:

Before (BALANCED default): `genre=0.35, mood=0.25, energy=0.15, acousticness=0.08, tempo=0.07, danceability=0.04, popularity=0.02, instrumentalness=0.02, speechiness=0.02`

After (experimental shift — genre reduced, energy raised): `genre=0.20, mood=0.25, energy=0.35, acousticness=0.08, tempo=0.07, danceability=0.04, popularity=0.02, instrumentalness=0.02, speechiness=0.02` (weights still sum to 1.0, remaining features unchanged)

With genre weight reduced from 0.35 to 0.20 and energy weight raised from 0.15 to 0.35, Bassline Therapy remained rank 1 for the hip-hop profile (its genre and energy both still dominated), but ranks 2–5 shifted toward high-energy songs from diverse genres rather than staying within the hip-hop cluster, demonstrating that the weight distribution matters more for lower-ranked recommendations than for the top result.

---

## 8. Future Work  

- **Balance genre representation in the catalog.** Hip-hop, lofi, classical, indie folk, and pop each have two songs in the current dataset. Jazz, country, r&b, metal, synthwave, rock, ambient, electronic, and indie pop each have only one. A jazz or country listener runs out of genre-matched material after rank 1. Adding two to three songs per single-entry genre would directly improve recommendation quality for those users without changing the formula at all.

- **Replace binary genre matching with genre-proximity scoring.** Right now a hip-hop listener earns zero genre credit for an r&b song, even though both genres share tempo patterns, production style, and cultural roots. A proximity table — where adjacent genres earn partial credit — would mean Sugar & Smoke (r&b) shows up as a partial match for a hip-hop listener rather than being treated as completely wrong. That single change would make ranks 2–5 feel much more relevant.

- **Add a collaborative filtering layer using simulated listening history.** Right now the formula has no memory. If two different users both love hip-hop and focused mood but one always skips Late Night Kings, the system cannot learn that. Even a simple simulation — grouping users by genre and mood, then surfacing songs their peers played most — would give the formula a second opinion and help surface songs that sit just below the genre-match threshold but are popular with similar listeners.

---

## 9. Personal Reflection  

The moment that stuck with me most was running the moody electronic profile. I expected the formula to find something in the middle — a song that was close on both genre and mood. Instead it picked Pulse Sequence, which matched electronic but was tagged "intense," not "moody." It made that choice confidently, with no fallback message and no hesitation. That is when I understood that the weights are not neutral — they are decisions. By setting genre to 40%, I quietly wrote a rule that says genre always wins over mood. That works well for a hip-hop listener with Bassline Therapy waiting in the catalog. It does not work for someone whose exact genre-mood combination does not exist in the data.

Using AI tools helped me move faster during setup. The scoring function and data model came together quickly because I had a solid starting point. But I had to read the output carefully every time. Early on, the tie-breaking logic was missing. Scores that were equal sorted in a different order each run. That was a small problem with a big effect on whether the output was reproducible. It reminded me that AI-generated code is a draft, not a solution.

The output surprised me. When the hip-hop profile came back with Bassline Therapy at rank 1 and a plain-English explanation — "genre matches your favorite (hip-hop), mood matches your preference (focused), energy level is close to your target" — it looked like something Spotify would actually show. The math behind that result is four multiplications and one addition. That gap between how simple the formula is and how convincing the output looks is something I keep thinking about.

If I kept building this, the first change I would make is a genre-proximity table. R&b and hip-hop should not both score zero genre credit for each other — they are too similar. After that, I would try adding a collaborative signal using simulated user histories. Something like: "other users who liked Bassline Therapy also played Late Night Kings 80% of the time." That would give the formula a second opinion on songs it almost recommended but did not.
