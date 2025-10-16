import { spawn, spawnSync } from 'child_process';
import fs from 'fs';
import net from 'net';
import path from 'path';

let cachedParserScriptPath = null;

let pythonProcess = null;
let startupPromise = null;
let lastStartError = null;
let cleanupRegistered = false;

const defaultLogger = console;

const isLocalHost = (host) => {
  if (!host) return false;
  const normalized = host.toLowerCase();
  return normalized === 'localhost' || normalized === '127.0.0.1' || normalized === '::1';
};

const resolveParserScriptPath = () => {
  const checked = [];
  const addCandidate = (value) => {
    if (!value) return;
    const resolved = path.resolve(value);
    if (!checked.includes(resolved)) checked.push(resolved);
  };

  addCandidate(process.env.PYTHON_PARSER_SCRIPT);

  const cwd = process.cwd();
  addCandidate(path.join(cwd, '..', 'python-parser', 'app.py'));
  addCandidate(path.join(cwd, 'python-parser', 'app.py'));
  addCandidate(path.join(cwd, '..', '..', 'python-parser', 'app.py'));

  for (const candidate of checked) {
    try {
      if (fs.existsSync(candidate)) {
        return candidate;
      }
    } catch {
      // ignore fs errors, continue searching
    }
  }

  throw new Error(`Python parser entrypoint not found. Checked paths: ${checked.join(', ') || '(none)'}`);
};

const getParserScriptPath = () => {
  if (cachedParserScriptPath && fs.existsSync(cachedParserScriptPath)) {
    return cachedParserScriptPath;
  }
  cachedParserScriptPath = resolveParserScriptPath();
  return cachedParserScriptPath;
};

const log = (logger, level, message, meta) => {
  const fn = logger?.[level] || logger?.log || defaultLogger[level] || defaultLogger.log;
  if (typeof fn === 'function') {
    fn.call(logger, message, meta);
  }
};

const ensureParserScriptExists = () => {
  return getParserScriptPath();
};

const candidateExecutables = () => {
  if (process.env.PYTHON_EXECUTABLE) {
    return [{ cmd: process.env.PYTHON_EXECUTABLE, args: [] }];
  }
  if (process.platform === 'win32') {
    return [
      { cmd: 'python', args: [] },
      { cmd: 'python3', args: [] },
      { cmd: 'py', args: ['-3'] },
      { cmd: 'py', args: [] },
    ];
  }
  return [
    { cmd: 'python3', args: [] },
    { cmd: 'python', args: [] },
  ];
};

const findPythonExecutable = (logger) => {
  const candidates = candidateExecutables();
  for (const candidate of candidates) {
    try {
      const result = spawnSync(candidate.cmd, [...candidate.args, '--version'], { stdio: 'ignore' });
      if (!result.error && result.status === 0) {
        return candidate;
      }
    } catch {
      // Try next candidate
    }
  }
  throw new Error('No Python executable found. Set PYTHON_EXECUTABLE environment variable to the Python interpreter path.');
};

const registerCleanup = () => {
  if (cleanupRegistered) return;
  cleanupRegistered = true;
  const cleanup = () => {
    if (pythonProcess) {
      try {
        pythonProcess.kill();
      } catch {
        // ignore cleanup errors
      }
      pythonProcess = null;
    }
  };
  process.on('exit', cleanup);
  process.on('SIGINT', cleanup);
  process.on('SIGTERM', cleanup);
};

const startPythonProcess = (logger) => {
  const scriptPath = ensureParserScriptExists();
  const executable = findPythonExecutable(logger);
  const args = [...executable.args, scriptPath];

  log(logger, 'info', 'Attempting to start local python-parser service', { executable: executable.cmd, args: executable.args });

  pythonProcess = spawn(executable.cmd, args, {
    cwd: path.dirname(scriptPath),
    env: {
      ...process.env,
      PYTHONUNBUFFERED: '1',
    },
    stdio: ['ignore', 'pipe', 'pipe'],
  });

  registerCleanup();

  return new Promise((resolve, reject) => {
    let resolved = false;
    const onError = (error) => {
      if (pythonProcess) {
        pythonProcess.removeListener('exit', onExit);
      }
      pythonProcess = null;
      if (!resolved) {
        reject(error);
      } else {
        log(logger, 'warn', 'python-parser process emitted error after start', { error: error?.message });
      }
    };

    const onExit = (code, signal) => {
      pythonProcess = null;
      const meta = { code, signal };
      if (!resolved) {
        reject(new Error(`python-parser exited before it became ready (code=${code}, signal=${signal})`));
      } else if (code !== 0) {
        log(logger, 'warn', 'python-parser process exited unexpectedly', meta);
      } else {
        log(logger, 'info', 'python-parser process exited cleanly', meta);
      }
    };

    pythonProcess.once('error', onError);
    pythonProcess.once('exit', onExit);
    pythonProcess.stdout?.on('data', (chunk) => {
      const text = chunk.toString().trim();
      if (text) log(logger, 'debug', '[python-parser] stdout', { text });
    });
    pythonProcess.stderr?.on('data', (chunk) => {
      const text = chunk.toString().trim();
      if (text) log(logger, 'warn', '[python-parser] stderr', { text });
    });
    pythonProcess.once('spawn', () => {
      resolved = true;
      log(logger, 'info', 'python-parser process started', { pid: pythonProcess?.pid, executable: executable.cmd });
      resolve();
    });
  });
};

const waitForPort = (host, port, timeoutMs = 5000) => new Promise((resolve, reject) => {
  const start = Date.now();
  const attempt = () => {
    const socket = net.connect({ host, port }, () => {
      socket.destroy();
      resolve();
    });
    socket.once('error', (err) => {
      socket.destroy();
      if (Date.now() - start >= timeoutMs) {
        reject(err);
      } else {
        setTimeout(attempt, 150);
      }
    });
  };
  attempt();
});

export const ensurePythonParserAvailable = async ({
  pythonUrl,
  logger = defaultLogger,
  timeoutMs = 750,
  allowAutoStart = false,
  autoStartTimeoutMs = 5000,
} = {}) => {
  if (!pythonUrl) throw new Error('pythonUrl is required');
  const url = new URL(pythonUrl);
  const host = url.hostname || 'localhost';
  const port = Number(url.port || (url.protocol === 'https:' ? 443 : 80));

  try {
    await waitForPort(host, port, timeoutMs);
    lastStartError = null;
    return { status: 'available', autoStarted: false };
  } catch (initialError) {
    if (!allowAutoStart || !isLocalHost(host)) {
      lastStartError = initialError;
      throw initialError;
    }
  }

  if (lastStartError) {
    throw lastStartError;
  }

  if (!startupPromise) {
    startupPromise = startPythonProcess(logger)
      .catch((err) => {
        lastStartError = err;
        throw err;
      })
      .finally(() => {
        startupPromise = null;
      });
  }

  await startupPromise;

  try {
    await waitForPort(host, port, autoStartTimeoutMs);
    lastStartError = null;
    return { status: 'available', autoStarted: true };
  } catch (err) {
    lastStartError = err;
    throw err;
  }
};

export const stopPythonParser = () => {
  if (pythonProcess) {
    try {
      pythonProcess.kill();
    } catch {
      // ignore
    }
    pythonProcess = null;
  }
  lastStartError = null;
};
