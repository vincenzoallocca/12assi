const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");
const { execFileSync } = require("node:child_process");

const root = path.resolve(__dirname, "..");
const useHead = process.argv.includes("--before");
const includeQuestionAudit = process.argv.includes("--audit");
const readHeadSource = file => execFileSync("git", [
  "show",
  "HEAD:" + path.relative(root, file).replace(/\\/g, "/")
], { cwd: root, encoding: "utf8" });
const readSource = file => useHead ? readHeadSource(file) : fs.readFileSync(file, "utf8");

function declaration(source, name) {
  const match = source.match(new RegExp("\\bconst\\s+" + name + "\\s*="));
  if (!match) throw new Error("Could not find " + name + " in index.html");
  let start = match.index + match[0].length;
  while (/\s/.test(source[start])) start++;
  let opening = source[start];
  if (source.startsWith("Object.freeze(", start)) {
    start += "Object.freeze".length;
    opening = source[start];
    while (/\s/.test(source[start])) start++;
    opening = source[start];
  }
  const pairs = { "[": "]", "{": "}", "(": ")" };
  if (!pairs[opening]) throw new Error("Unexpected initializer for " + name);
  const stack = [pairs[opening]];
  let quote = null;
  let escaped = false;
  for (let index = start + 1; index < source.length; index++) {
    const char = source[index];
    if (quote) {
      if (escaped) escaped = false;
      else if (char === "\\") escaped = true;
      else if (char === quote) quote = null;
      continue;
    }
    if (char === "'" || char === '"' || char === "`") {
      quote = char;
      continue;
    }
    if (char === "/" && source[index + 1] === "/") {
      const end = source.indexOf("\n", index + 2);
      index = end < 0 ? source.length : end;
      continue;
    }
    if (char === "/" && source[index + 1] === "*") {
      const end = source.indexOf("*/", index + 2);
      if (end < 0) throw new Error("Unclosed comment while parsing " + name);
      index = end + 1;
      continue;
    }
    if (pairs[char]) stack.push(pairs[char]);
    else if (char === stack[stack.length - 1]) {
      stack.pop();
      if (!stack.length) return vm.runInNewContext("(" + source.slice(start, index + 1) + ")");
    }
  }
  throw new Error("Unclosed initializer for " + name);
}

function loadEngine(source) {
  const module = { exports: {} };
  const sandbox = { module, exports: module.exports };
  sandbox.globalThis = sandbox;
  vm.runInNewContext(source, sandbox, { filename: "adaptive-engine.js" });
  return module.exports;
}

function seededValues(seed) {
  let state = seed >>> 0;
  return () => {
    state ^= state << 13;
    state ^= state >>> 17;
    state ^= state << 5;
    return (state >>> 0) / 4294967296;
  };
}

function syntheticCohort(seed) {
  const random = seededValues(seed);
  const positions = [0, 25, 50, 75, 100];
  return Array.from({ length: 50 }, (_, person) => ({
    name: "synthetic-" + seed + "-" + String(person + 1).padStart(2, "0"),
    values: Array.from({ length: 12 }, (_, axis) => {
      const mode = (person + axis + (random() < 0.5 ? 0 : 1)) % 4;
      if (mode === 0) return positions[random() < 0.5 ? 0 : 4];
      if (mode === 1) return positions[random() < 0.5 ? 1 : 3];
      if (mode === 2) return Math.round(10 + random() * 80);
      return [45, 50, 55][Math.floor(random() * 3)];
    })
  }));
}

function deterministicNoise(person, questionId) {
  const input = person + "|" + questionId;
  let hash = 2166136261;
  for (let index = 0; index < input.length; index++) {
    hash ^= input.charCodeAt(index);
    hash = Math.imul(hash, 16777619);
  }
  let state = hash >>> 0;
  state ^= state << 13;
  state ^= state >>> 17;
  state ^= state << 5;
  const sample = (state >>> 0) / 4294967296;
  if (sample >= 0.12) return 0;
  return sample < 0.06 ? -1 : 1;
}

function compatibility(a, b) {
  const distance = a.reduce((sum, value, axis) => sum + Math.abs(value - b[axis]), 0);
  return Math.max(1, Math.round(100 - distance / 12 * 1.3));
}

function textSimilarity(a, b) {
  const stopWords = new Set(["anche", "che", "con", "delle", "degli", "della", "dovrebbe", "dovrebbero", "il", "la", "le", "lo", "nel", "nella", "non", "per", "quando", "se", "sono", "una", "uno"]);
  const tokens = text => new Set(text.toLowerCase()
    .normalize("NFD").replace(/[\u0300-\u036f]/g, "")
    .replace(/[^a-z0-9\s]/g, " ").split(/\s+/)
    .filter(token => token.length > 2 && !stopWords.has(token)));
  const first = tokens(a);
  const second = tokens(b);
  const shared = [...first].filter(token => second.has(token)).length;
  const union = new Set([...first, ...second]).size;
  return union ? shared / union : 0;
}

function findSimilarQuestions(bank) {
  const pairs = [];
  for (let first = 0; first < bank.length; first++) {
    for (let second = first + 1; second < bank.length; second++) {
      const a = bank[first];
      const b = bank[second];
      if (a.axis !== b.axis) continue;
      const sharedTags = a.tags.filter(tag => b.tags.includes(tag));
      const similarity = textSimilarity(a.text, b.text);
      if (sharedTags.length || similarity >= 0.35) {
        pairs.push({
          firstId: a.id,
          secondId: b.id,
          axis: a.axis,
          sharedTags,
          textJaccard: Math.round(similarity * 100) / 100
        });
      }
    }
  }
  return pairs;
}

function simulate(cohort, engine, bank, config, axisCount, gallery) {
  const usage = new Map(bank.map(question => [question.id, {
    offered: 0,
    candidate: 0,
    selected: 0,
    alternativesAtSelection: 0,
    responses: { "-2": 0, "-1": 0, "0": 0, "1": 0, "2": 0 },
    neutralCount: 0,
    significantScoreChangeCount: 0
  }]));
  let selectionDiagnosticsAvailable = true;
  const rows = cohort.map(person => {
    const askedIds = [];
    const answers = {};
    let stopReason = null;
    while (askedIds.length < config.maxQuestions) {
      const selection = engine.selectNextQuestion(bank, { askedIds, answers, axisCount, config });
      if (!selection.question) {
        stopReason = selection.stopReason;
        break;
      }
      const question = selection.question;
      const eligibleIds = selection.diagnostics?.eligibleQuestionIds || [];
      const candidateIds = selection.diagnostics?.candidateQuestionIds || [];
      if (!selection.diagnostics) selectionDiagnosticsAvailable = false;
      for (const id of eligibleIds) usage.get(id).offered++;
      for (const id of candidateIds) usage.get(id).candidate++;
      const questionUsage = usage.get(question.id);
      questionUsage.selected++;
      questionUsage.alternativesAtSelection += Math.max(0, eligibleIds.length - 1);
      askedIds.push(question.id);
      const signal = Math.round((person.values[question.axis] - 50) / 25);
      const noise = person.name.startsWith("synthetic-") ? deterministicNoise(person.name, question.id) : 0;
      answers[question.id] = Math.max(-2, Math.min(2, signal * question.axisWeight + noise));
      questionUsage.responses[String(answers[question.id])]++;
      if (answers[question.id] === 0) questionUsage.neutralCount++;
      const scoredAnswer = engine.getScores(bank, askedIds, answers, axisCount)[question.axis];
      answers[question.id] = 0;
      const neutralScore = engine.getScores(bank, askedIds, answers, axisCount)[question.axis];
      answers[question.id] = Math.max(-2, Math.min(2, signal * question.axisWeight + noise));
      if (Math.abs(scoredAnswer - neutralScore) >= 2) questionUsage.significantScoreChangeCount++;
    }

    const stats = engine.getAxisStats(bank, askedIds, answers, axisCount);
    const scores = engine.getScores(bank, askedIds, answers, axisCount);
    const ranking = gallery.map((candidate, index) => ({
      name: candidate[0],
      index,
      compatibility: compatibility(scores, candidate[4])
    })).sort((a, b) => b.compatibility - a.compatibility || a.index - b.index);
    const galleryTargetIndex = gallery.findIndex(candidate => candidate[0] === person.name);
    const targetIndex = galleryTargetIndex >= 0 ? galleryTargetIndex : gallery
      .map((candidate, index) => ({
        index,
        distance: candidate[4].reduce((sum, value, axis) => sum + Math.abs(value - person.values[axis]), 0)
      }))
      .sort((a, b) => a.distance - b.distance || a.index - b.index)[0].index;
    const target = galleryTargetIndex >= 0 ? gallery[galleryTargetIndex][4] : person.values;
    const targetScoreError = scores.reduce((sum, score, axis) => sum + Math.abs(score - target[axis]), 0) / axisCount;
    const reversedIds = askedIds.slice().reverse();
    const reorderedStats = engine.getAxisStats(bank, reversedIds, answers, axisCount);
    const reorderedScores = engine.getScores(bank, reversedIds, answers, axisCount);
    const reorderedNext = engine.selectNextQuestion(bank, {
      askedIds: reversedIds, answers, axisCount, config
    }).question;
    const normalNext = engine.selectNextQuestion(bank, {
      askedIds, answers, axisCount, config
    }).question;
    return {
      person: person.name,
      askedIds,
      stopReason: stopReason || "max-questions",
      coverage: stats.map(stat => stat.answered),
      uncertainty: stats.map(stat => stat.uncertainty),
      scores,
      targetScoreError,
      topMatch: ranking[0].index === targetIndex,
      orderInvariant: scores.every((score, axis) => score === reorderedScores[axis]) &&
        stats.every((stat, axis) => Math.abs(stat.uncertainty - reorderedStats[axis].uncertainty) < 1e-12) &&
        (normalNext ? normalNext.id : null) === (reorderedNext ? reorderedNext.id : null)
    };
  });

  const lengths = rows.map(row => row.askedIds.length);
  const lengthHistogram = lengths.reduce((counts, length) => {
    counts[length] = (counts[length] || 0) + 1;
    return counts;
  }, {});
  const uniqueSequences = new Set(rows.map(row => row.askedIds.join("|"))).size;
  const axisStats = Array.from({ length: axisCount }, (_, axis) => ({
    axis: axis + 1,
    name: config.axisNames[axis],
    minCoverage: Math.min(...rows.map(row => row.coverage[axis])),
    meanCoverage: average(rows.map(row => row.coverage[axis])),
    uncertainAtEnd: rows.filter(row => row.uncertainty[axis] > config.maxUncertainty).length,
    exhaustedAndUncertain: rows.filter(row => row.stopReason === "no-eligible-questions" && row.uncertainty[axis] > config.maxUncertainty).length
  }));
  const stops = rows.reduce((counts, row) => {
    counts[row.stopReason] = (counts[row.stopReason] || 0) + 1;
    return counts;
  }, {});
  const repeats = rows.reduce((count, row) => count + row.askedIds.length - new Set(row.askedIds).size, 0);
  const replays = rows.every((row, index) => {
    const again = simulateOne(cohort[index], engine, bank, config, axisCount);
    return row.stopReason === again.stopReason && row.askedIds.join("|") === again.askedIds.join("|");
  });
  const questionAudit = bank.map(question => {
    const stat = usage.get(question.id);
    return {
      id: question.id,
      text: question.text,
      axis: question.axis,
      axisName: config.axisNames[question.axis],
      axisWeight: question.axisWeight,
      tags: question.tags,
      eligibility: question.eligibleWhen,
      offered: selectionDiagnosticsAvailable ? stat.offered : null,
      candidateOffers: selectionDiagnosticsAvailable ? stat.candidate : null,
      selected: stat.selected,
      selectionRateWhenOffered: selectionDiagnosticsAvailable && stat.offered ? stat.selected / stat.offered : null,
      selectionRateWhenCandidate: selectionDiagnosticsAvailable && stat.candidate ? stat.selected / stat.candidate : null,
      meanAlternativesWhenSelected: stat.selected ? stat.alternativesAtSelection / stat.selected : null,
      responseDistribution: stat.responses,
      neutralRate: stat.selected ? stat.neutralCount / stat.selected : null,
      significantScoreChangeRate: stat.selected ? stat.significantScoreChangeCount / stat.selected : null
    };
  });
  const selectedTotal = questionAudit.reduce((sum, item) => sum + item.selected, 0);
  const orderInvariant = rows.every(row => row.orderInvariant);
  return {
    sampleSize: rows.length,
    questions: {
      mean: average(lengths),
      min: Math.min(...lengths),
      max: Math.max(...lengths),
      histogram: lengthHistogram
    },
    uniquePaths: new Set(rows.map(row => row.askedIds.join("|"))).size,
    distinctSequences: uniqueSequences,
    repeatedQuestions: repeats,
    orderInvariant,
    minCoverageByAxis: axisStats.map(stat => stat.minCoverage),
    axisCoverage: axisStats,
    stopReasons: stops,
    meanUncertainAxesAtEnd: average(rows.map(row =>
      row.uncertainty.filter(uncertainty => uncertainty > config.maxUncertainty).length
    )),
    exhaustedAndUncertainByAxis: axisStats.map(stat => stat.exhaustedAndUncertain),
    axesMostOftenExhausted: axisStats.slice().sort((a, b) =>
      b.exhaustedAndUncertain - a.exhaustedAndUncertain || a.axis - b.axis
    ).slice(0, 5).map(stat => ({ axis: stat.axis, name: stat.name, profiles: stat.exhaustedAndUncertain })),
    reproducible: replays,
    questionUsage: {
      selectionDiagnosticsAvailable,
      questionsSelected: selectedTotal,
      questionsNeverSelected: questionAudit.filter(item => item.selected === 0).length,
      meanSelectionRateWhenOffered: selectionDiagnosticsAvailable
        ? average(questionAudit.filter(item => item.offered).map(item => item.selectionRateWhenOffered))
        : null,
      mostSelected: questionAudit.slice().sort((a, b) => b.selected - a.selected).slice(0, 10)
        .map(item => ({ id: item.id, axisName: item.axisName, selected: item.selected })),
      leastSelected: questionAudit.slice().sort((a, b) => a.selected - b.selected).slice(0, 10)
        .map(item => ({ id: item.id, axisName: item.axisName, selected: item.selected }))
    },
    ...(includeQuestionAudit ? { questionAudit } : {}),
    indicativeTargetCompatibility: gallery.length
      ? { topMatchCount: rows.filter(row => row.topMatch).length, meanAxisScoreError: average(rows.map(row => row.targetScoreError)) }
      : { meanAxisScoreError: average(rows.map(row => row.targetScoreError)) }
  };
}

function simulateOne(person, engine, bank, config, axisCount) {
  const askedIds = [];
  const answers = {};
  let stopReason = null;
  while (askedIds.length < config.maxQuestions) {
    const selection = engine.selectNextQuestion(bank, { askedIds, answers, axisCount, config });
    if (!selection.question) {
      stopReason = selection.stopReason;
      break;
    }
    const question = selection.question;
    askedIds.push(question.id);
    const signal = Math.round((person.values[question.axis] - 50) / 25);
    const noise = person.name.startsWith("synthetic-") ? deterministicNoise(person.name, question.id) : 0;
    answers[question.id] = Math.max(-2, Math.min(2, signal * question.axisWeight + noise));
  }
  return { askedIds, stopReason: stopReason || "max-questions" };
}

function simulateControlled(pattern, engine, bank, config, axisCount) {
  const askedIds = [];
  const answers = {};
  const axisCounts = Array(axisCount).fill(0);
  const eligibleIds = new Set();
  const eligibleFollowUpIds = new Set();
  const selectedFollowUpIds = [];
  const followUpsSelectedByAxis = Array(axisCount).fill(0);
  let eligibilityDiagnosticsAvailable = true;
  let stopReason = null;
  while (askedIds.length < config.maxQuestions) {
    const selection = engine.selectNextQuestion(bank, { askedIds, answers, axisCount, config });
    if (!selection.question) {
      stopReason = selection.stopReason;
      break;
    }
    const question = selection.question;
    if (!selection.diagnostics) eligibilityDiagnosticsAvailable = false;
    for (const id of selection.diagnostics?.eligibleQuestionIds || []) {
      eligibleIds.add(id);
      const eligibleQuestion = bank.find(candidate => candidate.id === id);
      if (eligibleQuestion?.followUp) eligibleFollowUpIds.add(id);
    }
    if (question.followUp) {
      followUpsSelectedByAxis[question.axis]++;
      selectedFollowUpIds.push(question.id);
    }
    const index = axisCounts[question.axis]++;
    const response = pattern === "neutral"
      ? 0
      : pattern === "contradictory"
        ? (index % 2 ? -2 : 2) * question.axisWeight
        : (pattern === "moderate-consistent" ? 1 : 2) * question.axisWeight;
    askedIds.push(question.id);
    answers[question.id] = response;
  }
  const stats = engine.getAxisStats(bank, askedIds, answers, axisCount);
  return {
    questions: askedIds.length,
    stopReason: stopReason || "max-questions",
    minCoverage: Math.min(...stats.map(stat => stat.answered)),
    uncertainAxes: stats.filter(stat => stat.uncertainty > config.maxUncertainty).length,
    meanUncertainty: average(stats.map(stat => stat.uncertainty)),
    scores: engine.getScores(bank, askedIds, answers, axisCount),
    followUpsSelectedByAxis,
    eligibleFollowUpIds: eligibilityDiagnosticsAvailable ? Array.from(eligibleFollowUpIds) : null,
    selectedFollowUpIds,
    neverEligibleQuestionIds: eligibilityDiagnosticsAvailable
      ? bank.filter(question => !eligibleIds.has(question.id)).map(question => question.id)
      : null
  };
}

function average(values) {
  return values.reduce((sum, value) => sum + value, 0) / values.length;
}

function roundMetrics(value) {
  if (Array.isArray(value)) return value.map(roundMetrics);
  if (value && typeof value === "object") {
    return Object.fromEntries(Object.entries(value).map(([key, item]) => [key, roundMetrics(item)]));
  }
  return typeof value === "number" ? Math.round(value * 100) / 100 : value;
}

function run(version, html, engineSource, cohorts) {
  const engine = loadEngine(engineSource);
  const axisNames = declaration(html, "AX").map(axis => axis[0]);
  const base = declaration(html, "Q");
  const followUps = declaration(html, "FOLLOW_UP_QUESTIONS");
  const tags = declaration(html, "QUESTION_TAGS");
  const config = { ...declaration(html, "ADAPTIVE_CONFIG"), axisNames };
  const bank = engine.createQuestionBank(base, followUps, axisNames.length, tags);
  const gallery = declaration(html, "PPL");
  const controlled = Object.fromEntries([
    "endpoint-consistent",
    "moderate-consistent",
    "neutral",
    "contradictory"
  ].map(pattern => [pattern, simulateControlled(pattern, engine, bank, config, axisNames.length)]));
  return {
    version,
    adaptiveConfig: config,
    questionBank: { original: base.length, followUps: followUps.length, total: bank.length },
    questionModel: "Each bank item has one explicitly assigned axis and one signed scoring weight.",
    responseModelLimit: "Within each axis, every question response is derived from the same target profile value; question wording and rationale are not modeled.",
    metricDefinitions: {
      score: "Per axis: round(50 + 50 * sum(axisWeight * answer * scoreWeight) / sum(2 * scoreWeight)); only answered items contribute.",
      uncertainty: "0.5 * observed neutral rate + 0.5 * population variance of polarity-normalized answers; no sample-size term and not probabilistically calibrated.",
      eligibleOffer: "The question is eligible under its configured conditions at a selection step.",
      candidateOffer: "The question is eligible and belongs to the selector's target-axis subset at that step.",
      significantScoreChange: "The displayed rounded axis score changes by at least 2 points compared with the same answer replaced by neutral.",
      questionOverlapPairs: "Same-axis questions sharing a tag or exceeding 0.35 Jaccard similarity after basic Italian stop-word removal; candidates for review, not asserted duplicates."
    },
    questionOverlapPairs: findSimilarQuestions(bank),
    controlledScenarios: controlled,
    cohorts: Object.fromEntries(Object.entries(cohorts).map(([name, people]) => [
      name,
      simulate(people, engine, bank, config, axisNames.length, gallery)
    ]))
  };
}

const htmlPath = path.join(root, "index.html");
const enginePath = path.join(root, "assets", "adaptive-engine.js");
const currentHtml = readSource(htmlPath);
const currentEngine = readSource(enginePath);
const currentGallery = declaration(currentHtml, "PPL").map(person => ({ name: person[0], values: person[4] }));
const cohorts = {
  gallery: currentGallery,
  syntheticSeed20261009: syntheticCohort(20261009),
  syntheticSeed424242: syntheticCohort(424242)
};
const current = run(useHead ? "HEAD baseline" : "working tree", currentHtml, currentEngine, cohorts);
const report = useHead
  ? {
      simulation: {
        gallery: "Profile scores are mapped to the nearest available answer; no response noise.",
        synthetic: "Seeded target profiles with deterministic question-specific +/-1 response noise on 12% of answers. All items on an axis still derive their base response from the same target scalar; item wording is not modeled."
      },
      baseline: current
    }
  : {
      simulation: {
        gallery: "Profile scores are mapped to the nearest available answer; no response noise.",
        synthetic: "Seeded target profiles with deterministic question-specific +/-1 response noise on 12% of answers. All items on an axis still derive their base response from the same target scalar; item wording is not modeled."
      },
        comparisonBasis: "Before uses the committed engine with the current worktree question bank, isolating engine behavior from bank changes.",
        before: run("Pre-audit engine (HEAD) with current question bank", currentHtml, readHeadSource(enginePath), cohorts),
        after: current
      };
process.stdout.write(JSON.stringify(roundMetrics(report), null, 2) + "\n");
