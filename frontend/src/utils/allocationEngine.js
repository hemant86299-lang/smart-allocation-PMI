/**
 * allocationEngine.js
 * ---------------------------------------------------------------------------
 * DEMO ALLOCATION ENGINE — runs entirely in the browser, no API calls.
 *
 * This is a frontend demonstration of the pipeline implemented in Python under
 * `../../src`. It follows the same stages and the same objective function, but
 * it is NOT the production model:
 *
 *   | Stage                | Real engine (src/*.py)          | This demo         |
 *   |----------------------|---------------------------------|-------------------|
 *   | Eligibility filter   | rule-based (eligibility.py)     | same rules        |
 *   | Fit scoring          | fuzzy logic (scikit-fuzzy)      | weighted score    |
 *   | Acceptance predictor | Logistic Regression (sklearn)   | logistic formula  |
 *   | Optimisation         | OR-Tools CP-SAT (exact ILP)     | greedy on utility |
 *   | Reallocation         | reallocation.py                 | same procedure    |
 *
 * The objective is identical in form: maximise SUM(matchScore x acceptProbability)
 * subject to (1) one internship per candidate, (2) seats <= capacity,
 * (3) reserved-category seats only go to that category.
 *
 * Everything here is deterministic: the same input always produces the same
 * allocation, so a demo can be re-run live without surprises.
 * ---------------------------------------------------------------------------
 */

import { ELIGIBILITY_RULES, SCORE_WEIGHTS } from '../data/mockData.js'

/* -------------------------------------------------------------------------- */
/* STAGE 1 — ELIGIBILITY (hard rules, mirrors src/eligibility.py)             */
/* -------------------------------------------------------------------------- */

/** Skills the candidate shares with the opportunity's requirements. */
export function skillOverlap(candidate, opportunity) {
  const required = new Set(opportunity.requiredSkills)
  return candidate.skills.filter((s) => required.has(s))
}

/** % of the opportunity's required skills that the candidate holds. */
export function skillMatchPct(candidate, opportunity) {
  if (!opportunity.requiredSkills.length) return 0
  return (skillOverlap(candidate, opportunity).length / opportunity.requiredSkills.length) * 100
}

/**
 * Candidate location preferences, primary first.
 * The Python filter compares a single `location_pref`; the demo accepts the
 * candidate's alternate cities too (a documented widening, so that location
 * becomes a scored dimension rather than a pure on/off gate).
 */
export function locationPreferences(candidate) {
  return [candidate.locationPref, ...(candidate.altLocations || [])]
}

/** Runs the three hard eligibility rules and reports each one individually. */
export function checkEligibility(candidate, opportunity) {
  const overlap = skillOverlap(candidate, opportunity)
  const prefs = locationPreferences(candidate)

  const checks = [
    {
      rule: 'Minimum qualification score',
      requirement: `>= ${ELIGIBILITY_RULES.minQualificationScore}`,
      actual: `${candidate.qualificationScore}`,
      passed: candidate.qualificationScore >= ELIGIBILITY_RULES.minQualificationScore,
    },
    {
      rule: 'Location preference match',
      requirement: opportunity.location,
      actual: prefs.join(', '),
      passed: prefs.includes(opportunity.location),
    },
    {
      rule: 'Minimum skill overlap',
      requirement: `>= ${ELIGIBILITY_RULES.minSkillOverlap} required skill`,
      actual: overlap.length ? overlap.join(', ') : 'none',
      passed: overlap.length >= ELIGIBILITY_RULES.minSkillOverlap,
    },
  ]

  const failed = checks.filter((chk) => !chk.passed)

  return {
    eligible: failed.length === 0,
    checks,
    failedRules: failed.map((chk) => chk.rule),
  }
}

/** Reserved-category constraint — a hard fairness rule, never a tie-breaker. */
export function categoryAllowed(candidate, opportunity) {
  if (!opportunity.reservedCategory) return true
  return candidate.category === opportunity.reservedCategory
}

/* -------------------------------------------------------------------------- */
/* STAGE 2 — MATCH SCORE (weighted components)                                */
/* -------------------------------------------------------------------------- */

function locationComponent(candidate, opportunity) {
  if (candidate.locationPref === opportunity.location) return 100
  if ((candidate.altLocations || []).includes(opportunity.location)) return 70
  return 0
}

function preferenceComponent(candidate, opportunity) {
  if ((candidate.preferredRoles || []).includes(opportunity.role)) return 100
  if (candidate.preferredSector === opportunity.sector) return 60
  return 25
}

/**
 * Weighted match score in 0-100.
 * Weights come from SCORE_WEIGHTS: skill 40, education 20, location 15,
 * preference 15, eligibility 10.
 */
export function scorePair(candidate, opportunity) {
  const overlap = skillOverlap(candidate, opportunity)
  const eligibility = checkEligibility(candidate, opportunity)

  const components = {
    skill: Math.round(skillMatchPct(candidate, opportunity) * 10) / 10,
    education: candidate.qualificationScore,
    location: locationComponent(candidate, opportunity),
    preference: preferenceComponent(candidate, opportunity),
    eligibility: eligibility.eligible ? 100 : 0,
  }

  const weighted =
    (components.skill * SCORE_WEIGHTS.skill +
      components.education * SCORE_WEIGHTS.education +
      components.location * SCORE_WEIGHTS.location +
      components.preference * SCORE_WEIGHTS.preference +
      components.eligibility * SCORE_WEIGHTS.eligibility) /
    100

  const matchScore = Math.round(weighted * 10) / 10

  /* Stage 3 stand-in for the logistic-regression acceptance model. */
  const z =
    -5.0 +
    0.07 * matchScore +
    0.01 * components.preference +
    0.005 * (candidate.experienceMonths || 0)
  const acceptProbability = Math.round((1 / (1 + Math.exp(-z))) * 1000) / 1000

  return {
    candidateId: candidate.id,
    opportunityId: opportunity.id,
    components,
    matchScore,
    acceptProbability,
    /* Same objective the CP-SAT optimiser maximises: fit x acceptance. */
    utility: Math.round(matchScore * acceptProbability * 100) / 100,
    overlapSkills: overlap,
    missingSkills: opportunity.requiredSkills.filter((s) => !overlap.includes(s)),
    eligibility,
    categoryAllowed: categoryAllowed(candidate, opportunity),
    meetsThreshold: matchScore >= opportunity.matchThreshold,
  }
}

/** Short human-readable justification shown in the allocation tables. */
export function explainMatch(pair, candidate, opportunity) {
  const { overlapSkills, components } = pair
  const skills = overlapSkills.slice(0, 3).join(' + ')

  if (components.skill >= 100) {
    return `Full skill match (${skills})`
  }
  if (components.skill >= 60) {
    return `Strong ${skills} match, score ${candidate.qualificationScore}`
  }
  if (components.preference === 100) {
    return `${skills} match + preferred role`
  }
  if (components.location === 100) {
    return `${skills} match in preferred city ${opportunity.location}`
  }
  return `Partial ${skills} match, qualification ${candidate.qualificationScore}`
}

/** Why an eligible candidate still did not get this seat. */
function blockedReason(pair, opportunity) {
  if (!pair.categoryAllowed) {
    return {
      code: 'RESERVED_CATEGORY',
      text: `Seat reserved for ${opportunity.reservedCategory} category`,
    }
  }
  if (!pair.meetsThreshold) {
    return {
      code: 'BELOW_THRESHOLD',
      text: `Match score ${pair.matchScore} below the ${opportunity.matchThreshold} threshold`,
    }
  }
  return { code: 'CAPACITY_FULL', text: 'All seats filled by higher-utility candidates' }
}

/* -------------------------------------------------------------------------- */
/* STAGE 3 — BUILD THE SCORED PAIR SET                                        */
/* -------------------------------------------------------------------------- */

/**
 * Scores every candidate x opportunity combination and splits the result into
 * eligible pairs (feasible for the optimiser) and rejected pairs (with reason).
 */
export function buildScoredPairs(candidates, opportunities) {
  const eligiblePairs = []
  const rejectedPairs = []

  candidates.forEach((candidate) => {
    opportunities.forEach((opportunity) => {
      const pair = scorePair(candidate, opportunity)
      if (pair.eligibility.eligible) {
        eligiblePairs.push(pair)
      } else {
        rejectedPairs.push(pair)
      }
    })
  })

  eligiblePairs.sort((a, b) => b.utility - a.utility)

  return {
    eligiblePairs,
    rejectedPairs,
    totalCombinations: candidates.length * opportunities.length,
  }
}

/* -------------------------------------------------------------------------- */
/* STAGE 4 — OPTIMISATION                                                     */
/* -------------------------------------------------------------------------- */

/**
 * Greedy assignment over pairs ordered by utility (matchScore x acceptProbability).
 *
 * Constraints enforced, identical to optimizer.py:
 *   1. each candidate receives at most one internship
 *   2. an internship never exceeds its capacity
 *   3. reserved-category seats only go to candidates of that category
 * Plus a demo-only gate: the pair must clear the opportunity's match threshold.
 *
 * The production engine solves this exactly with OR-Tools CP-SAT; greedy is a
 * close approximation that runs instantly in the browser.
 */
export function runAllocation(candidates, opportunities) {
  const { eligiblePairs, rejectedPairs, totalCombinations } = buildScoredPairs(
    candidates,
    opportunities
  )

  const seatsLeft = {}
  opportunities.forEach((opp) => {
    seatsLeft[opp.id] = opp.capacity
  })

  const assignedCandidate = {}
  const allocations = []
  const consideredButBlocked = {}

  eligiblePairs.forEach((pair) => {
    const candidate = candidates.find((cd) => cd.id === pair.candidateId)
    const opportunity = opportunities.find((op) => op.id === pair.opportunityId)

    const feasible =
      !assignedCandidate[pair.candidateId] &&
      seatsLeft[pair.opportunityId] > 0 &&
      pair.categoryAllowed &&
      pair.meetsThreshold

    if (feasible) {
      seatsLeft[pair.opportunityId] -= 1
      assignedCandidate[pair.candidateId] = pair.opportunityId
      allocations.push({
        candidateId: candidate.id,
        candidateName: candidate.name,
        category: candidate.category,
        education: candidate.education,
        college: candidate.college,
        skills: candidate.skills,
        opportunityId: opportunity.id,
        company: opportunity.company,
        role: opportunity.role,
        location: opportunity.location,
        sector: opportunity.sector,
        matchScore: pair.matchScore,
        acceptProbability: pair.acceptProbability,
        utility: pair.utility,
        components: pair.components,
        overlapSkills: pair.overlapSkills,
        missingSkills: pair.missingSkills,
        reason: explainMatch(pair, candidate, opportunity),
        status: 'Allocated',
      })
    } else if (!assignedCandidate[pair.candidateId]) {
      /* Keep the best near-miss for each candidate, for the waitlist view. */
      const existing = consideredButBlocked[pair.candidateId]
      if (!existing || pair.utility > existing.utility) {
        consideredButBlocked[pair.candidateId] = {
          ...pair,
          opportunity,
          blocked: blockedReason(pair, opportunity),
        }
      }
    }
  })

  allocations.sort((a, b) => b.matchScore - a.matchScore)

  /* ---- Candidates without a seat: pending (near miss) vs unmatched ---- */
  const pending = []
  const unmatched = []

  candidates.forEach((candidate) => {
    if (assignedCandidate[candidate.id]) return

    const nearMiss = consideredButBlocked[candidate.id]
    if (nearMiss) {
      pending.push({
        candidateId: candidate.id,
        candidateName: candidate.name,
        category: candidate.category,
        education: candidate.education,
        skills: candidate.skills,
        opportunityId: nearMiss.opportunity.id,
        company: nearMiss.opportunity.company,
        role: nearMiss.opportunity.role,
        location: nearMiss.opportunity.location,
        sector: nearMiss.opportunity.sector,
        matchScore: nearMiss.matchScore,
        acceptProbability: nearMiss.acceptProbability,
        utility: nearMiss.utility,
        components: nearMiss.components,
        overlapSkills: nearMiss.overlapSkills,
        reason: nearMiss.blocked.text,
        blockedCode: nearMiss.blocked.code,
        status: 'Pending',
      })
    } else {
      /*
       * No eligible pair at all. Report the single rule that actually blocks
       * this candidate everywhere, rather than the union of every rule that
       * failed against some opportunity (which would read as if all three
       * rules failed).
       */
      let reason
      if (candidate.qualificationScore < ELIGIBILITY_RULES.minQualificationScore) {
        reason = `Qualification score ${candidate.qualificationScore} is below the minimum of ${ELIGIBILITY_RULES.minQualificationScore}`
      } else {
        const prefs = locationPreferences(candidate)
        const inPreferredCities = opportunities.filter((opp) => prefs.includes(opp.location))
        if (inPreferredCities.length === 0) {
          reason = `No opportunity posted in preferred locations (${prefs.join(', ')})`
        } else {
          reason = `No required-skill overlap with the ${inPreferredCities.length} opportunities in ${prefs.join(' / ')}`
        }
      }

      unmatched.push({
        candidateId: candidate.id,
        candidateName: candidate.name,
        category: candidate.category,
        education: candidate.education,
        skills: candidate.skills,
        opportunityId: null,
        company: '—',
        role: '—',
        location: candidate.locationPref,
        sector: '—',
        matchScore: 0,
        acceptProbability: 0,
        utility: 0,
        reason,
        blockedCode: 'INELIGIBLE',
        status: 'Unmatched',
      })
    }
  })

  pending.sort((a, b) => b.matchScore - a.matchScore)
  unmatched.sort((a, b) => a.candidateId.localeCompare(b.candidateId))

  return {
    allocations,
    pending,
    unmatched,
    seatsLeft,
    eligiblePairCount: eligiblePairs.length,
    totalCombinations,
    stats: buildStats(allocations, pending, unmatched, candidates, opportunities, seatsLeft),
  }
}

/* -------------------------------------------------------------------------- */
/* STATS                                                                      */
/* -------------------------------------------------------------------------- */

function buildStats(allocations, pending, unmatched, candidates, opportunities, seatsLeft) {
  const scores = allocations.map((a) => a.matchScore)
  const totalSeats = opportunities.reduce((sum, o) => sum + o.capacity, 0)
  const seatsFilled = totalSeats - Object.values(seatsLeft).reduce((sum, n) => sum + n, 0)
  const avg = scores.length ? scores.reduce((sum, n) => sum + n, 0) / scores.length : 0
  const avgAccept = allocations.length
    ? allocations.reduce((sum, a) => sum + a.acceptProbability, 0) / allocations.length
    : 0

  return {
    totalCandidates: candidates.length,
    totalOpportunities: opportunities.length,
    totalSeats,
    seatsFilled,
    seatsVacant: totalSeats - seatsFilled,
    allocated: allocations.length,
    pending: pending.length,
    unmatched: unmatched.length,
    successRate: candidates.length
      ? Math.round((allocations.length / candidates.length) * 1000) / 10
      : 0,
    seatUtilisation: totalSeats ? Math.round((seatsFilled / totalSeats) * 1000) / 10 : 0,
    avgMatchScore: Math.round(avg * 10) / 10,
    highestMatchScore: scores.length ? Math.max(...scores) : 0,
    lowestMatchScore: scores.length ? Math.min(...scores) : 0,
    avgAcceptProbability: Math.round(avgAccept * 1000) / 1000,
  }
}

/* -------------------------------------------------------------------------- */
/* STAGE 5 — DYNAMIC REALLOCATION (mirrors src/reallocation.py)               */
/* -------------------------------------------------------------------------- */

/**
 * A candidate declines their offer. The vacated seat is offered to the best
 * eligible, currently-unallocated candidate. Unrelated allocations are never
 * disturbed; if no valid replacement exists the seat stays vacant.
 */
export function declineOffer(result, candidateId, candidates, opportunities) {
  const declined = result.allocations.find((a) => a.candidateId === candidateId)
  if (!declined) return { result, log: null }

  const opportunity = opportunities.find((o) => o.id === declined.opportunityId)
  const allocations = result.allocations.filter((a) => a.candidateId !== candidateId)
  const allocatedIds = new Set(allocations.map((a) => a.candidateId))

  /* Search unallocated candidates for the best feasible replacement. */
  let best = null
  candidates.forEach((candidate) => {
    if (allocatedIds.has(candidate.id) || candidate.id === candidateId) return
    const pair = scorePair(candidate, opportunity)
    if (!pair.eligibility.eligible || !pair.categoryAllowed || !pair.meetsThreshold) return
    if (!best || pair.utility > best.pair.utility) best = { candidate, pair }
  })

  const declinedCandidate = candidates.find((cd) => cd.id === candidateId)
  const pending = result.pending.filter((p) => p.candidateId !== best?.candidate.id)

  /* The declining candidate moves to the pending pool. */
  pending.push({
    ...declined,
    status: 'Declined',
    reason: 'Candidate declined the offer',
    blockedCode: 'DECLINED',
  })

  if (best) {
    allocations.push({
      candidateId: best.candidate.id,
      candidateName: best.candidate.name,
      category: best.candidate.category,
      education: best.candidate.education,
      college: best.candidate.college,
      skills: best.candidate.skills,
      opportunityId: opportunity.id,
      company: opportunity.company,
      role: opportunity.role,
      location: opportunity.location,
      sector: opportunity.sector,
      matchScore: best.pair.matchScore,
      acceptProbability: best.pair.acceptProbability,
      utility: best.pair.utility,
      components: best.pair.components,
      overlapSkills: best.pair.overlapSkills,
      missingSkills: best.pair.missingSkills,
      reason: `Reallocated after decline — ${explainMatch(best.pair, best.candidate, opportunity)}`,
      status: 'Reallocated',
    })
  }

  allocations.sort((a, b) => b.matchScore - a.matchScore)
  pending.sort((a, b) => b.matchScore - a.matchScore)

  const seatsLeft = { ...result.seatsLeft }
  if (!best) seatsLeft[opportunity.id] += 1

  return {
    result: {
      ...result,
      allocations,
      pending,
      seatsLeft,
      stats: buildStats(
        allocations,
        pending,
        result.unmatched,
        candidates,
        opportunities,
        seatsLeft
      ),
    },
    log: {
      declinedId: candidateId,
      declinedName: declinedCandidate?.name || candidateId,
      opportunityId: opportunity.id,
      company: opportunity.company,
      role: opportunity.role,
      replacementId: best?.candidate.id || null,
      replacementName: best?.candidate.name || null,
      replacementScore: best?.pair.matchScore || null,
      outcome: best ? 'REALLOCATED' : 'SEAT_VACANT',
    },
  }
}

/* -------------------------------------------------------------------------- */
/* SEAT-LEVEL SUMMARY (used by Opportunities + Analytics)                     */
/* -------------------------------------------------------------------------- */

export function opportunityUsage(result, opportunities) {
  return opportunities.map((opp) => {
    const filled = result.allocations.filter((a) => a.opportunityId === opp.id)
    const scores = filled.map((a) => a.matchScore)
    return {
      ...opp,
      filledSeats: filled.length,
      vacantSeats: opp.capacity - filled.length,
      fillRate: Math.round((filled.length / opp.capacity) * 1000) / 10,
      avgMatchScore: scores.length
        ? Math.round((scores.reduce((s, n) => s + n, 0) / scores.length) * 10) / 10
        : 0,
      applicants: result.allocations
        .concat(result.pending)
        .filter((a) => a.opportunityId === opp.id).length,
    }
  })
}

/* -------------------------------------------------------------------------- */
/* PIPELINE STAGES SHOWN DURING THE ANIMATED RUN                              */
/* -------------------------------------------------------------------------- */

export const PIPELINE_STAGES = [
  {
    key: 'load',
    label: 'Analyzing candidate profiles...',
    detail: 'Reading skills, qualification scores, categories and stated preferences.',
  },
  {
    key: 'skills',
    label: 'Evaluating skill compatibility...',
    detail: 'Computing skill-overlap percentage for every candidate–opportunity pair.',
  },
  {
    key: 'eligibility',
    label: 'Applying eligibility constraints...',
    detail: 'Hard rules: minimum qualification score, location preference, minimum skill overlap.',
  },
  {
    key: 'scoring',
    label: 'Scoring matches and acceptance likelihood...',
    detail: 'Weighted fit score plus predicted probability the offer is accepted.',
  },
  {
    key: 'optimise',
    label: 'Optimizing internship assignments...',
    detail: 'Maximising total match quality under capacity and reserved-category constraints.',
  },
  {
    key: 'finalise',
    label: 'Finalizing allocations...',
    detail: 'Writing the allocation register and generating per-candidate explanations.',
  },
]
