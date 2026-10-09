const test = require("node:test");
const assert = require("node:assert/strict");
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

test("converts the existing question tuples into stable, tagged axis questions", () => {
  const bank = createQuestionBank([[0, 1, "first"], [0, -1, "second"]], [
    { axis: 0, axisWeight: 1, text: "probe", followUp: true, tags: ["clarify"] }
  ], 1, [["public", "regional"]]);
  assert.deepEqual(bank.map(question => question.id), ["axis-01-q01", "axis-01-q02", "axis-01-q03"]);
  assert.deepEqual(bank.map(question => question.tags[0]), ["public", "regional", "clarify"]);
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
