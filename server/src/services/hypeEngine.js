const EventEmitter = require('events');

/**
 * HypeEngine keeps a rolling window of events and computes a score based
 * on configured weights.  When the score exceeds a threshold it emits
 * a `trigger_clip` event and resets itself.
 *
 * Consumption example (in server/index.js):
 *
 *   const { HypeEngine } = require('./services');
 *   const hype = new HypeEngine({ threshold: 10 });
 *   hype.on('trigger_clip', () => io.emit('trigger_clip'));
 *
 *   // later, whenever an event arrives
 *   hype.addEvent('audio_spike');
 */
class HypeEngine extends EventEmitter {
  /**
   * @param {object} opts
   * @param {number} [opts.windowMs=10000] rolling window size in milliseconds
   * @param {number} [opts.threshold=10] score which triggers a clip
   * @param {object} [opts.weights] custom weights for types
   */
  constructor(opts = {}) {
    super();
    const {
      windowMs = 10000,
      threshold = 10,
      weights = {}
    } = opts;

    this.windowMs = windowMs;
    this.threshold = threshold;

    // default weights, can be overridden by caller
    this.weights = Object.assign(
      {
        audio_spike: 3,
        chat_spam: 2,
        keyword: 2,
        manual_trigger: 10,
        scene_change: 4
      },
      weights
    );

    // keep a simple array of {type, timestamp}
    this.events = [];
  }

  /**
   * Add an event of the given type to the engine.  If the score crosses the
   * threshold, the engine emits `trigger_clip` and resets automatically.
   * @param {string} type one of the known event types
   */
  addEvent(type) {
    if (!(type in this.weights)) {
      // ignore unknown types rather than throwing so callers don't need to
      // guard; they can still inspect the return value if desired.
      return { score: this.getScore(), triggered: false };
    }

    const now = Date.now();
    this.events.push({ type, timestamp: now });
    this._prune(now);

    const score = this.getScore();
    if (score > this.threshold) {
      this.emit('trigger_clip', { score });
      this.reset();
      return { score, triggered: true };
    }

    return { score, triggered: false };
  }

  /**
   * Compute current accumulated score over the rolling window.
   */
  getScore() {
    return this.events.reduce((acc, ev) => acc + this.weights[ev.type], 0);
  }

  /**
   * Remove events older than the window.  Caller may provide a current timestamp
   * to avoid repeated Date.now() calls.
   */
  _prune(now = Date.now()) {
    const cutoff = now - this.windowMs;
    // keep only recent events
    this.events = this.events.filter((ev) => ev.timestamp >= cutoff);
  }

  /**
   * Clear all tracked events and effectively reset the score to zero.
   */
  reset() {
    this.events.length = 0;
  }

  /**
   * Configure a new threshold value at runtime.
   * @param {number} newThreshold
   */
  setThreshold(newThreshold) {
    this.threshold = newThreshold;
  }
}

module.exports = HypeEngine;
