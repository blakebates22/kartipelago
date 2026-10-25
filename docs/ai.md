# The rivals' AI

The seven rivals drive with the same controls, kart and rules as the player: no extra
speed, no shortcuts through the physics. A good rival is fast because it drives well.

| Module                    | What it does                                                                                                                                                                  |
| ------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `src/ai/racingLine.ts`    | The racing line: the road's centre relaxed toward a smooth line inside the edges (`ai.lineMargin`), with curvature, the road's width and the room either side at every point. |
| `src/ai/driver.ts`        | Driving: where on the road to be (the plan), pure-pursuit steering, the throttle, when to drift, mistakes, getting unstuck.                                                   |
| `src/ai/items.ts`         | When to fire what it's holding, from what a player could see.                                                                                                                 |
| `src/ai/skill.ts`         | Each rival's skills, by tier, and the field's difficulty.                                                                                                                     |
| `src/ai/catchup.ts`       | The small, bounded catch-up.                                                                                                                                                  |
| `assets/data/rivals.json` | The field: each rival's tier and style; `difficulty`.                                                                                                                         |

## Skills (src/ai/skill.ts)

Every rival has a tier (strong, good, weak) and its own tendencies on top (rivals.json):
precision, vision (look-ahead), drift, tapping, boosting (zippers and blue boosts,
lifting to enhance), reaction time, aggression (passing, following, blocking), item
sense, mistakes a minute, line bias and starts. `pace` is the only direct speed knob
and stays within a percent of 1.

The field: Juniper (strong, the corner ace), Bolt, Tank, Cobble and Comet (good), Thistle
and Rook (weak). `difficulty` (-1 .. 1, Normal is -0.4) nudges every skill toward or
away from perfect, and the mistakes the other way.

**One difficulty** (Blake, Oct 24): 90s-style, no easy mode. A decent player wins a
little over half of Normal's races; a brand-new player mostly loses until they learn
the courses.

**Throttle tapping** only above Normal: a new player can't see it or learn it from the
rivals, so at Normal nobody taps.

**Every rival drives the player's kart** (Blake, Oct 24): the racer you pick never
changes the driving, so a race is won by how it's driven, not by a kart class.

## Driving (src/ai/driver.ts)

- **The plan** (a few times a second, after the rival's reaction time): its own line,
  or pulling out to pass, tucking in behind, covering the line behind it, dodging a trap,
  or lining up with a zipper pad ahead on this road (at about its height: not one on a
  road above or below).
- **Steering**: pure pursuit for a point ahead on the line; the look-ahead grows with
  speed and shrinks on a narrow road (a far point cuts corners into the walls). Off the
  road it heads back by the shortest way.
- **Speed**: it lifts or brakes when boosted faster than the road ahead allows, on a
  narrow road for a kink it can't steer round at speed, and when it's been knocked well
  off its line (a spin, a wall) so it comes round before a narrow road takes it off the
  edge.
- **Drifting**: decided once per corner, by drift skill, for corners whose shape rewards
  a drift; only from its line, pointing the right way, where the road is wide enough
  (13 m) for the slide; it lets go if thrown off the road.
- **Mistakes**: a missed drift, a wide line, a late lift, an early exit, a few times a
  minute by skill.
- **Unstuck**: barely moving, or no progress in a few seconds, and it backs out
  turning toward the road. **Lost** (under 25 m of progress in 8 s: off the road behind
  a wall, say) and it's put back at its last checkpoint (`wantsRespawn`).

## Catch-up (src/ai/catchup.ts, tuning.json ai)

Off within 50 m of the player either way. Beyond, over the next 150 m, a rival behind
gets up to 2.5% more top speed, a rival ahead up to 4.5% less. Gaps are in metres along
the race (`race.metresPerCheckpoint`; before Oct 24 they were in checkpoints and the
catch-up never switched on).

## Respawns

A fall in a course's respawn zone puts the kart past the hazard (a jump's gap). The
zone is looked up from where it fell and, if that's not in a zone (a wash well below the
road can be nearer a later stretch), from its last spot on the road
(`hazards.respawnSpot`).

## Balancing tools

- `tests/raceSim.ts`: a whole race headless (physics, items, bumps, zippers, loops,
  respawn zones), with stats per kart: place, laps, respawns and where, stuck spells,
  walls, drifting, items.
- `tools/audit/race.audit.ts`: races on a list of courses.
  `TRACKS=a,b SEEDS=10 PLAYER=novice|competent|expert OUT=x.json` and for experiments
  `RIVALS=<field.json> AI=<json of tuning.ai overrides> CLASS=<kart class> SHUFFLE=1
ITEMS=0 CATCHUP=0`.

Numbers at Normal (12 courses x 10 races, Oct 24): the competent stand-in wins 56%
(average place 2.2), the novice 2-3% (average place 4.6-4.8); Juniper and Comet lead
the field, Thistle and Rook trail.

## Still to do

- Drifting is slower than steering on the tightest corners; the drift choice could
  weigh that.
- Riverbend's water: rivals that go in recover slowly.
- The Courtyard Passage test (Dragon Isles) is skipped until the passage path is
  redrawn (it runs out over the sea).
