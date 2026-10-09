const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");
const {
  createQuestionBank,
  getAxisStats,
  getScores,
  selectNextQuestion
} = require("../assets/adaptive-engine.js");

function makeBank(axisCount = 2) {
  const questions = [];
  for (let axis = 0; axis < axisCount; axis++) {
    for (let item = 0; item < 5; item++) {
      questions.push({
        id: "a" + axis + "q" + item,
        axis,
        axisWeight: item % 2 ? -1 : 1,
        text: "question " + axis + " " + item,
        tags: ["topic-" + axis + "-" + item],
        discrimination: item === 4 ? 2 : 1,
        eligibleWhen: item === 4 ? { minAxisResponses: 2, minUncertainty: 0.3 } : null
      });
    }
  }
  return questions;
}

const config = { minQuestions: 6, maxQuestions: 10, minPerAxis: 3, maxUncertainty: 0.3 };

function readDeclaration(source, name) {
  const match = source.match(new RegExp("\\bconst\\s+" + name + "\\s*="));
  assert.ok(match, "Missing declaration: " + name);
  let start = match.index + match[0].length;
  while (/\s/.test(source[start])) start++;
  const pairs = { "[": "]", "{": "}", "(": ")" };
  const stack = [pairs[source[start]]];
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
    if (char === "'" || char === '"' || char === "`") quote = char;
    else if (char === "/" && source[index + 1] === "/") {
      index = source.indexOf("\n", index + 2);
    } else if (char === "/" && source[index + 1] === "*") {
      index = source.indexOf("*/", index + 2) + 1;
    } else if (pairs[char]) stack.push(pairs[char]);
    else if (char === stack[stack.length - 1]) {
      stack.pop();
      if (!stack.length) {
        return vm.runInNewContext("(" + source.slice(start, index + 1) + ")");
      }
    }
  }
  throw new Error("Unclosed declaration: " + name);
}

function loadActualQuestionBank() {
  const html = fs.readFileSync(path.join(__dirname, "..", "index.html"), "utf8");
  const axes = readDeclaration(html, "AX");
  const questions = readDeclaration(html, "Q");
  const followUps = readDeclaration(html, "FOLLOW_UP_QUESTIONS");
  const tags = readDeclaration(html, "QUESTION_TAGS");
  return createQuestionBank(questions, followUps, axes.length, tags);
}

test("converts the existing question tuples into stable, tagged axis questions", () => {
  const bank = createQuestionBank([[0, 1, "first"], [0, -1, "second"]], [
    { axis: 0, axisWeight: 1, text: "probe", followUp: true, tags: ["clarify"] }
  ], 1, [["public", "regional"]]);
  assert.deepEqual(bank.map(question => question.id), ["axis-01-q01", "axis-01-q02", "axis-01-q03"]);
  assert.deepEqual(bank.map(question => question.tags[0]), ["public", "regional", "clarify"]);
});

test("editorial revisions preserve the complete bank, item polarity, and metadata", () => {
  const bank = loadActualQuestionBank();
  const expected = {
    "axis-01-q03": [1, "public-services", "Gli standard essenziali di scuola e sanità dovrebbero essere uguali in tutto il Paese."],
    "axis-02-q02": [-1, "executive-authority", "In generale, è preferibile che il governo decida rapidamente, anche se ciò riduce il tempo per la consultazione parlamentare."],
    "axis-02-q03": [1, "voting-rights", "I cittadini adulti dovrebbero avere diritto di voto."],
    "axis-03-q04": [-1, "surveillance", "Per prevenire reati gravi, le autorità dovrebbero poter accedere alle comunicazioni private senza una preventiva autorizzazione del giudice."],
    "axis-04-q01": [1, "cultural-pluralism", "La presenza di culture e religioni diverse nella società è un valore da tutelare."],
    "axis-04-q02": [-1, "assimilation", "Chi immigra dovrebbe adottare le consuetudini culturali prevalenti nel Paese ospitante, anche quando differiscono dalle proprie."],
    "axis-05-q02": [-1, "defense-spending", "Il Paese dovrebbe investire di più nelle capacità di difesa delle forze armate."],
    "axis-05-q04": [-1, "conscription", "Il Paese dovrebbe prevedere il servizio militare obbligatorio."],
    "axis-07-q02": [-1, "private-efficiency", "Per la maggior parte dei servizi pubblici, è preferibile l'erogazione da parte di imprese private anziché di enti statali."],
    "axis-07-q03": [1, "strategic-sectors", "Energia e banche dovrebbero essere di proprietà pubblica."],
    "axis-08-q01": [1, "redistribution", "Lo Stato dovrebbe stabilire obiettivi economici e coordinare produzione e investimenti per ridurre le disuguaglianze."],
    "axis-09-q02": [-1, "free-trade", "Il Paese dovrebbe ridurre le barriere commerciali per favorire il libero scambio."],
    "axis-10-q01": [1, "secularism", "Le istituzioni pubbliche dovrebbero essere neutrali rispetto alle religioni."],
    "axis-10-q03": [1, "religion-role", "Le motivazioni religiose dovrebbero avere un peso limitato nelle decisioni pubbliche."],
    "axis-11-q02": [-1, "family-tradition", "Le politiche familiari dovrebbero dare particolare sostegno alle forme di famiglia comunemente considerate tradizionali."],
    "axis-12-q01": [1, "tech-optimism", "Sono ottimista sul contributo che la tecnologia può dare al progresso della società."],
    "axis-12-q06": [-1, "precautionary-principle", "Quando non è ancora chiaro quali rischi comporti una nuova tecnologia, è preferibile limitarne lo sviluppo anche se potrebbe portare benefici economici."]
  };

  assert.equal(bank.length, 101);
  assert.equal(new Set(bank.map(question => question.id)).size, 101);
  assert.equal(Object.keys(expected).length, 17);

  for (const [id, [axisWeight, tag, text]] of Object.entries(expected)) {
    const question = bank.find(item => item.id === id);
    assert.ok(question, "Missing expected question " + id);
    assert.equal(question.axisWeight, axisWeight, id + " polarity");
    assert.equal(question.text, text, id + " text");
    assert.deepEqual(Array.from(question.tags), [tag], id + " tags");
    assert.equal(bank.filter(item => item.text === text).length, 1, id + " text uniqueness");
    assert.equal(question.scoreWeight, 1, id + " score weight");
    assert.equal(question.followUp, id === "axis-12-q06", id + " follow-up status");
    assert.equal(question.priority, id === "axis-12-q06" ? 2 : 1, id + " priority");
    assert.equal(question.discrimination, id === "axis-12-q06" ? 1.2 : 1, id + " discrimination");
    assert.deepEqual(
      JSON.parse(JSON.stringify(question.eligibleWhen)),
      id === "axis-12-q06"
        ? { minAxisResponses: 2, minUncertainty: 0.3, maxNeutralRate: 0.3 }
        : null,
      id + " eligibility"
    );
  }
});

test("can cover all twelve axes before prioritizing uncertain axes", () => {
  const bank = makeBank(12);
  const askedIds = [];
  const answers = {};
  const coverageConfig = { ...config, minQuestions: 36, maxQuestions: 60 };
  for (let count = 0; count < 36; count++) {
    const next = selectNextQuestion(bank, { askedIds, answers, axisCount: 12, config: coverageConfig });
    assert.ok(next.question);
    askedIds.push(next.question.id);
    answers[next.question.id] = 2;
  }
  assert.deepEqual(getAxisStats(bank, askedIds, answers, 12).map(stat => stat.answered), Array(12).fill(3));
});

test("different answers lead to different follow-up questions", () => {
  const bank = makeBank();
  const askedIds = ["a0q0", "a0q1", "a0q2", "a1q0", "a1q1", "a1q2"];
  const neutral = selectNextQuestion(bank, {
    askedIds,
    answers: Object.fromEntries(askedIds.map(id => [id, 0])),
    axisCount: 2, config
  });
  const consistent = selectNextQuestion(bank, {
    askedIds,
    answers: { a0q0: 2, a0q1: -2, a0q2: 2, a1q0: 0, a1q1: 0, a1q2: 0 },
    axisCount: 2, config
  });
  assert.equal(neutral.question.id, "a0q4");
  assert.equal(consistent.question.id, "a1q4");
});

test("revising a previous answer recalculates both the next question and the score", () => {
  const bank = makeBank();
  const askedIds = ["a0q0", "a0q1", "a0q2", "a1q0", "a1q1", "a1q2"];
  const answers = Object.fromEntries(askedIds.map(id => [id, 0]));
  const initialScore = getScores(bank, askedIds, answers, 2)[0];
  const initialNext = selectNextQuestion(bank, { askedIds, answers, axisCount: 2, config }).question.id;
  answers.a0q0 = 2;
  const revisedScore = getScores(bank, askedIds, answers, 2)[0];
  const revisedNext = selectNextQuestion(bank, { askedIds, answers, axisCount: 2, config }).question.id;
  assert.equal(initialScore, 50);
  assert.equal(revisedScore, 67);
  assert.equal(initialNext, "a0q4");
  assert.equal(revisedNext, "a1q4");
});

test("does not repeat questions and skips candidates already on the path", () => {
  const bank = makeBank();
  const result = selectNextQuestion(bank, {
    askedIds: ["a0q0", "a0q1", "a1q0"],
    answers: { a0q0: 0, a0q1: 0, a1q0: 1 },
    axisCount: 2, config
  });
  assert.ok(result.question);
  assert.ok(!["a0q0", "a0q1", "a1q0"].includes(result.question.id));
});

test("scores only questions actually answered using the existing axis formula", () => {
  const bank = makeBank();
  const scores = getScores(bank, ["a0q0", "a0q1"], { a0q0: 2, a0q1: 1, a1q0: 2 }, 2);
  assert.equal(scores[0], 63);
  assert.equal(scores[1], 50);
});

test("reports neutral answers as uncertainty rather than as a directional position", () => {
  const bank = makeBank();
  const stats = getAxisStats(bank, ["a0q0", "a0q1"], { a0q0: 0, a0q1: 0 }, 2);
  assert.equal(stats[0].neutralRate, 1);
  assert.equal(stats[0].uncertainty, 0.5);
});

test("ends when minimum coverage and information criteria are met", () => {
  const bank = makeBank();
  const askedIds = ["a0q0", "a0q1", "a0q2", "a1q0", "a1q1", "a1q2"];
  const answers = Object.fromEntries(askedIds.map((id, index) => [id, index % 2 ? -2 : 2]));
  const result = selectNextQuestion(bank, { askedIds, answers, axisCount: 2, config });
  assert.equal(result.stopReason, "sufficient-information");
  assert.equal(result.question, null);
});

test("honors the maximum even when more clarification items remain", () => {
  const bank = makeBank();
  const askedIds = bank.slice(0, 10).map(question => question.id);
  const answers = Object.fromEntries(askedIds.map(id => [id, 2]));
  const result = selectNextQuestion(bank, { askedIds, answers, axisCount: 2, config });
  assert.equal(result.stopReason, "max-questions");
});

test("stops cleanly when there are no eligible questions", () => {
  const bank = [{ id: "only", axis: 0, axisWeight: 1, text: "only", tags: [] }];
  const result = selectNextQuestion(bank, {
    askedIds: ["only"], answers: { only: 2 }, axisCount: 1,
    config: { ...config, minPerAxis: 1 }
  });
  assert.equal(result.stopReason, "no-eligible-questions");
  assert.equal(result.question, null);
});

test("handles missing answers without counting them as neutral", () => {
  const bank = makeBank();
  const stats = getAxisStats(bank, ["a0q0"], {}, 2);
  assert.equal(stats[0].answered, 0);
  assert.equal(stats[0].neutralRate, 1);
  assert.deepEqual(getScores(bank, ["a0q0"], {}, 2), [50, 50]);
});
