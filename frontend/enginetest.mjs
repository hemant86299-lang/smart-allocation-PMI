import { candidates, opportunities, TOTAL_SEATS } from './src/data/mockData.js'
import { runAllocation, opportunityUsage, declineOffer } from './src/utils/allocationEngine.js'

const r = runAllocation(candidates, opportunities)
console.log('STATS', JSON.stringify(r.stats, null, 1))
console.log('eligible pairs:', r.eligiblePairCount, 'of', r.totalCombinations)
console.log('\n-- TOP 8 ALLOCATIONS --')
r.allocations.slice(0, 8).forEach(a => console.log(`${a.candidateName} -> ${a.company} | ${a.role} | ${a.matchScore}% | p=${a.acceptProbability} | ${a.reason}`))
console.log('\n-- SCORE RANGE --', Math.min(...r.allocations.map(a=>a.matchScore)), '..', Math.max(...r.allocations.map(a=>a.matchScore)))
console.log('\n-- PENDING (' + r.pending.length + ') --')
r.pending.forEach(p => console.log(`${p.candidateName} [${p.category}] ${p.blockedCode} -> ${p.company} ${p.matchScore}% :: ${p.reason}`))
console.log('\n-- UNMATCHED (' + r.unmatched.length + ') --')
r.unmatched.forEach(p => console.log(`${p.candidateName} :: ${p.reason}`))
console.log('\n-- SEATS (total ' + TOTAL_SEATS + ') --')
opportunityUsage(r, opportunities).forEach(o => console.log(`${o.id} ${o.company.padEnd(30)} ${o.location.padEnd(10)} ${o.filledSeats}/${o.capacity} avg=${o.avgMatchScore} res=${o.reservedCategory||'-'} thr=${o.matchThreshold}`))
const d = declineOffer(r, r.allocations[0].candidateId, candidates, opportunities)
console.log('\n-- DECLINE TEST --', JSON.stringify(d.log))
console.log('after decline allocated =', d.result.stats.allocated)

console.log('\n==== MULTI-DECLINE / REALLOCATION CHECK ====')
const byCompany = {}
r.allocations.forEach(a => { if (!byCompany[a.company]) byCompany[a.company] = a })
Object.values(byCompany).forEach(a => {
  const d = declineOffer(r, a.candidateId, candidates, opportunities)
  console.log(`decline ${a.candidateName.padEnd(24)} @ ${a.company.padEnd(28)} -> ${d.log.outcome.padEnd(13)} ${d.log.replacementName || ''} ${d.log.replacementScore || ''}`)
})
