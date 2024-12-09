function openBetModal(matchId, homeTeam, awayTeam, homeOdds, awayOdds) {
    document.getElementById('match-id').value = matchId;
    document.getElementById('home-odds-field').value = homeOdds;
    document.getElementById('away-odds-field').value = awayOdds;

    document.getElementById('home-team').value = homeTeam;
    document.getElementById('away-team').value = awayTeam;

    document.getElementById('team-select').innerHTML = `
        <option value="${homeTeam}">Home (${homeTeam})</option>
        <option value="${awayTeam}">Away (${awayTeam})</option>
    `;
    document.getElementById('home-odds').textContent = homeOdds;
    document.getElementById('away-odds').textContent = awayOdds;

    // Set the hidden id field
    document.getElementById('match-id-hidden').value = matchId;

    document.getElementById('bet-modal').style.display = 'block';
}

function closeBetModal() {
    document.getElementById('bet-modal').style.display = 'none';
    document.getElementById('bet-modal-overlay').style.display = 'none';
}