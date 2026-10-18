/** Every balloon and weapon setting (assets/data/tuning.json, "items"). */
export interface ItemsConfig {
  /** Blue balloon boost timers per level, seconds (from the original's timer values). */
  blue1Sec: number;
  blue2Sec: number;
  blue3Sec: number;
  /** Timer multiplier when activated with the throttle released (1 = same timer). */
  blueEnhancedScale: number;
  /** Level 3's sound charges for this long before its boost sound (physics starts at once). */
  blue3ChargeSec: number;
  redL3Ammo: number;

  /** Missile speed added to the kart's own velocity, m/s, and how much of that is kept. */
  missileSpeed: number;
  missileCarry: number;
  missileLife: number;
  missileHitRadius: number;
  /** Homing: how far ahead it looks for a target, its turn rate (rad/s), the distance
   * under which it aims straight at the target, and how far ahead along the track it
   * aims otherwise. */
  homingRange: number;
  homingTurn: number;
  homingDirect: number;
  homingLookAhead: number;
  missileSpinSec: number;
  missileSpeedKeep: number;
  /** Upward kick from a missile hit, m/s. */
  missilePop: number;

  oilRadius: number;
  oilSpinSec: number;
  oilSpeedKeep: number;
  mineRadius: number;
  mineSpinSec: number;
  mineSpeedKeep: number;
  minePop: number;
  bubbleRadius: number;
  /** How long a bubble holds a racer, s. */
  bubbleSec: number;
  /** Traps are dropped this far behind the kart, m. */
  trapBehind: number;
  /** The racer who dropped a trap can't set it off for this long, s. */
  trapOwnerGrace: number;
  trapLife: number;

  shield1Sec: number;
  shield2Sec: number;
  shield3Sec: number;
  /** How much heavier a shielded kart is when bumping (others get pushed, it doesn't). */
  shieldMass: number;

  /** Metres per original game unit, for the magnet ranges (a guess; tune it). */
  magnetUnit: number;
  /** Magnet targeting ranges in original game units. */
  magnet1Range: number;
  magnet2Range: number;
  magnet3Range: number;
  magnetSec: number;
  /** How fast a magnet turns you toward the target (rad/s) and the speed it pulls you
   * to (multiple of top speed) at magnetAccel m/s². It lets go within magnetReach m. */
  magnetTurn: number;
  magnetSpeedMult: number;
  magnetAccel: number;
  magnetReach: number;
  /** Reverse magnet: how long it holds the rival, how fast it drags them to you (m/s),
   * and how hard it brakes them (m/s²). */
  reverseMagnetSec: number;
  reversePull: number;
  reverseDecel: number;

  /** After a hit, a racer can't be hit again for this long, s. */
  hitImmuneSec: number;
  balloonRadius: number;
  balloonRespawnSec: number;
  /** Whether AI rivals pick up balloons (they don't use them yet). */
  aiCollect: boolean;
  volume: number;
}
