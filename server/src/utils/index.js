// simple logger helpers used throughout the server
// in production we suppress most of the console spam, but warnings
// and errors still print so that alerts/monitoring can pick them up.

const isProd = process.env.NODE_ENV === 'production';

function log(...args) {
    if (!isProd) console.log(...args);
}

function debug(...args) {
    if (!isProd) console.debug(...args);
}

function warn(...args) {
    console.warn(...args);
}

function error(...args) {
    console.error(...args);
}

module.exports = {
    log,
    debug,
    warn,
    error
};
