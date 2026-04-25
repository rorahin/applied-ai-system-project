# Music Knowledge Base

This document provides domain knowledge used by the RAG retrieval layer to
improve music recommendation interpretation beyond what the keyword parser
can extract directly. The knowledge retrieval module loads this file, matches
entries against a user request by keyword, and augments the parsed preference
profile with dimensions the parser could not infer on its own.

Each entry includes trigger keywords, suggested musical attributes (energy,
mood, decade), and a plain-language note explaining the mapping rationale.

---

## Entries

### workout
- **keywords**: workout, gym, exercise, training, pump up, sweat, lifting, gains
- **energy**: 0.90
- **mood**: intense
- **decade**:
- **note**: High-energy, intense songs are ideal for workout sessions. Target energy above 0.85 with an aggressive or intense mood.

### focus
- **keywords**: focus, study, studying, concentrate, concentration, work session, deep work, coding
- **energy**: 0.45
- **mood**: focused
- **decade**:
- **note**: Low-to-medium energy, focused mood songs support deep work and study. Avoid high-energy or emotionally distracting tracks.

### party
- **keywords**: party, dance, dancing, club, celebration, celebrate, pregame, banger
- **energy**: 0.85
- **mood**: happy
- **decade**:
- **note**: Upbeat, high-energy happy songs work well for parties. Prioritize danceability and a positive mood.

### sleep
- **keywords**: sleep, sleeping, bedtime, lullaby, wind down, rest, insomnia, falling asleep
- **energy**: 0.20
- **mood**: chill
- **decade**:
- **note**: Very low energy calm or ambient music aids sleep and relaxation. Avoid upbeat or intense tracks.

### nostalgic
- **keywords**: nostalgic, throwback, memories, childhood, remember, reminisce, old days
- **energy**:
- **mood**: moody
- **decade**: 1990s
- **note**: Nostalgic requests often reference older decades and reflective or moody emotional tones.

### road trip
- **keywords**: road trip, drive, driving, highway, travel, commute, long drive, road
- **energy**: 0.70
- **mood**: happy
- **decade**:
- **note**: Medium-high energy, upbeat songs are popular for road trips and long drives.

### meditation
- **keywords**: meditation, meditate, mindfulness, zen, peaceful, calm down, breathing, relax
- **energy**: 0.20
- **mood**: chill
- **decade**:
- **note**: Very low energy ambient or classical-leaning music suits meditation and mindfulness practice.

### morning
- **keywords**: morning, wake up, sunrise, breakfast, start the day, morning routine, alarm
- **energy**: 0.65
- **mood**: happy
- **decade**:
- **note**: Upbeat, moderately energetic happy songs are a good fit for morning routines and starting the day.
