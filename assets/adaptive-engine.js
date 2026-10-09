(function (root) {
  "use strict";

  const DEFAULTS = Object.freeze({
    minQuestions: 36,
    maxQuestions: 60,
    minPerAxis: 3,
    maxUncertainty: 0.3
  });

  function normalizeQuestion(question, axisCount, id, legacyIndex) {
    const normalized = {
      id,
      axis: question.axis,
      axisWeight: question.axisWeight,
      text: question.text,
      scoreWeight: question.scoreWeight === undefined ? 1 : question.scoreWeight,
      priority: question.priority === undefined ? 1 : question.priority,
      discrimination: question.discrimination === undefined ? 1 : question.discrimination,
      tags: Array.isArray(question.tags) ? question.tags.slice() : [],
      eligibleWhen: question.eligibleWhen || null,
      followUp: Boolean(question.followUp),
      legacyIndex
    };

    if (!Number.isInteger(normalized.axis) || normalized.axis < 0 || normalized.axis >= axisCount) {
      throw new RangeError("Question axis is outside the configured axis range.");
    }
    if (normalized.axisWeight !== 1 && normalized.axisWeight !== -1) {
      throw new TypeError("Question axisWeight must be 1 or -1.");
    }
    if (!normalized.text || !Number.isFinite(normalized.scoreWeight) || normalized.scoreWeight <= 0) {
      throw new TypeError("Questions require text and a positive scoreWeight.");
    }
    return normalized;
  }

  function createQuestionBank(baseQuestions, followUps, axisCount, baseTags) {
    const perAxis = Array(axisCount).fill(0);
    const questions = [];

    baseQuestions.forEach((tuple, legacyIndex) => {
      const axis = tuple[0];
      const sequence = perAxis[axis]++;
      questions.push(normalizeQuestion({
        axis,
        axisWeight: tuple[1],
        text: tuple[2],
        tags: baseTags && baseTags[axis] ? [baseTags[axis][sequence] || "general"] : []
      }, axisCount, "axis-" + String(axis + 1).padStart(2, "0") + "-q" + String(sequence + 1).padStart(2, "0"), legacyIndex));
    });

    followUps.forEach(question => {
      const sequence = perAxis[question.axis]++;
      questions.push(normalizeQuestion(question, axisCount,
        question.id || "axis-" + String(question.axis + 1).padStart(2, "0") + "-q" + String(sequence + 1).padStart(2, "0"),
        questions.length));
    });

    const ids = new Set();
    for (const question of questions) {
      if (ids.has(question.id)) throw new Error("Question IDs must be unique: " + question.id);
      ids.add(question.id);
    }
    return questions;
  }

  function getAxisStats(bank, askedIds, answers, axisCount) {
    const byId = new Map(bank.map(question => [question.id, question]));
    const axes = Array.from({ length: axisCount }, () => []);
    for (const id of askedIds) {
      const question = byId.get(id);
      if (question && Number.isFinite(answers[id])) {
        axes[question.axis].push({ question, answer: answers[id] });
      }
    }
    return axes.map(items => {
      const signed = items.map(item => item.question.axisWeight * item.answer / 2);
      const mean = signed.length ? signed.reduce((sum, value) => sum + value, 0) / signed.length : 0;
      const variance = signed.length
        ? signed.reduce((sum, value) => sum + Math.pow(value - mean, 2), 0) / signed.length
        : 1;
      const neutralRate = items.length ? items.filter(item => item.answer === 0).length / items.length : 1;
      return {
        answered: items.length,
        neutralRate,
        uncertainty: 0.5 * neutralRate + 0.5 * variance
      };
    });
  }

  function getScores(bank, askedIds, answers, axisCount) {
    const byId = new Map(bank.map(question => [question.id, question]));
    const sums = Array(axisCount).fill(0);
    const weights = Array(axisCount).fill(0);
    for (const id of askedIds) {
      const question = byId.get(id);
      const answer = answers[id];
      if (!question || !Number.isFinite(answer)) continue;
      const scoreWeight = Number.isFinite(question.scoreWeight) ? question.scoreWeight : 1;
      sums[question.axis] += question.axisWeight * answer * scoreWeight;
      weights[question.axis] += 2 * scoreWeight;
    }
    return sums.map((sum, axis) => weights[axis]
      ? Math.round(50 + 50 * sum / weights[axis])
      : 50);
  }

  function conditionMatches(condition, stat) {
    if (!condition) return true;
    const checks = [
      ["minAxisResponses", stat.answered, value => stat.answered >= value],
      ["maxAxisResponses", stat.answered, value => stat.answered <= value],
      ["minUncertainty", stat.uncertainty, value => stat.uncertainty >= value],
      ["maxUncertainty", stat.uncertainty, value => stat.uncertainty <= value],
      ["minNeutralRate", stat.neutralRate, value => stat.neutralRate >= value],
      ["maxNeutralRate", stat.neutralRate, value => stat.neutralRate <= value]
    ];
    return checks.every(([key, , passes]) => condition[key] === undefined || passes(condition[key]));
  }

  function selectNextQuestion(bank, state) {
    const options = { ...DEFAULTS, ...(state.config || {}) };
    const axisCount = state.axisCount;
    const askedIds = state.askedIds || [];
    const answers = state.answers || {};
    const asked = new Set(askedIds);
    const stats = getAxisStats(bank, askedIds, answers, axisCount);
    const allAxesCovered = stats.every(stat => stat.answered >= options.minPerAxis);
    const allAxesCertain = stats.every(stat => stat.uncertainty <= options.maxUncertainty);
    const sufficient = askedIds.length >= options.minQuestions && allAxesCovered && allAxesCertain;

    if (askedIds.length >= options.maxQuestions) {
      return { question: null, stopReason: "max-questions", stats };
    }
    if (sufficient) {
      return { question: null, stopReason: "sufficient-information", stats };
    }

    const eligible = bank.filter(question =>
      !asked.has(question.id) &&
      conditionMatches(question.eligibleWhen, stats[question.axis])
    );
    if (!eligible.length) {
      return { question: null, stopReason: "no-eligible-questions", stats };
    }

    const undercovered = eligible.filter(question => stats[question.axis].answered < options.minPerAxis);
    let targetAxes;
    if (undercovered.length) {
      const minimum = Math.min(...undercovered.map(question => stats[question.axis].answered));
      const leastCovered = undercovered.filter(question => stats[question.axis].answered === minimum);
      const maximumUncertainty = Math.max(...leastCovered.map(question => stats[question.axis].uncertainty));
      targetAxes = new Set(leastCovered
        .filter(question => stats[question.axis].uncertainty === maximumUncertainty)
        .map(question => question.axis));
    } else {
      const maximumUncertainty = Math.max(...eligible.map(question => stats[question.axis].uncertainty));
      targetAxes = new Set(eligible
        .filter(question => stats[question.axis].uncertainty === maximumUncertainty)
        .map(question => question.axis));
    }

    const seenTags = new Set(askedIds.flatMap(id => {
      const question = bank.find(candidate => candidate.id === id);
      return question ? question.tags : [];
    }));
    const polarityCounts = Array.from({ length: axisCount }, () => ({ positive: 0, negative: 0 }));
    for (const id of askedIds) {
      const question = bank.find(candidate => candidate.id === id);
      if (question) polarityCounts[question.axis][question.axisWeight > 0 ? "positive" : "negative"]++;
    }

    const candidates = eligible.filter(question => targetAxes.has(question.axis));
    candidates.sort((a, b) => {
      const noveltyA = a.tags.some(tag => !seenTags.has(tag)) ? 1 : 0;
      const noveltyB = b.tags.some(tag => !seenTags.has(tag)) ? 1 : 0;
      const balanceA = polarityCounts[a.axis][a.axisWeight > 0 ? "positive" : "negative"];
      const balanceB = polarityCounts[b.axis][b.axisWeight > 0 ? "positive" : "negative"];
      return noveltyB - noveltyA ||
        (b.discrimination || 1) - (a.discrimination || 1) ||
        (b.priority || 1) - (a.priority || 1) ||
        balanceA - balanceB ||
        bank.indexOf(a) - bank.indexOf(b);
    });

    return { question: candidates[0], stopReason: null, stats };
  }

  const api = { DEFAULTS, createQuestionBank, getAxisStats, getScores, selectNextQuestion };
  root.AdaptiveQuizEngine = api;
  if (typeof module !== "undefined" && module.exports) module.exports = api;
})(typeof globalThis !== "undefined" ? globalThis : this);
