/**
 * next.config.js
 * expose environment variables to the client bundle.
 *
 * Vercel automatically injects process.env.* values at build time; including
 * NEXT_PUBLIC_* variables makes them available in the browser.
 */
module.exports = {
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || ''
  }
};
