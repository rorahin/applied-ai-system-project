# Reflection: Music Recommender Simulation

## Profile Comparisons

### Profile A vs. Profile B — Hip-Hop Worker vs. Jazz Listener

Both profiles produced a clear, strong rank-1 result — Bassline Therapy for the hip-hop listener and Coffee Shop Stories for the jazz listener. However, what followed was very different. The hip-hop listener's rank 2 was still a hip-hop song (Late Night Kings), giving them two genuinely relevant results before the catalog ran out. The jazz listener had only one jazz song in the entire catalog, so ranks 2–5 immediately crossed into other genres. The songs that filled those spots — lofi and classical tracks — shared the low-energy, acoustic quality of jazz but not the genre itself.

This comparison shows that the formula rewards catalog depth: a user whose genre is more represented in the dataset consistently gets a stronger recommendation set, not because the algorithm is smarter for them, but because it has more raw material to work with.

---

### Profile A vs. Profile C — Hip-Hop Worker vs. Gym Pop Listener

Both users prefer low-acoustic, high-energy music, but their mood and genre preferences differ significantly. Gym Hero scored nearly a perfect 0.995 for the pop/intense profile — higher than Bassline Therapy's 0.984 — because its energy was an exact match to the target (0.93) and its acousticness was almost zero (0.05). The hip-hop worker's rank 2–5 and the pop gym listener's rank 2–5 will actually overlap heavily, because once the genre-matched songs are exhausted, both profiles fall back to the same pool of high-energy, low-acoustic songs.

This convergence in lower ranks is a sign that the catalog's high-energy cluster (Storm Runner, Pulse Sequence, Weight of Silence) ends up serving very different users almost identically. Two users with opposite genre preferences end up getting the same songs recommended in positions 3–5 because energy and acousticness, not genre, become the deciding factors once genre matches run out.

---

### Profile B vs. Adversarial Profile 1 — Jazz Listener vs. Moody Electronic User

The jazz listener's experience was frustrating but understandable: one strong match followed by acoustic-flavored fallback. The moody electronic user's experience was more structurally broken. Not only did no song match both their genre and mood, but the formula chose between two imperfect options in a way that may feel wrong: it prioritized the correct-genre, wrong-mood song (Pulse Sequence/intense) over the correct-mood, wrong-genre song (Night Drive Loop/synthwave). This happened because genre weight (0.40) exceeds mood weight (0.30).

A real user asking for "moody electronic" might care more about getting the mood right than the genre right — especially since synthwave and electronic are culturally adjacent — but the formula has no way to express that nuance. This comparison surfaces a genuine tension: the weight hierarchy embeds a value judgment (genre matters more than mood) that may not apply to all users equally.

---

### Design Tradeoff — High Energy vs. Cold Start

The gym listener (pop/intense, energy 0.93) and the cold-start adversarial user (no genre, no mood, energy 0.50) represent an interesting tension in the design. The gym listener gets an almost-perfect top result because all four sub-scores fire or nearly fire. The cold-start user, despite having a perfectly valid mid-range energy preference, receives a rank-1 result that has nothing to do with their musical identity — because with genre and mood scoring at zero, the only differentiator is a 0.20 weight on energy and a 0.10 weight on acousticness.

This reveals a core design assumption: the formula is built for users who know and declare their preferences. It degrades gracefully in the mathematical sense (the output is always a valid ranked list) but not in the experiential sense (the list is not meaningful). The gym user's near-perfect score and the cold-start user's essentially random output both come from the same formula — the difference is entirely in how much information the user provided upfront.

---

## Plain-Language Summary

The recommender works like a checklist with different point values: matching your favorite genre earns the most points (40 out of 100), matching your preferred mood earns 30 points, being close to your target energy level earns up to 20 points, and having the right acoustic texture earns up to 10 points. Every song in the catalog gets scored on that checklist and the one with the highest total wins.

The problem is that the checklist is rigid. If your favorite genre is jazz and only one jazz song exists in the catalog, that one song gets the genre bonus. Everything after rank 1 is filled by whoever scores highest on mood, energy, and texture — regardless of whether you would enjoy them. Here is a real example from the data: a pop listener gets Gym Hero at rank 1. But if they keep scrolling, they might see Weight of Silence, a metal track, sitting at rank 3 or 4. That happens because Weight of Silence's energy (0.96) is close enough to a high-energy pop listener's target that it outscores more musically related options. The formula has no concept of which genres sound alike. It treats every non-matching genre as equally wrong and fills the gaps using energy, the only feature that is measured on a continuous scale.

---

## What I Learned

Building this recommender made it clear that the hard part of recommendation systems is not the math. It is the design choices that the math enforces without anyone noticing. Choosing to weight genre at 40% feels intuitive. But it silently decides that a jazz listener — with only Coffee Shop Stories in the entire catalog — will always get a weaker result set than a hip-hop listener who has Bassline Therapy and Late Night Kings both available. That is not a neutral technical choice. It is a judgment about which users matter more. Real systems like Spotify invest enormous effort in this exact problem — making sure that niche-taste users are not structurally penalized just because the catalog skews toward popular genres.

---

## Personal Reflection

I did not expect the hardest part of this project to be picking a number. But choosing 0.40 for genre weight took longer than writing most of the code. Every weight I considered felt like a statement: "this matters more than that." Once I committed to genre at 40%, the system's behavior in the moody electronic test was not a surprise — it was a logical consequence. Pulse Sequence won that slot because I had already decided, at design time, that genre beats mood. I just had not thought about what that meant for a user whose exact genre-mood combination was not in the catalog.

The AI tool helped me move faster but not without friction. The first version of the scoring function worked fine on typical inputs. It fell apart on edge cases. Scores that were identical sorted differently on each run because tie-breaking was not implemented. That is the kind of problem that does not show up until you actually test with real data. Running the five user profiles against the finished code was what made the edge cases visible — not reading the code, but running it.

What I keep coming back to is how convincing the output looked for the hip-hop profile. Bassline Therapy at rank 1, score 0.984, with "genre matches your favorite (hip-hop), mood matches your preference (focused)" printed right below it. That looks like a real product. But behind that output is a formula that does not know what hip-hop sounds like. It just knows that the genre field says "hip-hop" and the target field says "hip-hop" and those two strings match. The explainability layer is what makes it feel intelligent. Without it, you would just see a sorted list of numbers.

The next version of this would start with one change: a genre-proximity table. R&b and hip-hop scoring zero genre credit for each other is the biggest single failure in the current formula. After that, I would want to test what happens when you run many different user profiles and aggregate the results — not to improve any one recommendation, but to see which songs keep showing up in the wrong places and why.
