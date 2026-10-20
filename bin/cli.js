#!/usr/bin/env node
'use strict';

const fs = require('fs');
const os = require('os');
const path = require('path');
const crypto = require('crypto');

const PKG_ROOT = path.resolve(__dirname, '..');
const PKG = require(path.join(PKG_ROOT, 'package.json'));
const SKILLS_SRC = path.join(PKG_ROOT, 'skills');
const MARKER = '.ai-workflow-suite';

// Skills roots used by each agent tool. A target is "detected" when the tool's
// config dir exists; the skills subdir is created on install.
const TARGETS = [
  { id: 'claude', label: 'Claude Code', base: '.claude', skills: path.join('.claude', 'skills') },
  { id: 'codex', label: 'Codex CLI', base: '.codex', skills: path.join('.codex', 'skills') },
  { id: 'omp', label: 'omp', base: '.omp', skills: path.join('.omp', 'agent', 'skills') },
  { id: 'agents', label: 'Universal (~/.agents)', base: '.agents', skills: path.join('.agents', 'skills') },
  { id: 'qoder', label: 'Qoder', base: '.qoder-cn', skills: path.join('.qoder-cn', 'skills') },
];

const ALIASES = {
  claude: 'claude', 'claude-code': 'claude', claudecode: 'claude', cc: 'claude',
  codex: 'codex', 'codex-cli': 'codex',
  omp: 'omp',
  agents: 'agents', universal: 'agents',
  qoder: 'qoder',
};

function home() {
  return os.homedir();
}

function targetRoot(t) {
  return path.join(home(), t.skills);
}

function detected(t) {
  return fs.existsSync(path.join(home(), t.base));
}

// ---------------- source skills ----------------

function listSourceSkills() {
  if (!fs.existsSync(SKILLS_SRC)) {
    die(`Bundled skills are missing at ${SKILLS_SRC}. The package looks corrupted - reinstall it.`);
  }
  return fs
    .readdirSync(SKILLS_SRC, { withFileTypes: true })
    .filter((e) => e.isDirectory())
    .map((e) => e.name)
    .filter((n) => fs.existsSync(path.join(SKILLS_SRC, n, 'SKILL.md')))
    .sort();
}

function walkFiles(dir, base) {
  base = base || dir;
  const out = [];
  for (const entry of fs.readdirSync(dir, { withFileTypes: true }).sort((a, b) => (a.name < b.name ? -1 : 1))) {
    if (entry.name === MARKER || entry.name.startsWith('._') || entry.name === '.DS_Store') continue;
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) out.push(...walkFiles(full, base));
    else if (entry.isFile()) out.push(path.relative(base, full));
  }
  return out;
}

function treeFingerprint(dir) {
  const files = walkFiles(dir);
  const h = crypto.createHash('sha256');
  for (const rel of files) {
    h.update(rel.replace(/\\/g, '/'));
    h.update('\0');
    h.update(fs.readFileSync(path.join(dir, rel)));
    h.update('\0');
  }
  return h.digest('hex');
}

// ---------------- fs helpers ----------------

function copyTree(src, dest) {
  fs.mkdirSync(dest, { recursive: true });
  for (const rel of walkFiles(src)) {
    const from = path.join(src, rel);
    const to = path.join(dest, rel);
    fs.mkdirSync(path.dirname(to), { recursive: true });
    fs.copyFileSync(from, to);
    try {
      fs.chmodSync(to, 0o755);
    } catch (_) {
      /* Windows / restricted fs: exec bit is not meaningful there */
    }
  }
}

function removeTree(dir) {
  fs.rmSync(dir, { recursive: true, force: true });
}

function installedSkillsAt(skillsRoot) {
  if (!fs.existsSync(skillsRoot)) return [];
  return fs
    .readdirSync(skillsRoot, { withFileTypes: true })
    .filter((e) => e.isDirectory() && /^ai-workflow/.test(e.name))
    .map((e) => {
      const full = path.join(skillsRoot, e.name);
      const marker = path.join(full, MARKER);
      let meta = null;
      if (fs.existsSync(marker)) {
        try {
          meta = JSON.parse(fs.readFileSync(marker, 'utf8'));
        } catch (_) {
          meta = {};
        }
      }
      return { name: e.name, dir: full, managed: Boolean(meta), meta: meta || {} };
    });
}

// ---------------- output ----------------

const USE_COLOR = !process.env.NO_COLOR && process.stdout.isTTY;
const c = (code, s) => (USE_COLOR ? `\x1b[${code}m${s}\x1b[0m` : s);
const green = (s) => c('32', s);
const dim = (s) => c('2', s);
const bold = (s) => c('1', s);
const yellow = (s) => c('33', s);
const red = (s) => c('31', s);

function die(msg) {
  process.stderr.write(`${red('✗')} ${msg}\n`);
  process.exit(1);
}

// ---------------- commands ----------------

function resolveTargets(specified) {
  if (specified.includes('all')) return TARGETS.filter(detected);
  if (specified.length) {
    const picked = [];
    for (const raw of specified) {
      const id = ALIASES[String(raw).toLowerCase()];
      if (!id) die(`Unknown target "${raw}". Known: ${TARGETS.map((t) => t.id).join(', ')}, all`);
      const t = TARGETS.find((x) => x.id === id);
      if (!picked.includes(t)) picked.push(t);
    }
    return picked;
  }
  const found = TARGETS.filter(detected);
  if (!found.length) {
    die(
      `No supported agent tool detected in ${home()}.\n` +
        `Pass a target explicitly, e.g. \`${PKG.name} claude\`, or --dir <skills path>.`
    );
  }
  return found;
}

function install(target, opts) {
  const skills = listSourceSkills();
  const skillsRoot = opts.dir ? path.resolve(opts.dir) : targetRoot(target);
  const label = opts.dir ? 'Custom' : target.label;
  fs.mkdirSync(skillsRoot, { recursive: true });

  const existing = new Map(installedSkillsAt(skillsRoot).map((s) => [s.name, s]));
  const report = { target: target ? target.id : 'custom', root: skillsRoot, added: [], updated: [], unchanged: [], skipped: [] };

  const srcFp = treeFingerprint(SKILLS_SRC);

  for (const name of skills) {
    const src = path.join(SKILLS_SRC, name);
    const dest = path.join(skillsRoot, name);
    const prior = existing.get(name);

    if (prior && prior.meta.fingerprint && prior.meta.fingerprint === srcFp && !opts.force) {
      report.unchanged.push(name);
      continue;
    }
    if (prior && !prior.managed && !opts.force) {
      report.skipped.push({ name, reason: 'a directory with this name exists but was not installed by this tool' });
      continue;
    }
    copyTree(src, dest);
    fs.writeFileSync(
      path.join(dest, MARKER),
      JSON.stringify({ name, version: PKG.version, fingerprint: srcFp, installedAt: new Date().toISOString() }, null, 2) + '\n'
    );
    if (prior) report.updated.push(name);
    else report.added.push(name);
  }

  printInstall(report, label);
  return report;
}

function printInstall(report, label) {
  process.stdout.write(`${bold(label)} ${dim(report.root)}\n`);
  const line = (kind, names, color) => {
    if (!names.length) return;
    process.stdout.write(`  ${color(kind)} ${names.map((n) => `${green('✓')} ${n}`).join(', ')}\n`);
  };
  line('installed', report.added, green);
  line('updated  ', report.updated, yellow);
  line('unchanged', report.unchanged, dim);
  for (const s of report.skipped) {
    process.stdout.write(`  ${red('skipped')} ${s.name} - ${s.reason} (use --force to overwrite)\n`);
  }
}

function uninstall(target, opts) {
  const skillsRoot = opts.dir ? path.resolve(opts.dir) : targetRoot(target);
  const label = opts.dir ? 'Custom' : target.label;
  const found = installedSkillsAt(skillsRoot).filter((s) => s.managed);
  process.stdout.write(`${bold(label)} ${dim(skillsRoot)}\n`);
  if (!found.length) {
    process.stdout.write(`  ${dim('nothing to remove')}\n`);
    return;
  }
  for (const s of found) {
    removeTree(s.dir);
    process.stdout.write(`  ${red('removed ')} ${s.name}\n`);
  }
}

function list() {
  const skills = listSourceSkills();
  process.stdout.write(`${bold(PKG.name)} v${PKG.version} - ${skills.length} skills\n`);
  process.stdout.write(`  ${skills.join(', ')}\n\n`);
  process.stdout.write(`${bold('Targets')}\n`);
  for (const t of TARGETS) {
    const root = targetRoot(t);
    const here = detected(t);
    const inst = installedSkillsAt(root).filter((s) => s.managed);
    const state = !here ? dim('not detected') : inst.length ? green(`v${inst[0].meta.version || '?'}`) : dim('none installed');
    process.stdout.write(`  ${t.id.padEnd(8)} ${state}  ${dim(root)}\n`);
  }
}

function pythonHint() {
  const bins = process.platform === 'win32' ? ['python', 'py', 'python3'] : ['python3', 'python'];
  const ext = process.platform === 'win32' ? ['.exe', ''] : [''];
  for (const dir of String(process.env.PATH || '').split(path.delimiter)) {
    if (!dir) continue;
    for (const b of bins) {
      for (const e of ext) {
        if (fs.existsSync(path.join(dir, b + e))) return true;
      }
    }
  }
  return false;
}

function help() {
  process.stdout.write(`${bold(PKG.name)} v${PKG.version}

Install the ai-workflow skill suite into your agent tools' skills directory.

${bold('Install')}
  npm install -g ${PKG.name}

${bold('Usage')}
  ${PKG.name}                     auto-detect tools and install everywhere
  ${PKG.name} claude codex omp     install into the named tools only
  ${PKG.name} --list                  show bundled skills and detected targets
  ${PKG.name} --uninstall [targets]    remove managed skills
  ${PKG.name} --dir <path>            install into an explicit skills root

  One-off without a global install: npx ${PKG.name}

${bold('Flags')}
  --to, --target <ids>   comma or space separated: ${TARGETS.map((t) => t.id).join(', ')}, all
  --dir <path>           explicit skills root (skips auto-detection)
  --force                overwrite directories this tool did not install
  --list                 show status and exit
  --uninstall            remove instead of install
  --help, --version

${bold('After install')}
  Restart the tool, then trigger a skill by name, e.g. /ai-workflow-project
  or say "use ai-workflow for this requirement: ...".
`);
}

function parseArgs(argv) {
  const opts = { targets: [], dir: null, force: false, list: false, uninstall: false, help: false, version: false, json: false };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === '--help' || a === '-h') opts.help = true;
    else if (a === '--version' || a === '-v') opts.version = true;
    else if (a === '--list' || a === '-l') opts.list = true;
    else if (a === '--uninstall' || a === '--remove') opts.uninstall = true;
    else if (a === '--force' || a === '-f') opts.force = true;
    else if (a === '--json') opts.json = true;
    else if (a === '--dir' || a === '--skills-dir' || a === '-d') opts.dir = argv[++i];
    else if (a.startsWith('--dir=')) opts.dir = a.slice(6);
    else if (a === '--to' || a === '--target' || a === '-t') {
      while (i + 1 < argv.length && !argv[i + 1].startsWith('-')) opts.targets.push(argv[++i]);
    } else if (a.startsWith('--to=') || a.startsWith('--target=')) {
      opts.targets.push(...a.split('=').slice(1).join('=').split(','));
    } else if (a === 'all' || ALIASES[String(a).toLowerCase()]) opts.targets.push(a);
    else if (a.startsWith('-')) die(`Unknown flag: ${a} (see --help)`);
    else die(`Unknown argument: ${a} (see --help)`);
  }
  opts.targets = opts.targets.map((t) => String(t).trim()).filter(Boolean);
  return opts;
}

function main() {
  const opts = parseArgs(process.argv.slice(2));
  if (opts.help) return help();
  if (opts.version) return process.stdout.write(`${PKG.version}\n`);
  if (opts.list) return list();

  if (opts.dir) {
    const fake = { id: 'custom', label: 'Custom', base: '', skills: '' };
    if (opts.uninstall) return uninstall(fake, opts);
    return install(fake, opts);
  }

  const targets = resolveTargets(opts.targets);

  if (opts.uninstall) {
    for (const t of targets) uninstall(t, opts);
    return;
  }

  const results = targets.map((t) => install(t, opts));

  const anyChanged = results.some((r) => r.added.length || r.updated.length);
  if (anyChanged) {
    process.stdout.write(`\n${green('Done.')} Restart your agent tool to pick up the skills.\n`);
    process.stdout.write(`  Single requirement: ${bold('/ai-workflow')}   Big project: ${bold('/ai-workflow-project')}\n`);
    if (!pythonHint()) {
      process.stdout.write(`  ${yellow('Note')} ai-workflow-state ships Python helpers (sync.py, validate_state.py); python was not found on PATH.\n`);
    }
  }
  const skipped = results.flatMap((r) => r.skipped);
  if (skipped.length) {
    process.stdout.write(`\n${yellow('Some skills were skipped')} because a same-named directory already existed and was not installed by this tool.\nRe-run with ${bold('--force')} to replace them.\n`);
    process.exit(2);
  }
}

main();
